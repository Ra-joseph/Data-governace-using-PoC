"""
Policy Exception Management API.

When policy enforcement runs and a data domain fails validation, the domain
owner can raise a **policy exception request** to allow deployment despite
the failure.  An advisory board reviews the request and either approves or
rejects it.  The deployment gate checks whether every failure in a domain
either has an approved exception or has been fixed.

Endpoints:
  POST /detect-failures         – scan approved policies for enforcement failures
  GET  /failures                – list current policy failures per domain
  POST /                        – raise an exception request for a specific failure
  GET  /                        – list all exception requests
  GET  /{id}                    – get exception request detail
  POST /{id}/approve            – board approves the exception
  POST /{id}/reject             – board rejects the exception
  GET  /deployment-gate/{domain} – check if a domain may deploy
  GET  /stats                   – summary statistics
  POST /reset                   – clear stores (testing)
"""

import logging
from typing import Optional
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.policy_draft import PolicyDraft
from app.models.policy_artifact import PolicyArtifact
from app.models.contract import Contract

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy-exceptions", tags=["policy-exceptions"])


# ── Pydantic Schemas ────────────────────────────────────────────────────

class ExceptionRequest(BaseModel):
    failure_id: str
    domain: str
    policy_id: int
    policy_title: str
    justification: str
    business_impact: str
    requested_by: str = "domain-owner"
    requested_duration_days: int = 90


class BoardDecision(BaseModel):
    decided_by: str
    comments: str


# ── In-Memory Stores ────────────────────────────────────────────────────
# In production these would be DB tables.

_failure_store: dict = {}     # failure_id -> failure record
_exception_store: dict = {}   # exception_id -> exception request record
_next_exception_id = 1


def _reset_stores():
    global _next_exception_id
    _failure_store.clear()
    _exception_store.clear()
    _next_exception_id = 1


# ── Failure Detection ───────────────────────────────────────────────────

def _build_failure_id(policy_id: int, domain: str) -> str:
    return f"FAIL-{policy_id}-{domain}"


def _detect_domain_failures(policies, db: Session) -> list:
    """
    For every approved policy, run it against contracts that belong to
    the policy's affected domains.  Record each (policy, domain) pair
    where at least one contract fails.
    """
    from app.services.authored_policy_loader import (
        validate_contract_with_authored_policies,
    )
    import yaml as _yaml
    import json

    failures = []

    for policy in policies:
        artifact = (
            db.query(PolicyArtifact)
            .filter(PolicyArtifact.policy_id == policy.id)
            .order_by(PolicyArtifact.version.desc())
            .first()
        )
        if not artifact:
            continue

        try:
            parsed_yaml = _yaml.safe_load(artifact.yaml_content)
        except Exception:
            continue

        authored_list = [{
            "draft_id": policy.id,
            "policy_uid": policy.policy_uid,
            "title": policy.title,
            "category": policy.policy_category,
            "severity": policy.severity,
            "scanner_type": artifact.scanner_type,
            "version": policy.version,
            "parsed_yaml": parsed_yaml,
            "artifact_id": artifact.id,
        }]

        domains = policy.affected_domains or ["ALL"]

        contracts = db.query(Contract).all()

        for domain in domains:
            failing_contracts = []
            for contract in contracts:
                contract_data = _extract_contract_data(contract)
                if not contract_data:
                    continue

                violations = validate_contract_with_authored_policies(
                    contract_data, authored_list,
                )
                if violations:
                    failing_contracts.append({
                        "contract_id": contract.id,
                        "dataset_id": contract.dataset_id,
                        "violation_count": len(violations),
                        "violations": [
                            {"field": v.field, "message": v.message, "severity": v.type.value}
                            for v in violations
                        ],
                    })

            if failing_contracts:
                fid = _build_failure_id(policy.id, domain)
                failures.append({
                    "failure_id": fid,
                    "policy_id": policy.id,
                    "policy_title": policy.title,
                    "policy_category": policy.policy_category,
                    "severity": policy.severity,
                    "domain": domain,
                    "failing_contracts": failing_contracts,
                    "total_failing": len(failing_contracts),
                    "detected_at": datetime.utcnow().isoformat(),
                })

    return failures


def _extract_contract_data(contract: Contract):
    import json as _json
    data = contract.machine_readable
    if not data:
        return None
    if isinstance(data, str):
        try:
            data = _json.loads(data)
        except Exception:
            return None
    return data if isinstance(data, dict) else None


# ── Endpoints ───────────────────────────────────────────────────────────

@router.post("/detect-failures")
def detect_failures(
    domain: Optional[str] = Query(None, description="Limit scan to one domain"),
    db: Session = Depends(get_db),
):
    """
    Scan all approved policies and detect enforcement failures.

    Records each (policy, domain) pair where at least one contract fails.
    """
    query = db.query(PolicyDraft).filter(PolicyDraft.status == "approved")
    policies = query.all()

    if domain:
        policies = [
            p for p in policies
            if domain in (p.affected_domains or ["ALL"])
            or "ALL" in (p.affected_domains or [])
        ]

    failures = _detect_domain_failures(policies, db)

    for f in failures:
        _failure_store[f["failure_id"]] = f

    return {
        "policies_scanned": len(policies),
        "total_failures": len(failures),
        "failures": failures,
    }


@router.get("/failures")
def list_failures(
    domain: Optional[str] = Query(None),
):
    """List current policy enforcement failures, optionally filtered by domain."""
    failures = list(_failure_store.values())
    if domain:
        failures = [f for f in failures if f["domain"] == domain]

    # Annotate each failure with its exception status
    annotated = []
    for f in failures:
        exception = _find_exception_for_failure(f["failure_id"])
        annotated.append({
            **f,
            "exception_status": exception["status"] if exception else None,
            "exception_id": exception["id"] if exception else None,
        })

    return {
        "total": len(annotated),
        "failures": annotated,
    }


@router.post("/")
def create_exception_request(req: ExceptionRequest):
    """
    Raise an exception request so the domain can deploy despite a policy failure.
    The advisory board must approve before the deployment gate opens.
    """
    global _next_exception_id

    # Verify the failure exists
    if req.failure_id not in _failure_store:
        raise HTTPException(status_code=404, detail="Failure not found – run detect-failures first")

    # Check for existing open/approved exception
    existing = _find_exception_for_failure(req.failure_id)
    if existing and existing["status"] in ("pending_review", "approved"):
        raise HTTPException(
            status_code=409,
            detail=f"An exception request already exists (id={existing['id']}, status={existing['status']})",
        )

    eid = _next_exception_id
    _next_exception_id += 1

    record = {
        "id": eid,
        "failure_id": req.failure_id,
        "domain": req.domain,
        "policy_id": req.policy_id,
        "policy_title": req.policy_title,
        "justification": req.justification,
        "business_impact": req.business_impact,
        "requested_by": req.requested_by,
        "requested_duration_days": req.requested_duration_days,
        "status": "pending_review",
        "created_at": datetime.utcnow().isoformat(),
        "decision": None,
    }
    _exception_store[eid] = record

    return record


@router.get("/requests")
def list_exception_requests(
    status: Optional[str] = Query(None, description="pending_review | approved | rejected"),
    domain: Optional[str] = Query(None),
):
    """List all exception requests with optional filters."""
    records = list(_exception_store.values())
    if status:
        records = [r for r in records if r["status"] == status]
    if domain:
        records = [r for r in records if r["domain"] == domain]

    records.sort(key=lambda r: r["created_at"], reverse=True)

    return {
        "total": len(records),
        "pending": sum(1 for r in records if r["status"] == "pending_review"),
        "approved": sum(1 for r in records if r["status"] == "approved"),
        "rejected": sum(1 for r in records if r["status"] == "rejected"),
        "requests": records,
    }


@router.get("/requests/{exception_id}")
def get_exception_request(exception_id: int):
    """Get details of a specific exception request."""
    record = _exception_store.get(exception_id)
    if not record:
        raise HTTPException(status_code=404, detail="Exception request not found")
    return record


@router.post("/requests/{exception_id}/approve")
def approve_exception(exception_id: int, decision: BoardDecision):
    """
    Advisory board approves the exception request.
    The domain may now deploy despite the policy failure.
    """
    record = _exception_store.get(exception_id)
    if not record:
        raise HTTPException(status_code=404, detail="Exception request not found")
    if record["status"] != "pending_review":
        raise HTTPException(status_code=409, detail=f"Cannot approve – current status is '{record['status']}'")

    record["status"] = "approved"
    record["decision"] = {
        "action": "approved",
        "decided_by": decision.decided_by,
        "comments": decision.comments,
        "decided_at": datetime.utcnow().isoformat(),
    }

    return record


@router.post("/requests/{exception_id}/reject")
def reject_exception(exception_id: int, decision: BoardDecision):
    """
    Advisory board rejects the exception request.
    The domain must fix the policy failure before deploying.
    """
    record = _exception_store.get(exception_id)
    if not record:
        raise HTTPException(status_code=404, detail="Exception request not found")
    if record["status"] != "pending_review":
        raise HTTPException(status_code=409, detail=f"Cannot reject – current status is '{record['status']}'")

    record["status"] = "rejected"
    record["decision"] = {
        "action": "rejected",
        "decided_by": decision.decided_by,
        "comments": decision.comments,
        "decided_at": datetime.utcnow().isoformat(),
    }

    return record


@router.get("/deployment-gate/{domain}")
def check_deployment_gate(domain: str):
    """
    Deployment gate for a domain.

    Returns **allowed=True** only when every policy failure in the domain
    either:
      - has an **approved** exception, or
      - has been resolved (no longer in the failure store).

    This is the check a CI/CD pipeline or merge-request hook would call.
    """
    domain_failures = [f for f in _failure_store.values() if f["domain"] == domain]

    if not domain_failures:
        return {
            "domain": domain,
            "allowed": True,
            "reason": "No policy failures detected for this domain",
            "total_failures": 0,
            "unresolved": 0,
            "approved_exceptions": 0,
            "pending_exceptions": 0,
            "rejected_exceptions": 0,
            "blockers": [],
        }

    unresolved = []
    approved = 0
    pending = 0
    rejected = 0
    blockers = []

    for f in domain_failures:
        exc = _find_exception_for_failure(f["failure_id"])
        if exc and exc["status"] == "approved":
            approved += 1
        elif exc and exc["status"] == "pending_review":
            pending += 1
            blockers.append({
                "failure_id": f["failure_id"],
                "policy_title": f["policy_title"],
                "severity": f["severity"],
                "reason": "Exception pending board review",
                "exception_id": exc["id"],
            })
        elif exc and exc["status"] == "rejected":
            rejected += 1
            blockers.append({
                "failure_id": f["failure_id"],
                "policy_title": f["policy_title"],
                "severity": f["severity"],
                "reason": "Exception rejected – must fix the violation",
                "exception_id": exc["id"],
            })
        else:
            unresolved.append(f["failure_id"])
            blockers.append({
                "failure_id": f["failure_id"],
                "policy_title": f["policy_title"],
                "severity": f["severity"],
                "reason": "No exception raised – raise one or fix the violation",
            })

    allowed = len(blockers) == 0

    return {
        "domain": domain,
        "allowed": allowed,
        "reason": "All failures have approved exceptions" if allowed else "Unresolved policy failures block deployment",
        "total_failures": len(domain_failures),
        "unresolved": len(unresolved),
        "approved_exceptions": approved,
        "pending_exceptions": pending,
        "rejected_exceptions": rejected,
        "blockers": blockers,
    }


@router.get("/stats")
def exception_stats():
    """Summary statistics for policy exceptions."""
    failures = list(_failure_store.values())
    exceptions = list(_exception_store.values())

    domain_failures = defaultdict(int)
    category_failures = defaultdict(int)
    for f in failures:
        domain_failures[f["domain"]] += 1
        category_failures[f["policy_category"]] += 1

    pending = [e for e in exceptions if e["status"] == "pending_review"]
    approved = [e for e in exceptions if e["status"] == "approved"]
    rejected = [e for e in exceptions if e["status"] == "rejected"]

    # Domains that can deploy vs. blocked
    all_domains = list(set(f["domain"] for f in failures))
    deployable = []
    blocked = []
    for d in all_domains:
        df = [f for f in failures if f["domain"] == d]
        all_covered = all(
            (_find_exception_for_failure(f["failure_id"]) or {}).get("status") == "approved"
            for f in df
        )
        if all_covered:
            deployable.append(d)
        else:
            blocked.append(d)

    return {
        "total_failures": len(failures),
        "total_exceptions": len(exceptions),
        "pending_review": len(pending),
        "approved": len(approved),
        "rejected": len(rejected),
        "approval_rate_pct": round(len(approved) / len(exceptions) * 100, 1) if exceptions else 0,
        "failures_by_domain": dict(domain_failures),
        "failures_by_category": dict(category_failures),
        "domains_deployable": deployable,
        "domains_blocked": blocked,
    }


@router.post("/reset")
def reset_stores():
    """Reset all failure and exception data (testing/admin)."""
    _reset_stores()
    return {"message": "Stores reset", "failures": 0, "exceptions": 0}


# ── Helpers ──────────────────────────────────────────────────────────────

def _find_exception_for_failure(failure_id: str):
    """Find the most recent exception request for a given failure."""
    matches = [e for e in _exception_store.values() if e["failure_id"] == failure_id]
    if not matches:
        return None
    matches.sort(key=lambda e: e["created_at"], reverse=True)
    return matches[0]

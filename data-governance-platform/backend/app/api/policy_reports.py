"""
Policy Impact Analysis & Compliance Reporting API.

Provides endpoints for:
  - Impact analysis: which contracts/datasets would be affected by a policy
  - Compliance reports: coverage matrix, pass/fail rates per policy
  - Bulk validation: re-validate all contracts against current policy set
"""

import json
import logging
from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.contract import Contract
from app.models.dataset import Dataset
from app.models.policy_draft import PolicyDraft
from app.models.policy_artifact import PolicyArtifact
from app.services.policy_engine import PolicyEngine
from app.services.authored_policy_loader import (
    load_authored_policies,
    validate_contract_with_authored_policies,
    get_combined_validation,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy-reports", tags=["policy-reports"])


# ── Response Models ──────────────────────────────────────────────────────

class ImpactSummary(BaseModel):
    policy_id: int
    policy_title: str
    total_contracts: int
    affected_contracts: int
    new_violations: int
    affected_datasets: list


class ComplianceOverview(BaseModel):
    total_contracts: int
    total_datasets: int
    total_policies_active: int
    total_policies_authored: int
    contracts_passing: int
    contracts_warning: int
    contracts_failing: int
    contracts_unvalidated: int
    pass_rate_pct: float
    policy_coverage: list
    severity_summary: dict
    classification_breakdown: dict


class BulkValidationResult(BaseModel):
    total_contracts: int
    validated: int
    passed: int
    warnings: int
    failed: int
    errors: int
    results: list


# ── Impact Analysis ──────────────────────────────────────────────────────

@router.get("/impact/{policy_id}", response_model=ImpactSummary)
def analyze_policy_impact(
    policy_id: int,
    db: Session = Depends(get_db),
):
    """
    Analyze the impact of an authored policy on existing contracts.

    Runs the policy against all contracts with stored machine_readable data
    and reports which would gain new violations.
    """
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    # Load just this one policy's artifact
    artifact = (
        db.query(PolicyArtifact)
        .filter(PolicyArtifact.policy_id == policy_id)
        .order_by(PolicyArtifact.version.desc())
        .first()
    )

    contracts = db.query(Contract).all()
    total_contracts = len(contracts)
    affected = []
    total_new_violations = 0
    affected_dataset_ids = set()

    for contract in contracts:
        contract_data = _extract_contract_data(contract)
        if not contract_data:
            continue

        if artifact:
            import yaml
            try:
                parsed_yaml = yaml.safe_load(artifact.yaml_content)
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

            violations = validate_contract_with_authored_policies(contract_data, authored_list)
            if violations:
                affected.append({
                    "contract_id": contract.id,
                    "dataset_id": contract.dataset_id,
                    "version": contract.version,
                    "new_violations": len(violations),
                    "violation_types": [v.type.value for v in violations],
                })
                total_new_violations += len(violations)
                if contract.dataset_id:
                    affected_dataset_ids.add(contract.dataset_id)

    # Get dataset names
    affected_datasets = []
    if affected_dataset_ids:
        datasets = db.query(Dataset).filter(Dataset.id.in_(affected_dataset_ids)).all()
        affected_datasets = [{"id": d.id, "name": d.name} for d in datasets]

    return ImpactSummary(
        policy_id=policy.id,
        policy_title=policy.title,
        total_contracts=total_contracts,
        affected_contracts=len(affected),
        new_violations=total_new_violations,
        affected_datasets=affected_datasets,
    )


# ── Compliance Overview ──────────────────────────────────────────────────

@router.get("/compliance", response_model=ComplianceOverview)
def get_compliance_overview(db: Session = Depends(get_db)):
    """
    Generate a comprehensive compliance overview report.

    Returns pass/fail rates, policy coverage matrix, severity distribution,
    and classification-level breakdown.
    """
    contracts = db.query(Contract).all()
    datasets = db.query(Dataset).all()

    total_contracts = len(contracts)
    total_datasets = len(datasets)

    # Active authored policies
    total_authored = db.query(PolicyDraft).count()
    total_active = db.query(PolicyDraft).filter(PolicyDraft.status == "approved").count()

    # Contract status counts
    passing = 0
    warning = 0
    failing = 0
    unvalidated = 0

    severity_counts = {"critical": 0, "warning": 0}
    classification_counts = {}

    for contract in contracts:
        status = (contract.validation_status or "").lower()
        if status == "passed":
            passing += 1
        elif status == "warning":
            warning += 1
        elif status == "failed":
            failing += 1
        else:
            unvalidated += 1

        # Count violations by severity
        results = contract.validation_results or {}
        if isinstance(results, str):
            try:
                results = json.loads(results)
            except Exception:
                results = {}

        for v in results.get("violations", []):
            vtype = (v.get("type") or "warning").lower()
            if vtype in severity_counts:
                severity_counts[vtype] += 1

        # Classification from governance_rules
        rules = contract.governance_rules or {}
        if isinstance(rules, str):
            try:
                rules = json.loads(rules)
            except Exception:
                rules = {}
        cls = rules.get("classification", "unknown")
        classification_counts[cls] = classification_counts.get(cls, 0) + 1

    # Policy coverage: for each static policy category, how many contracts checked
    engine = PolicyEngine()
    policy_categories = list(engine.policies.keys())
    coverage = []
    for cat in policy_categories:
        policies_in_cat = engine.policies[cat].get("policies", [])
        coverage.append({
            "category": cat,
            "policy_count": len(policies_in_cat),
            "policies": [{"id": p["id"], "name": p["name"]} for p in policies_in_cat],
        })

    # Authored policy coverage
    authored_cats = (
        db.query(PolicyDraft.policy_category, func.count(PolicyDraft.id))
        .filter(PolicyDraft.status == "approved")
        .group_by(PolicyDraft.policy_category)
        .all()
    )
    for cat, count in authored_cats:
        coverage.append({
            "category": f"authored:{cat}",
            "policy_count": count,
            "policies": [],
        })

    validated = total_contracts - unvalidated
    pass_rate = (passing / validated * 100) if validated > 0 else 0.0

    return ComplianceOverview(
        total_contracts=total_contracts,
        total_datasets=total_datasets,
        total_policies_active=total_active,
        total_policies_authored=total_authored,
        contracts_passing=passing,
        contracts_warning=warning,
        contracts_failing=failing,
        contracts_unvalidated=unvalidated,
        pass_rate_pct=round(pass_rate, 1),
        policy_coverage=coverage,
        severity_summary=severity_counts,
        classification_breakdown=classification_counts,
    )


# ── Bulk Validation ──────────────────────────────────────────────────────

@router.post("/bulk-validate", response_model=BulkValidationResult)
def bulk_validate(
    include_authored: bool = Query(True),
    db: Session = Depends(get_db),
):
    """
    Re-validate all contracts against the full policy set.

    Runs both static YAML policies and (optionally) authored policies
    against every contract. Updates validation_status and validation_results.
    """
    contracts = db.query(Contract).all()
    total = len(contracts)
    passed = 0
    warnings = 0
    failed = 0
    errors = 0
    results_list = []

    for contract in contracts:
        contract_data = _extract_contract_data(contract)
        if not contract_data:
            errors += 1
            results_list.append({
                "contract_id": contract.id,
                "status": "error",
                "message": "No parseable contract data",
            })
            continue

        try:
            if include_authored:
                result = get_combined_validation(contract_data, db)
            else:
                engine = PolicyEngine()
                result = engine.validate_contract(contract_data)

            # Update contract in DB
            contract.validation_status = result.status.value
            contract.validation_results = {
                "status": result.status.value,
                "passed": result.passed,
                "warnings": result.warnings,
                "failures": result.failures,
                "violations": [
                    {
                        "type": v.type.value,
                        "policy": v.policy,
                        "field": v.field,
                        "message": v.message,
                        "remediation": v.remediation,
                    }
                    for v in result.violations
                ],
            }
            contract.last_validated_at = datetime.utcnow()

            status_val = result.status.value
            if status_val == "passed":
                passed += 1
            elif status_val == "warning":
                warnings += 1
            else:
                failed += 1

            results_list.append({
                "contract_id": contract.id,
                "status": status_val,
                "violations": len(result.violations),
                "failures": result.failures,
            })

        except Exception as e:
            errors += 1
            logger.warning(f"Bulk validation error for contract {contract.id}: {e}")
            results_list.append({
                "contract_id": contract.id,
                "status": "error",
                "message": str(e),
            })

    db.commit()

    return BulkValidationResult(
        total_contracts=total,
        validated=total - errors,
        passed=passed,
        warnings=warnings,
        failed=failed,
        errors=errors,
        results=results_list,
    )


# ── Per-Policy Compliance Detail ─────────────────────────────────────────

@router.get("/policy-compliance/{policy_id}")
def get_policy_compliance_detail(
    policy_id: int,
    db: Session = Depends(get_db),
):
    """
    Get compliance details for a specific authored policy.

    Returns how many contracts pass/fail this specific policy,
    with a breakdown of which contracts have violations.
    """
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    artifact = (
        db.query(PolicyArtifact)
        .filter(PolicyArtifact.policy_id == policy_id)
        .order_by(PolicyArtifact.version.desc())
        .first()
    )

    contracts = db.query(Contract).all()
    compliant = []
    non_compliant = []

    for contract in contracts:
        contract_data = _extract_contract_data(contract)
        if not contract_data:
            continue

        if artifact:
            import yaml
            try:
                parsed_yaml = yaml.safe_load(artifact.yaml_content)
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

            violations = validate_contract_with_authored_policies(contract_data, authored_list)
            if violations:
                non_compliant.append({
                    "contract_id": contract.id,
                    "dataset_id": contract.dataset_id,
                    "violations": [
                        {"field": v.field, "message": v.message}
                        for v in violations
                    ],
                })
            else:
                compliant.append({"contract_id": contract.id, "dataset_id": contract.dataset_id})
        else:
            # No artifact → cannot enforce → treat as compliant
            compliant.append({"contract_id": contract.id, "dataset_id": contract.dataset_id})

    total = len(compliant) + len(non_compliant)
    return {
        "policy_id": policy.id,
        "policy_title": policy.title,
        "policy_status": policy.status,
        "total_contracts": total,
        "compliant_count": len(compliant),
        "non_compliant_count": len(non_compliant),
        "compliance_rate_pct": round(len(compliant) / total * 100, 1) if total > 0 else 100.0,
        "compliant": compliant,
        "non_compliant": non_compliant,
    }


# ── Helpers ──────────────────────────────────────────────────────────────

def _extract_contract_data(contract: Contract) -> Optional[dict]:
    """Extract parseable contract data from a Contract model."""
    data = contract.machine_readable
    if not data:
        return None
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            return None
    if isinstance(data, dict):
        return data
    return None

"""
Policy governance dashboard API.

Provides endpoints for compliance statistics, authored policy metrics,
and combined validation that includes authored policies.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.policy_draft import PolicyDraft
from app.models.policy_artifact import PolicyArtifact
from app.models.policy_approval_log import PolicyApprovalLog
from app.schemas.contract import ValidationResult
from app.services.authored_policy_loader import (
    load_authored_policies,
    get_combined_validation,
)

router = APIRouter(prefix="/policy-dashboard", tags=["policy-dashboard"])


class DashboardStatsResponse(BaseModel):
    total_policies: int
    by_status: dict
    by_category: dict
    by_severity: dict
    total_artifacts: int
    total_approval_actions: int
    scanner_breakdown: dict
    recent_approvals: list


class CombinedValidationRequest(BaseModel):
    contract_data: dict
    domain: Optional[str] = None


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get comprehensive policy governance statistics."""
    total = db.query(PolicyDraft).count()

    # Status breakdown
    status_rows = (
        db.query(PolicyDraft.status, func.count(PolicyDraft.id))
        .group_by(PolicyDraft.status)
        .all()
    )
    by_status = {row[0]: row[1] for row in status_rows}

    # Category breakdown
    cat_rows = (
        db.query(PolicyDraft.policy_category, func.count(PolicyDraft.id))
        .group_by(PolicyDraft.policy_category)
        .all()
    )
    by_category = {row[0]: row[1] for row in cat_rows}

    # Severity breakdown
    sev_rows = (
        db.query(PolicyDraft.severity, func.count(PolicyDraft.id))
        .group_by(PolicyDraft.severity)
        .all()
    )
    by_severity = {row[0]: row[1] for row in sev_rows}

    # Artifact count
    total_artifacts = db.query(PolicyArtifact).count()

    # Approval actions
    total_actions = db.query(PolicyApprovalLog).count()

    # Scanner breakdown from artifacts
    scanner_rows = (
        db.query(PolicyArtifact.scanner_type, func.count(PolicyArtifact.id))
        .group_by(PolicyArtifact.scanner_type)
        .all()
    )
    scanner_breakdown = {row[0]: row[1] for row in scanner_rows}

    # Recent approvals (last 10)
    recent_logs = (
        db.query(PolicyApprovalLog)
        .order_by(PolicyApprovalLog.timestamp.desc())
        .limit(10)
        .all()
    )
    recent_approvals = [
        {
            "id": log.id,
            "policy_id": log.policy_id,
            "action": log.action,
            "actor_name": log.actor_name,
            "comment": log.comment,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None,
        }
        for log in recent_logs
    ]

    return DashboardStatsResponse(
        total_policies=total,
        by_status=by_status,
        by_category=by_category,
        by_severity=by_severity,
        total_artifacts=total_artifacts,
        total_approval_actions=total_actions,
        scanner_breakdown=scanner_breakdown,
        recent_approvals=recent_approvals,
    )


@router.get("/active-policies")
def get_active_policies(
    domain: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Get all active (approved) authored policies with their artifacts."""
    policies = load_authored_policies(db, domain=domain)
    return {
        "total": len(policies),
        "domain_filter": domain,
        "policies": [
            {
                "draft_id": p["draft_id"],
                "policy_uid": p["policy_uid"],
                "title": p["title"],
                "category": p["category"],
                "severity": p["severity"],
                "scanner_type": p["scanner_type"],
                "version": p["version"],
            }
            for p in policies
        ],
    }


@router.post("/validate-combined")
def validate_combined(
    request: CombinedValidationRequest,
    db: Session = Depends(get_db),
):
    """
    Validate a contract against BOTH static YAML policies AND authored policies.

    This is the "full enforcement" endpoint that closes the loop between
    policy authoring and contract validation.
    """
    result = get_combined_validation(
        contract_data=request.contract_data,
        db=db,
        domain=request.domain,
    )
    return {
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
        "total_violations": len(result.violations),
    }

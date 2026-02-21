"""
Policy authoring API router.

Provides endpoints for creating, managing, and approving governance policies
authored in plain English. Policies follow a draft -> submit -> approve/reject
workflow before YAML/JSON artifacts are generated.
"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.policy_draft import PolicyDraft
from app.models.policy_version import PolicyVersion
from app.models.policy_artifact import PolicyArtifact
from app.models.policy_approval_log import PolicyApprovalLog
from app.schemas.policy import (
    PolicyCreate, PolicyUpdate, PolicySubmit, PolicyApprove, PolicyReject,
    PolicyResponse, PolicyDetailResponse, PolicyListResponse,
    PolicyArtifactResponse,
)

router = APIRouter(prefix="/policies/authored", tags=["policy-authoring"])


@router.post("/", response_model=PolicyResponse, status_code=201)
def create_policy(policy: PolicyCreate, db: Session = Depends(get_db)):
    """Create a new policy draft."""
    db_policy = PolicyDraft(
        policy_uid=str(uuid.uuid4()),
        title=policy.title,
        description=policy.description,
        policy_category=policy.policy_category.value,
        affected_domains=policy.affected_domains,
        severity=policy.severity.value,
        scanner_hint=policy.scanner_hint.value,
        remediation_guide=policy.remediation_guide,
        effective_date=policy.effective_date,
        authored_by=policy.authored_by,
        status="draft",
        version=1,
    )
    db.add(db_policy)
    db.commit()
    db.refresh(db_policy)
    return db_policy


@router.get("/", response_model=PolicyListResponse)
def list_policies(
    domain: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """List policies with optional filters."""
    query = db.query(PolicyDraft)

    if status:
        query = query.filter(PolicyDraft.status == status)
    if category:
        query = query.filter(PolicyDraft.policy_category == category)
    if severity:
        query = query.filter(PolicyDraft.severity == severity)
    if domain:
        # Filter where affected_domains contains the domain or "ALL"
        # For SQLite JSON, use string matching
        query = query.filter(
            (PolicyDraft.affected_domains.contains(domain)) |
            (PolicyDraft.affected_domains.contains("ALL"))
        )

    total = query.count()
    policies = query.order_by(PolicyDraft.created_at.desc()).offset(skip).limit(limit).all()
    return PolicyListResponse(policies=policies, total=total)


@router.get("/{policy_id}", response_model=PolicyDetailResponse)
def get_policy(policy_id: int, db: Session = Depends(get_db)):
    """Get a policy with its version history, artifacts, and approval logs."""
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    return policy


@router.patch("/{policy_id}", response_model=PolicyResponse)
def update_policy(policy_id: int, update: PolicyUpdate, db: Session = Depends(get_db)):
    """Update a draft policy. Only allowed when status is 'draft'."""
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    if policy.status != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot update policy in '{policy.status}' status. Only 'draft' policies can be edited."
        )

    update_data = update.model_dump(exclude_unset=True)
    # Convert enum values to strings
    for key, value in update_data.items():
        if hasattr(value, 'value'):
            update_data[key] = value.value

    for key, value in update_data.items():
        setattr(policy, key, value)

    db.commit()
    db.refresh(policy)
    return policy


@router.post("/{policy_id}/submit", response_model=PolicyResponse)
def submit_policy(policy_id: int, db: Session = Depends(get_db)):
    """Submit a draft policy for approval. Remediation guide must be set."""
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    if policy.status != "draft":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit policy in '{policy.status}' status. Only 'draft' policies can be submitted."
        )
    if not policy.remediation_guide or not policy.remediation_guide.strip():
        raise HTTPException(
            status_code=422,
            detail="Remediation guide is mandatory before submitting a policy for approval."
        )

    policy.status = "pending_approval"

    # Create audit log
    log = PolicyApprovalLog(
        policy_id=policy.id,
        action="submitted",
        actor_name=policy.authored_by,
        comment=None,
    )
    db.add(log)
    db.commit()
    db.refresh(policy)
    return policy


@router.post("/{policy_id}/approve", response_model=PolicyResponse)
def approve_policy(policy_id: int, body: PolicyApprove, db: Session = Depends(get_db)):
    """Approve a pending policy. Creates a version snapshot and generates artifacts."""
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    if policy.status != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot approve policy in '{policy.status}' status. Only 'pending_approval' policies can be approved."
        )

    policy.status = "approved"

    # Create immutable version snapshot
    version_snapshot = PolicyVersion(
        policy_id=policy.id,
        version=policy.version,
        title=policy.title,
        description=policy.description,
        policy_category=policy.policy_category,
        affected_domains=policy.affected_domains,
        severity=policy.severity,
        scanner_hint=policy.scanner_hint,
        remediation_guide=policy.remediation_guide,
        effective_date=policy.effective_date,
        authored_by=policy.authored_by,
        approved_by=body.approver_name,
        status="approved",
    )
    db.add(version_snapshot)

    # Create audit log
    log = PolicyApprovalLog(
        policy_id=policy.id,
        action="approved",
        actor_name=body.approver_name,
        comment=None,
    )
    db.add(log)

    db.commit()
    db.refresh(policy)
    return policy


@router.post("/{policy_id}/reject", response_model=PolicyResponse)
def reject_policy(policy_id: int, body: PolicyReject, db: Session = Depends(get_db)):
    """Reject a pending policy. Requires a comment (min 10 chars) and approver name."""
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    if policy.status != "pending_approval":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot reject policy in '{policy.status}' status. Only 'pending_approval' policies can be rejected."
        )

    policy.status = "rejected"

    # Create version snapshot
    version_snapshot = PolicyVersion(
        policy_id=policy.id,
        version=policy.version,
        title=policy.title,
        description=policy.description,
        policy_category=policy.policy_category,
        affected_domains=policy.affected_domains,
        severity=policy.severity,
        scanner_hint=policy.scanner_hint,
        remediation_guide=policy.remediation_guide,
        effective_date=policy.effective_date,
        authored_by=policy.authored_by,
        approved_by=body.approver_name,
        status="rejected",
    )
    db.add(version_snapshot)

    # Create audit log
    log = PolicyApprovalLog(
        policy_id=policy.id,
        action="rejected",
        actor_name=body.approver_name,
        comment=body.comment,
    )
    db.add(log)

    db.commit()
    db.refresh(policy)
    return policy


@router.get("/{policy_id}/yaml", response_model=PolicyArtifactResponse)
def get_policy_yaml(policy_id: int, db: Session = Depends(get_db)):
    """Download the latest YAML artifact for an approved policy."""
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    artifact = (
        db.query(PolicyArtifact)
        .filter(PolicyArtifact.policy_id == policy_id)
        .order_by(PolicyArtifact.version.desc())
        .first()
    )
    if not artifact:
        raise HTTPException(
            status_code=404,
            detail="No YAML artifact found for this policy. The policy must be approved first."
        )
    return artifact


@router.get("/domains/{domain}/policies", response_model=PolicyListResponse)
def get_domain_policies(domain: str, db: Session = Depends(get_db)):
    """Get all active (approved) policies for a specific domain."""
    query = db.query(PolicyDraft).filter(PolicyDraft.status == "approved")
    # Filter by domain or ALL
    query = query.filter(
        (PolicyDraft.affected_domains.contains(domain)) |
        (PolicyDraft.affected_domains.contains("ALL"))
    )
    policies = query.order_by(PolicyDraft.created_at.desc()).all()
    return PolicyListResponse(policies=policies, total=len(policies))

"""
Policy authoring API router.

Provides endpoints for creating, managing, and approving governance policies
authored in plain English. Policies follow a draft -> submit -> approve/reject
workflow before YAML/JSON artifacts are generated.
"""

import uuid
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
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
from app.services.policy_converter import convert_policy_to_yaml

logger = logging.getLogger(__name__)

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
    """Approve a pending policy. Creates a version snapshot, generates YAML/JSON artifacts, and commits to Git."""
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

    # --- Stage 2: Generate YAML/JSON artifact ---
    conversion = convert_policy_to_yaml(
        policy_uid=policy.policy_uid,
        title=policy.title,
        description=policy.description,
        policy_category=policy.policy_category,
        affected_domains=policy.affected_domains or ["ALL"],
        severity=policy.severity,
        scanner_hint=policy.scanner_hint,
        remediation_guide=policy.remediation_guide or "",
        effective_date=policy.effective_date,
        authored_by=policy.authored_by,
        version=policy.version,
    )

    # Try to commit YAML to Git (graceful degradation if Git is unavailable)
    git_commit_hash = None
    git_file_path = None
    try:
        from app.services.git_service import GitService
        git_service = GitService()
        git_info = git_service.commit_contract(
            contract_yaml=conversion["yaml_content"],
            dataset_name=f"policy_{policy.policy_uid[:8]}",
            version=f"{policy.version}.0.0",
            commit_message=f"Add policy: {policy.title} (v{policy.version})",
        )
        git_commit_hash = git_info.get("commit_hash")
        git_file_path = git_info.get("file_path")
    except Exception as e:
        logger.warning(f"Git commit failed for policy {policy.id}: {e}")

    artifact = PolicyArtifact(
        policy_id=policy.id,
        version=policy.version,
        yaml_content=conversion["yaml_content"],
        json_content=conversion["json_content"],
        scanner_type=conversion["scanner_type"],
        git_commit_hash=git_commit_hash,
        git_file_path=git_file_path,
    )
    db.add(artifact)

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


@router.get("/{policy_id}/preview-yaml")
def preview_policy_yaml(policy_id: int, db: Session = Depends(get_db)):
    """
    Preview the YAML/JSON that would be generated for a policy, without
    committing to Git or creating an artifact record. Works on any status.
    """
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    conversion = convert_policy_to_yaml(
        policy_uid=policy.policy_uid,
        title=policy.title,
        description=policy.description,
        policy_category=policy.policy_category,
        affected_domains=policy.affected_domains or ["ALL"],
        severity=policy.severity,
        scanner_hint=policy.scanner_hint,
        remediation_guide=policy.remediation_guide or "",
        effective_date=policy.effective_date,
        authored_by=policy.authored_by,
        version=policy.version,
    )

    return {
        "yaml_content": conversion["yaml_content"],
        "json_content": conversion["json_content"],
        "scanner_type": conversion["scanner_type"],
        "policy_id_generated": conversion["policy_id"],
        "is_preview": True,
    }


@router.get("/{policy_id}/versions")
def get_version_history(policy_id: int, db: Session = Depends(get_db)):
    """
    Get the full version history for a policy, including snapshots and artifacts.

    Returns an ordered list of versions with their approval metadata,
    artifact summaries, and diff availability flags.
    """
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    versions = (
        db.query(PolicyVersion)
        .filter(PolicyVersion.policy_id == policy_id)
        .order_by(PolicyVersion.version.desc())
        .all()
    )

    artifacts_by_version = {}
    for art in db.query(PolicyArtifact).filter(PolicyArtifact.policy_id == policy_id).all():
        artifacts_by_version[art.version] = {
            "artifact_id": art.id,
            "scanner_type": art.scanner_type,
            "git_commit_hash": art.git_commit_hash,
            "generated_at": art.generated_at.isoformat() if art.generated_at else None,
        }

    result = []
    for v in versions:
        result.append({
            "version": v.version,
            "title": v.title,
            "description": v.description,
            "severity": v.severity,
            "status": v.status,
            "authored_by": v.authored_by,
            "approved_by": v.approved_by,
            "created_at": v.created_at.isoformat() if v.created_at else None,
            "has_artifact": v.version in artifacts_by_version,
            "artifact": artifacts_by_version.get(v.version),
        })

    return {
        "policy_id": policy.id,
        "policy_uid": policy.policy_uid,
        "current_version": policy.version,
        "current_status": policy.status,
        "total_versions": len(result),
        "versions": result,
    }


@router.get("/{policy_id}/versions/{version_number}/diff")
def get_version_diff(policy_id: int, version_number: int, db: Session = Depends(get_db)):
    """
    Compare two consecutive versions of a policy.

    Returns a field-by-field diff between `version_number` and the previous version.
    If version_number is 1, compares against an empty baseline.
    """
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    current = (
        db.query(PolicyVersion)
        .filter(PolicyVersion.policy_id == policy_id, PolicyVersion.version == version_number)
        .first()
    )
    if not current:
        raise HTTPException(status_code=404, detail=f"Version {version_number} not found")

    previous = None
    if version_number > 1:
        previous = (
            db.query(PolicyVersion)
            .filter(PolicyVersion.policy_id == policy_id, PolicyVersion.version == version_number - 1)
            .first()
        )

    diff_fields = _compute_version_diff(previous, current)

    # Also diff YAML artifacts if both exist
    yaml_diff = None
    curr_art = db.query(PolicyArtifact).filter(
        PolicyArtifact.policy_id == policy_id, PolicyArtifact.version == version_number
    ).first()
    prev_art = None
    if version_number > 1:
        prev_art = db.query(PolicyArtifact).filter(
            PolicyArtifact.policy_id == policy_id, PolicyArtifact.version == version_number - 1
        ).first()

    if curr_art:
        yaml_diff = {
            "current_yaml": curr_art.yaml_content,
            "previous_yaml": prev_art.yaml_content if prev_art else None,
        }

    return {
        "policy_id": policy_id,
        "version": version_number,
        "compared_to": version_number - 1 if version_number > 1 else None,
        "changes": diff_fields,
        "yaml_diff": yaml_diff,
    }


def _compute_version_diff(previous, current):
    """Compute field-level diff between two PolicyVersion snapshots."""
    fields = ["title", "description", "severity", "policy_category", "scanner_hint",
              "remediation_guide", "affected_domains", "effective_date", "authored_by"]
    changes = []
    for f in fields:
        old_val = getattr(previous, f, None) if previous else None
        new_val = getattr(current, f, None)
        # Normalize for comparison
        if isinstance(old_val, list) and isinstance(new_val, list):
            old_str, new_str = sorted(old_val), sorted(new_val)
        else:
            old_str, new_str = old_val, new_val
        if old_str != new_str:
            changes.append({
                "field": f,
                "old_value": _serialize(old_val),
                "new_value": _serialize(new_val),
            })
    # Always include status change
    old_status = previous.status if previous else None
    new_status = current.status
    if old_status != new_status:
        changes.append({"field": "status", "old_value": old_status, "new_value": new_status})
    return changes


def _serialize(val):
    """Serialize a value for JSON output."""
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()
    return val


@router.post("/{policy_id}/revise", response_model=PolicyResponse)
def revise_policy(policy_id: int, db: Session = Depends(get_db)):
    """
    Create a new draft revision of an approved or rejected policy.

    Bumps the version number and resets status to 'draft', allowing
    the author to edit and re-submit. The previous version snapshot
    is preserved in the version history.
    """
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    if policy.status not in ("approved", "rejected"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot revise policy in '{policy.status}' status. Only 'approved' or 'rejected' policies can be revised."
        )

    policy.version += 1
    policy.status = "draft"

    log = PolicyApprovalLog(
        policy_id=policy.id,
        action="revised",
        actor_name=policy.authored_by,
        comment=f"Opened revision v{policy.version}",
    )
    db.add(log)
    db.commit()
    db.refresh(policy)
    return policy


@router.post("/{policy_id}/deprecate", response_model=PolicyResponse)
def deprecate_policy(policy_id: int, body: PolicyApprove, db: Session = Depends(get_db)):
    """
    Deprecate an approved policy. Marks it as no longer enforced.

    Only approved policies can be deprecated. Creates an audit trail entry.
    """
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")
    if policy.status != "approved":
        raise HTTPException(
            status_code=400,
            detail=f"Cannot deprecate policy in '{policy.status}' status. Only 'approved' policies can be deprecated."
        )

    policy.status = "deprecated"

    log = PolicyApprovalLog(
        policy_id=policy.id,
        action="deprecated",
        actor_name=body.approver_name,
        comment="Policy deprecated",
    )
    db.add(log)
    db.commit()
    db.refresh(policy)
    return policy


@router.get("/{policy_id}/timeline")
def get_policy_timeline(policy_id: int, db: Session = Depends(get_db)):
    """
    Get a unified chronological timeline of all events for a policy.

    Merges approval logs (submitted, approved, rejected, deprecated, revised)
    with version snapshots into a single ordered timeline.
    """
    policy = db.query(PolicyDraft).filter(PolicyDraft.id == policy_id).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    logs = (
        db.query(PolicyApprovalLog)
        .filter(PolicyApprovalLog.policy_id == policy_id)
        .order_by(PolicyApprovalLog.timestamp.asc())
        .all()
    )

    events = [
        {
            "type": "created",
            "timestamp": policy.created_at.isoformat() if policy.created_at else None,
            "actor": policy.authored_by,
            "detail": f"Policy draft created: \"{policy.title}\"",
            "version": 1,
        }
    ]

    for log_entry in logs:
        events.append({
            "type": log_entry.action,
            "timestamp": log_entry.timestamp.isoformat() if log_entry.timestamp else None,
            "actor": log_entry.actor_name,
            "detail": log_entry.comment or f"Policy {log_entry.action}",
            "version": policy.version,
        })

    return {
        "policy_id": policy.id,
        "policy_uid": policy.policy_uid,
        "title": policy.title,
        "current_status": policy.status,
        "current_version": policy.version,
        "total_events": len(events),
        "events": events,
    }


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

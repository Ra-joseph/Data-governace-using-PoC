"""
Policy Export, Import & Sharing API.

Provides endpoints for:
  - Exporting individual or bulk policies as portable YAML/JSON bundles
  - Importing policy bundles to create new drafts
  - Policy template catalog for reusable governance patterns
"""

import json
import uuid
import logging
from typing import Optional, List
from datetime import datetime, date

import yaml
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.policy_draft import PolicyDraft
from app.models.policy_artifact import PolicyArtifact
from app.models.policy_version import PolicyVersion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy-exchange", tags=["policy-exchange"])

# ── Schemas ──────────────────────────────────────────────────────────────

BUNDLE_FORMAT_VERSION = "1.0"


class ImportPolicyEntry(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    policy_category: str
    affected_domains: List[str] = Field(default=["ALL"])
    severity: str = Field(default="WARNING")
    scanner_hint: str = Field(default="auto")
    remediation_guide: Optional[str] = None
    effective_date: Optional[str] = None
    authored_by: str = Field(default="Imported Policy")


class ImportBundleRequest(BaseModel):
    bundle_name: str = Field(default="Imported Bundle")
    imported_by: str = Field(default="Data Governance Admin")
    policies: List[ImportPolicyEntry]


class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    category: str
    tags: List[str] = Field(default=[])
    policy_data: ImportPolicyEntry


# ── Export ───────────────────────────────────────────────────────────────

@router.get("/export/{policy_id}")
def export_policy(
    policy_id: int,
    format: str = Query("yaml", regex="^(yaml|json)$"),
    db: Session = Depends(get_db),
):
    """
    Export a single policy as a portable YAML or JSON document.

    Includes policy metadata, the latest artifact, and version info.
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

    export_doc = _build_export_document(policy, artifact)

    if format == "yaml":
        content = yaml.dump(export_doc, default_flow_style=False, sort_keys=False)
        return Response(
            content=content,
            media_type="text/yaml",
            headers={"Content-Disposition": f'attachment; filename="policy_{policy.policy_uid[:8]}_v{policy.version}.yaml"'},
        )
    else:
        return export_doc


@router.get("/export-bundle")
def export_bundle(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    format: str = Query("yaml", regex="^(yaml|json)$"),
    db: Session = Depends(get_db),
):
    """
    Export multiple policies as a portable bundle.

    Filters by status and/or category. Returns a bundle document
    containing all matching policies with their artifacts.
    """
    query = db.query(PolicyDraft)
    if status:
        query = query.filter(PolicyDraft.status == status)
    if category:
        query = query.filter(PolicyDraft.policy_category == category)

    policies = query.order_by(PolicyDraft.created_at.desc()).all()

    bundle = {
        "bundle_format_version": BUNDLE_FORMAT_VERSION,
        "exported_at": datetime.utcnow().isoformat(),
        "total_policies": len(policies),
        "filters": {"status": status, "category": category},
        "policies": [],
    }

    for policy in policies:
        artifact = (
            db.query(PolicyArtifact)
            .filter(PolicyArtifact.policy_id == policy.id)
            .order_by(PolicyArtifact.version.desc())
            .first()
        )
        bundle["policies"].append(_build_export_document(policy, artifact))

    if format == "yaml":
        content = yaml.dump(bundle, default_flow_style=False, sort_keys=False)
        return Response(
            content=content,
            media_type="text/yaml",
            headers={"Content-Disposition": 'attachment; filename="policy_bundle.yaml"'},
        )
    else:
        return bundle


# ── Import ───────────────────────────────────────────────────────────────

VALID_CATEGORIES = {"data_quality", "security", "privacy", "compliance", "lineage", "sla"}
VALID_SEVERITIES = {"CRITICAL", "WARNING", "INFO"}
VALID_SCANNERS = {"rule_based", "ai_semantic", "auto"}


@router.post("/import")
def import_bundle(
    request: ImportBundleRequest,
    db: Session = Depends(get_db),
):
    """
    Import a bundle of policies, creating new drafts for each.

    Each imported policy gets a fresh UUID, version 1, and 'draft' status.
    Duplicate detection is based on title matching.
    """
    created = []
    skipped = []
    errors = []

    for entry in request.policies:
        # Validate category
        if entry.policy_category not in VALID_CATEGORIES:
            errors.append({"title": entry.title, "error": f"Invalid category: {entry.policy_category}"})
            continue

        # Validate severity
        severity = entry.severity.upper()
        if severity not in VALID_SEVERITIES:
            severity = "WARNING"

        # Validate scanner
        scanner = entry.scanner_hint.lower()
        if scanner not in VALID_SCANNERS:
            scanner = "auto"

        # Check for duplicate by title
        existing = db.query(PolicyDraft).filter(PolicyDraft.title == entry.title).first()
        if existing:
            skipped.append({
                "title": entry.title,
                "existing_id": existing.id,
                "reason": "Policy with same title already exists",
            })
            continue

        # Parse effective date
        eff_date = None
        if entry.effective_date:
            try:
                eff_date = date.fromisoformat(entry.effective_date)
            except ValueError:
                pass

        policy = PolicyDraft(
            policy_uid=str(uuid.uuid4()),
            title=entry.title,
            description=entry.description,
            policy_category=entry.policy_category,
            affected_domains=entry.affected_domains,
            severity=severity,
            scanner_hint=scanner,
            remediation_guide=entry.remediation_guide,
            effective_date=eff_date,
            authored_by=entry.authored_by or request.imported_by,
            status="draft",
            version=1,
        )
        db.add(policy)
        db.flush()

        created.append({
            "id": policy.id,
            "policy_uid": policy.policy_uid,
            "title": policy.title,
            "category": policy.policy_category,
            "severity": policy.severity,
        })

    db.commit()

    return {
        "bundle_name": request.bundle_name,
        "imported_by": request.imported_by,
        "total_in_bundle": len(request.policies),
        "created": len(created),
        "skipped": len(skipped),
        "errors": len(errors),
        "created_policies": created,
        "skipped_policies": skipped,
        "error_details": errors,
    }


# ── Template Catalog ─────────────────────────────────────────────────────

# In-memory template store (in production, this would be a DB table)
_BUILTIN_TEMPLATES = [
    {
        "id": "tmpl-pii-encryption",
        "name": "PII Encryption Required",
        "description": "Enforce AES-256 encryption for all PII fields at rest and TLS in transit.",
        "category": "security",
        "tags": ["pii", "encryption", "gdpr"],
        "policy_data": {
            "title": "PII fields must be encrypted",
            "description": "All fields flagged as PII must use AES-256 encryption at rest and TLS 1.2+ in transit.",
            "policy_category": "security",
            "affected_domains": ["ALL"],
            "severity": "CRITICAL",
            "scanner_hint": "rule_based",
            "remediation_guide": "1. Identify PII columns in schema\n2. Set encryption_required: true in governance\n3. Verify TLS is enabled for data transfer",
        },
    },
    {
        "id": "tmpl-data-retention",
        "name": "Data Retention Policy",
        "description": "Require retention period specification for confidential and restricted data.",
        "category": "compliance",
        "tags": ["retention", "compliance", "data-lifecycle"],
        "policy_data": {
            "title": "Data retention policy required",
            "description": "Confidential and restricted data must specify a retention period in days.",
            "policy_category": "compliance",
            "affected_domains": ["ALL"],
            "severity": "CRITICAL",
            "scanner_hint": "rule_based",
            "remediation_guide": "1. Add retention_days to governance section\n2. Set value based on data classification\n3. Confidential: minimum 2555 days (7 years)",
        },
    },
    {
        "id": "tmpl-completeness",
        "name": "Data Completeness Threshold",
        "description": "Ensure critical datasets maintain at least 95% completeness.",
        "category": "data_quality",
        "tags": ["quality", "completeness", "sla"],
        "policy_data": {
            "title": "Critical data completeness >= 95%",
            "description": "Datasets classified as confidential or restricted must maintain a completeness threshold of at least 95%.",
            "policy_category": "data_quality",
            "affected_domains": ["ALL"],
            "severity": "CRITICAL",
            "scanner_hint": "rule_based",
            "remediation_guide": "1. Set completeness_threshold to 95 or higher in quality_rules\n2. Implement data quality monitoring\n3. Set up alerts for threshold breaches",
        },
    },
    {
        "id": "tmpl-owner-required",
        "name": "Dataset Ownership Required",
        "description": "All datasets must have a designated owner with name and contact email.",
        "category": "compliance",
        "tags": ["ownership", "accountability", "governance"],
        "policy_data": {
            "title": "Dataset ownership required",
            "description": "Every dataset must have owner_name and owner_email specified for accountability.",
            "policy_category": "compliance",
            "affected_domains": ["ALL"],
            "severity": "CRITICAL",
            "scanner_hint": "rule_based",
            "remediation_guide": "1. Add owner_name and owner_email to the dataset section\n2. Owner should be a team lead or data steward",
        },
    },
    {
        "id": "tmpl-freshness-sla",
        "name": "Freshness SLA for Temporal Data",
        "description": "Datasets with temporal fields must define a freshness SLA.",
        "category": "data_quality",
        "tags": ["freshness", "sla", "temporal"],
        "policy_data": {
            "title": "Freshness SLA required for temporal data",
            "description": "Any dataset containing date, timestamp, or datetime fields must specify a freshness_sla.",
            "policy_category": "data_quality",
            "affected_domains": ["ALL"],
            "severity": "WARNING",
            "scanner_hint": "rule_based",
            "remediation_guide": "1. Add freshness_sla to quality_rules (e.g., '24h', '1h')\n2. Align with downstream consumer expectations",
        },
    },
]


@router.get("/templates")
def list_templates(
    category: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
):
    """
    List available policy templates.

    Templates are reusable governance patterns that can be instantiated
    into new policy drafts with a single click.
    """
    templates = _BUILTIN_TEMPLATES[:]

    if category:
        templates = [t for t in templates if t["category"] == category]
    if tag:
        templates = [t for t in templates if tag in t["tags"]]

    return {
        "total": len(templates),
        "templates": templates,
    }


@router.get("/templates/{template_id}")
def get_template(template_id: str):
    """Get a specific template by ID."""
    for t in _BUILTIN_TEMPLATES:
        if t["id"] == template_id:
            return t
    raise HTTPException(status_code=404, detail="Template not found")


@router.post("/templates/{template_id}/instantiate")
def instantiate_template(
    template_id: str,
    authored_by: str = Query("Data Governance Expert"),
    db: Session = Depends(get_db),
):
    """
    Create a new policy draft from a template.

    Copies the template's policy data into a fresh draft ready for
    customization and submission.
    """
    template = None
    for t in _BUILTIN_TEMPLATES:
        if t["id"] == template_id:
            template = t
            break

    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    pd = template["policy_data"]

    # Check for existing with same title
    existing = db.query(PolicyDraft).filter(PolicyDraft.title == pd["title"]).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"A policy with title '{pd['title']}' already exists (id={existing.id}). Edit or revise it instead.",
        )

    policy = PolicyDraft(
        policy_uid=str(uuid.uuid4()),
        title=pd["title"],
        description=pd["description"],
        policy_category=pd["policy_category"],
        affected_domains=pd.get("affected_domains", ["ALL"]),
        severity=pd.get("severity", "WARNING"),
        scanner_hint=pd.get("scanner_hint", "auto"),
        remediation_guide=pd.get("remediation_guide"),
        authored_by=authored_by,
        status="draft",
        version=1,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)

    return {
        "template_id": template_id,
        "template_name": template["name"],
        "created_policy": {
            "id": policy.id,
            "policy_uid": policy.policy_uid,
            "title": policy.title,
            "status": policy.status,
            "category": policy.policy_category,
            "severity": policy.severity,
        },
    }


# ── Helpers ──────────────────────────────────────────────────────────────

def _build_export_document(policy: PolicyDraft, artifact=None) -> dict:
    """Build a portable export document for a single policy."""
    doc = {
        "policy_uid": policy.policy_uid,
        "title": policy.title,
        "description": policy.description,
        "policy_category": policy.policy_category,
        "affected_domains": policy.affected_domains or ["ALL"],
        "severity": policy.severity,
        "scanner_hint": policy.scanner_hint,
        "remediation_guide": policy.remediation_guide,
        "effective_date": policy.effective_date.isoformat() if policy.effective_date else None,
        "authored_by": policy.authored_by,
        "status": policy.status,
        "version": policy.version,
        "created_at": policy.created_at.isoformat() if policy.created_at else None,
    }
    if artifact:
        doc["artifact"] = {
            "version": artifact.version,
            "scanner_type": artifact.scanner_type,
            "yaml_content": artifact.yaml_content,
            "json_content": artifact.json_content,
            "git_commit_hash": artifact.git_commit_hash,
            "generated_at": artifact.generated_at.isoformat() if artifact.generated_at else None,
        }
    return doc

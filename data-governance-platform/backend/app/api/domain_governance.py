"""
Domain Governance & Policy Analytics API.

Provides endpoints for:
  - Domain-scoped governance views (policies per domain, coverage gaps)
  - Policy effectiveness analytics (violation trends, remediation rates)
  - Cross-domain governance matrix
"""

import logging
from typing import Optional, List
from collections import defaultdict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.policy_draft import PolicyDraft
from app.models.policy_artifact import PolicyArtifact
from app.models.policy_approval_log import PolicyApprovalLog
from app.models.policy_version import PolicyVersion
from app.models.contract import Contract
from app.models.dataset import Dataset

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/domain-governance", tags=["domain-governance"])

# Known domains for governance matrix
KNOWN_DOMAINS = ["finance", "marketing", "hr", "engineering", "operations", "legal", "ALL"]
POLICY_CATEGORIES = ["data_quality", "security", "privacy", "compliance", "lineage", "sla"]


# ── Domain Overview ──────────────────────────────────────────────────────

@router.get("/domains")
def list_domains(db: Session = Depends(get_db)):
    """
    List all known governance domains with policy counts.

    Scans all authored policies to discover domains and counts
    how many policies (by status) apply to each.
    """
    policies = db.query(PolicyDraft).all()

    domain_map = defaultdict(lambda: {
        "total": 0, "approved": 0, "pending": 0, "draft": 0,
        "rejected": 0, "deprecated": 0, "categories": set(),
    })

    discovered_domains = set()
    for p in policies:
        domains = p.affected_domains or ["ALL"]
        for d in domains:
            discovered_domains.add(d)
            domain_map[d]["total"] += 1
            status = p.status or "draft"
            if status in domain_map[d]:
                domain_map[d][status] += 1
            domain_map[d]["categories"].add(p.policy_category)

    result = []
    for d in sorted(discovered_domains):
        info = domain_map[d]
        result.append({
            "domain": d,
            "total_policies": info["total"],
            "approved": info["approved"],
            "pending": info["pending"],
            "draft": info["draft"],
            "categories_covered": sorted(info["categories"]),
            "coverage_score": _calculate_coverage_score(info["categories"]),
        })

    return {
        "total_domains": len(result),
        "domains": result,
    }


@router.get("/domains/{domain}")
def get_domain_detail(domain: str, db: Session = Depends(get_db)):
    """
    Get detailed governance information for a specific domain.

    Includes policies, category coverage, gaps, and datasets in this domain.
    """
    policies = db.query(PolicyDraft).all()

    domain_policies = []
    for p in policies:
        domains = p.affected_domains or ["ALL"]
        if domain in domains or "ALL" in domains:
            domain_policies.append({
                "id": p.id,
                "title": p.title,
                "category": p.policy_category,
                "severity": p.severity,
                "status": p.status,
                "version": p.version,
                "scanner_hint": p.scanner_hint,
            })

    # Category coverage
    covered_cats = set(p["category"] for p in domain_policies if p["status"] == "approved")
    missing_cats = [c for c in POLICY_CATEGORIES if c not in covered_cats]

    # Datasets that might belong to this domain (heuristic: name contains domain)
    datasets = db.query(Dataset).all()
    domain_datasets = [
        {"id": d.id, "name": d.name, "classification": d.classification, "contains_pii": d.contains_pii}
        for d in datasets
        if domain.lower() in (d.name or "").lower() or domain == "ALL"
    ]

    return {
        "domain": domain,
        "total_policies": len(domain_policies),
        "active_policies": sum(1 for p in domain_policies if p["status"] == "approved"),
        "policies": domain_policies,
        "categories_covered": sorted(covered_cats),
        "categories_missing": missing_cats,
        "coverage_score": _calculate_coverage_score(covered_cats),
        "datasets": domain_datasets,
    }


# ── Cross-Domain Matrix ─────────────────────────────────────────────────

@router.get("/matrix")
def get_governance_matrix(db: Session = Depends(get_db)):
    """
    Generate a cross-domain policy coverage matrix.

    Shows which categories are covered by approved policies in each domain.
    Useful for identifying governance gaps across the organization.
    """
    policies = db.query(PolicyDraft).filter(PolicyDraft.status == "approved").all()

    # Build matrix: domain → category → count
    matrix = defaultdict(lambda: defaultdict(int))
    discovered_domains = set()

    for p in policies:
        domains = p.affected_domains or ["ALL"]
        for d in domains:
            discovered_domains.add(d)
            matrix[d][p.policy_category] += 1

    rows = []
    for d in sorted(discovered_domains):
        row = {"domain": d}
        for cat in POLICY_CATEGORIES:
            row[cat] = matrix[d].get(cat, 0)
        row["total"] = sum(row[cat] for cat in POLICY_CATEGORIES)
        row["coverage_pct"] = round(
            sum(1 for cat in POLICY_CATEGORIES if matrix[d].get(cat, 0) > 0) / len(POLICY_CATEGORIES) * 100
        )
        rows.append(row)

    return {
        "categories": POLICY_CATEGORIES,
        "domains": sorted(discovered_domains),
        "matrix": rows,
    }


# ── Policy Analytics ─────────────────────────────────────────────────────

@router.get("/analytics")
def get_policy_analytics(db: Session = Depends(get_db)):
    """
    Comprehensive policy analytics dashboard data.

    Includes approval velocity, category distribution, severity trends,
    scanner type analysis, and authorship metrics.
    """
    policies = db.query(PolicyDraft).all()
    logs = db.query(PolicyApprovalLog).order_by(PolicyApprovalLog.timestamp.asc()).all()
    artifacts = db.query(PolicyArtifact).all()

    total = len(policies)

    # Approval funnel
    statuses = defaultdict(int)
    for p in policies:
        statuses[p.status] += 1

    funnel = {
        "drafted": statuses.get("draft", 0) + statuses.get("pending_approval", 0) + statuses.get("approved", 0) + statuses.get("rejected", 0) + statuses.get("deprecated", 0),
        "submitted": statuses.get("pending_approval", 0) + statuses.get("approved", 0) + statuses.get("rejected", 0),
        "approved": statuses.get("approved", 0) + statuses.get("deprecated", 0),
        "rejected": statuses.get("rejected", 0),
        "deprecated": statuses.get("deprecated", 0),
    }

    # Category distribution
    cat_dist = defaultdict(int)
    for p in policies:
        cat_dist[p.policy_category] += 1

    # Severity distribution
    sev_dist = defaultdict(int)
    for p in policies:
        sev_dist[p.severity] += 1

    # Scanner type from artifacts
    scanner_dist = defaultdict(int)
    for a in artifacts:
        scanner_dist[a.scanner_type] += 1

    # Authorship leaderboard
    author_counts = defaultdict(int)
    for p in policies:
        author_counts[p.authored_by] += 1
    top_authors = sorted(author_counts.items(), key=lambda x: -x[1])[:10]

    # Approval activity over time (group by month)
    monthly_activity = defaultdict(lambda: {"approved": 0, "rejected": 0, "submitted": 0})
    for log in logs:
        if log.timestamp:
            month_key = log.timestamp.strftime("%Y-%m")
            action = log.action
            if action in ("approved", "rejected", "submitted"):
                monthly_activity[month_key][action] += 1

    activity_timeline = [
        {"month": k, **v}
        for k, v in sorted(monthly_activity.items())
    ]

    # Average versions per policy
    version_counts = [p.version for p in policies]
    avg_versions = round(sum(version_counts) / len(version_counts), 1) if version_counts else 0

    # Multi-domain policies
    multi_domain = sum(1 for p in policies if len(p.affected_domains or []) > 1)

    return {
        "total_policies": total,
        "approval_funnel": funnel,
        "category_distribution": dict(cat_dist),
        "severity_distribution": dict(sev_dist),
        "scanner_distribution": dict(scanner_dist),
        "top_authors": [{"author": a, "count": c} for a, c in top_authors],
        "activity_timeline": activity_timeline,
        "avg_versions_per_policy": avg_versions,
        "multi_domain_policies": multi_domain,
        "total_artifacts": len(artifacts),
        "total_audit_events": len(logs),
    }


# ── Policy Effectiveness ─────────────────────────────────────────────────

@router.get("/effectiveness")
def get_policy_effectiveness(db: Session = Depends(get_db)):
    """
    Measure policy effectiveness based on contract validation outcomes.

    For each approved authored policy, shows how many contracts it catches
    violations in (enforcement rate) and overall governance health score.
    """
    approved_policies = db.query(PolicyDraft).filter(PolicyDraft.status == "approved").all()
    contracts = db.query(Contract).all()

    # Count how many contracts have each validation status
    contract_statuses = defaultdict(int)
    total_violations_stored = 0
    for c in contracts:
        contract_statuses[c.validation_status or "unvalidated"] += 1
        results = c.validation_results or {}
        if isinstance(results, dict):
            total_violations_stored += len(results.get("violations", []))

    total_contracts = len(contracts)
    validated = total_contracts - contract_statuses.get("unvalidated", 0) - contract_statuses.get("pending", 0)

    # Health score: weighted combination of pass rate and policy coverage
    pass_rate = (contract_statuses.get("passed", 0) / validated * 100) if validated > 0 else 0
    policy_coverage = (len(approved_policies) / max(len(POLICY_CATEGORIES), 1)) * 100
    health_score = round(min(100, (pass_rate * 0.6 + min(policy_coverage, 100) * 0.4)), 1)

    # Per-policy effectiveness summary
    policy_summaries = []
    for p in approved_policies:
        # Count versions and artifacts
        version_count = db.query(PolicyVersion).filter(PolicyVersion.policy_id == p.id).count()
        artifact_count = db.query(PolicyArtifact).filter(PolicyArtifact.policy_id == p.id).count()

        policy_summaries.append({
            "id": p.id,
            "title": p.title,
            "category": p.policy_category,
            "severity": p.severity,
            "version": p.version,
            "domains": p.affected_domains or ["ALL"],
            "total_versions": version_count,
            "total_artifacts": artifact_count,
        })

    return {
        "health_score": health_score,
        "total_contracts": total_contracts,
        "contracts_validated": validated,
        "contract_statuses": dict(contract_statuses),
        "total_violations_detected": total_violations_stored,
        "pass_rate_pct": round(pass_rate, 1),
        "active_policies": len(approved_policies),
        "policy_coverage_pct": round(min(policy_coverage, 100), 1),
        "policy_summaries": policy_summaries,
    }


# ── Helpers ──────────────────────────────────────────────────────────────

def _calculate_coverage_score(categories) -> int:
    """Calculate a 0-100 coverage score based on how many categories are covered."""
    if not categories:
        return 0
    return round(len(set(categories)) / len(POLICY_CATEGORIES) * 100)

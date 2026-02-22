"""
Policy Conflict Detection & Resolution API.

Provides endpoints for:
  - Automatic detection of overlapping or contradictory policies
  - Conflict listing, detail, and resolution workflow
  - Conflict statistics and recommendations
"""

import logging
from typing import Optional, List
from collections import defaultdict
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.policy_draft import PolicyDraft

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/policy-conflicts", tags=["policy-conflicts"])

# Conflict types
CONFLICT_TYPES = {
    "overlap": "Two policies cover the same domain and category with different rules",
    "contradiction": "Policies impose contradictory requirements",
    "severity_mismatch": "Same concern addressed at different severity levels",
    "domain_gap": "A domain is only partially covered by related policies",
    "redundancy": "Policies are functionally equivalent (duplicate effort)",
}

# Severity hierarchy for comparison
SEVERITY_RANK = {"CRITICAL": 3, "WARNING": 2, "INFO": 1}


# ── Pydantic Schemas ────────────────────────────────────────────────────

class ConflictResolution(BaseModel):
    strategy: str  # "keep_both", "merge", "deprecate_one", "escalate"
    resolution_notes: str
    resolved_by: str = "governance-admin"


# ── In-Memory Conflict Store ────────────────────────────────────────────
# Conflicts are computed on-the-fly and optionally stored for resolution tracking.
# In production this would be a DB table; here we use a lightweight dict.

_conflict_store: dict = {}  # conflict_id -> conflict record
_next_conflict_id = 1


def _reset_store():
    """Reset conflict store (for testing)."""
    global _conflict_store, _next_conflict_id
    _conflict_store = {}
    _next_conflict_id = 1


# ── Detection Logic ─────────────────────────────────────────────────────

def _detect_overlaps(policies: List[PolicyDraft]) -> list:
    """Detect policies that cover the same domain+category pair."""
    conflicts = []
    # Group by (domain, category)
    domain_cat_map = defaultdict(list)
    for p in policies:
        domains = p.affected_domains or ["ALL"]
        for d in domains:
            domain_cat_map[(d, p.policy_category)].append(p)

    for (domain, category), group in domain_cat_map.items():
        if len(group) < 2:
            continue
        # Check pairs for overlap
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                conflict = {
                    "type": "overlap",
                    "description": f"Both policies cover {category} in {domain} domain",
                    "domain": domain,
                    "category": category,
                    "policy_a": {"id": a.id, "title": a.title, "severity": a.severity, "status": a.status},
                    "policy_b": {"id": b.id, "title": b.title, "severity": b.severity, "status": b.status},
                }
                # Check for severity mismatch
                if a.severity != b.severity:
                    conflict["type"] = "severity_mismatch"
                    conflict["description"] = (
                        f"Policies address {category} in {domain} at different severity "
                        f"levels: {a.severity} vs {b.severity}"
                    )
                # Check for potential contradiction via keyword heuristic
                if _descriptions_contradict(a.description, b.description):
                    conflict["type"] = "contradiction"
                    conflict["description"] = (
                        f"Policies may impose contradictory {category} requirements in {domain}"
                    )
                conflicts.append(conflict)

    return conflicts


def _detect_redundancies(policies: List[PolicyDraft]) -> list:
    """Detect policies that are functionally equivalent."""
    conflicts = []
    seen = set()

    for i in range(len(policies)):
        for j in range(i + 1, len(policies)):
            a, b = policies[i], policies[j]
            pair_key = tuple(sorted([a.id, b.id]))
            if pair_key in seen:
                continue

            if _is_redundant(a, b):
                seen.add(pair_key)
                domains_a = set(a.affected_domains or ["ALL"])
                domains_b = set(b.affected_domains or ["ALL"])
                shared = domains_a & domains_b
                if shared:
                    conflicts.append({
                        "type": "redundancy",
                        "description": f"Policies appear functionally equivalent in domains: {', '.join(sorted(shared))}",
                        "domain": sorted(shared)[0],
                        "category": a.policy_category,
                        "policy_a": {"id": a.id, "title": a.title, "severity": a.severity, "status": a.status},
                        "policy_b": {"id": b.id, "title": b.title, "severity": b.severity, "status": b.status},
                    })

    return conflicts


def _descriptions_contradict(desc_a: str, desc_b: str) -> bool:
    """
    Heuristic: detect potential contradictions between two policy descriptions.
    Looks for opposing keywords (require vs prohibit, allow vs deny, etc.).
    """
    neg_pairs = [
        ({"require", "must", "mandatory", "enforce", "always"}, {"prohibit", "never", "forbid", "deny", "disallow"}),
        ({"encrypt", "encrypted"}, {"unencrypted", "plaintext", "no encryption"}),
        ({"retain",}, {"delete", "purge", "remove"}),
    ]
    a_lower = (desc_a or "").lower()
    b_lower = (desc_b or "").lower()

    for positive, negative in neg_pairs:
        a_has_pos = any(w in a_lower for w in positive)
        a_has_neg = any(w in a_lower for w in negative)
        b_has_pos = any(w in b_lower for w in positive)
        b_has_neg = any(w in b_lower for w in negative)

        if (a_has_pos and b_has_neg) or (a_has_neg and b_has_pos):
            return True

    return False


def _is_redundant(a: PolicyDraft, b: PolicyDraft) -> bool:
    """Check if two policies are functionally redundant."""
    if a.policy_category != b.policy_category:
        return False
    if a.severity != b.severity:
        return False
    if a.scanner_hint != b.scanner_hint:
        return False
    # Similar descriptions (basic similarity)
    a_words = set((a.description or "").lower().split())
    b_words = set((b.description or "").lower().split())
    if not a_words or not b_words:
        return False
    overlap = len(a_words & b_words)
    union = len(a_words | b_words)
    jaccard = overlap / union if union > 0 else 0
    return jaccard > 0.7


# ── Endpoints ───────────────────────────────────────────────────────────

@router.post("/detect")
def detect_conflicts(
    scope: Optional[str] = Query(None, description="Limit detection to a specific domain"),
    status_filter: Optional[str] = Query("approved", description="Filter policies by status"),
    db: Session = Depends(get_db),
):
    """
    Run conflict detection across all policies.

    Scans for overlaps, contradictions, severity mismatches, and redundancies.
    Results are stored for later resolution.
    """
    global _next_conflict_id

    query = db.query(PolicyDraft)
    if status_filter:
        query = query.filter(PolicyDraft.status == status_filter)
    policies = query.all()

    if scope:
        policies = [
            p for p in policies
            if scope in (p.affected_domains or ["ALL"]) or "ALL" in (p.affected_domains or [])
        ]

    # Run detectors
    all_conflicts = []
    all_conflicts.extend(_detect_overlaps(policies))
    all_conflicts.extend(_detect_redundancies(policies))

    # Store results
    new_ids = []
    for conflict in all_conflicts:
        # Dedup: check if same pair already in store
        pair_key = tuple(sorted([conflict["policy_a"]["id"], conflict["policy_b"]["id"]]))
        existing = [
            cid for cid, c in _conflict_store.items()
            if tuple(sorted([c["policy_a"]["id"], c["policy_b"]["id"]])) == pair_key
            and c["type"] == conflict["type"]
        ]
        if existing:
            new_ids.append(existing[0])
            continue

        conflict_id = _next_conflict_id
        _next_conflict_id += 1
        conflict["id"] = conflict_id
        conflict["status"] = "open"
        conflict["detected_at"] = datetime.utcnow().isoformat()
        conflict["resolution"] = None
        _conflict_store[conflict_id] = conflict
        new_ids.append(conflict_id)

    return {
        "total_policies_scanned": len(policies),
        "total_conflicts_found": len(all_conflicts),
        "new_conflicts": sum(1 for c in _conflict_store.values() if c["id"] in new_ids and c.get("resolution") is None),
        "conflict_ids": new_ids,
        "by_type": _count_by_type(all_conflicts),
    }


@router.get("/")
def list_conflicts(
    status: Optional[str] = Query(None, description="Filter by status: open, resolved"),
    conflict_type: Optional[str] = Query(None, description="Filter by conflict type"),
):
    """List all detected conflicts with optional filtering."""
    conflicts = list(_conflict_store.values())

    if status:
        conflicts = [c for c in conflicts if c["status"] == status]
    if conflict_type:
        conflicts = [c for c in conflicts if c["type"] == conflict_type]

    # Sort: open first, then by detected_at desc
    conflicts.sort(key=lambda c: (c["status"] != "open", c.get("detected_at", "")), reverse=False)

    return {
        "total": len(conflicts),
        "open": sum(1 for c in conflicts if c["status"] == "open"),
        "resolved": sum(1 for c in conflicts if c["status"] == "resolved"),
        "conflicts": conflicts,
    }


@router.get("/stats")
def conflict_stats():
    """Get summary statistics about policy conflicts."""
    conflicts = list(_conflict_store.values())
    open_conflicts = [c for c in conflicts if c["status"] == "open"]
    resolved_conflicts = [c for c in conflicts if c["status"] == "resolved"]

    type_dist = defaultdict(int)
    domain_dist = defaultdict(int)
    severity_pairs = []

    for c in conflicts:
        type_dist[c["type"]] += 1
        domain_dist[c.get("domain", "unknown")] += 1
        if c["type"] == "severity_mismatch":
            severity_pairs.append({
                "policy_a": c["policy_a"]["title"],
                "severity_a": c["policy_a"]["severity"],
                "policy_b": c["policy_b"]["title"],
                "severity_b": c["policy_b"]["severity"],
            })

    # Resolution strategies used
    strategy_dist = defaultdict(int)
    for c in resolved_conflicts:
        if c.get("resolution"):
            strategy_dist[c["resolution"]["strategy"]] += 1

    return {
        "total_conflicts": len(conflicts),
        "open": len(open_conflicts),
        "resolved": len(resolved_conflicts),
        "resolution_rate_pct": round(len(resolved_conflicts) / len(conflicts) * 100, 1) if conflicts else 0,
        "by_type": dict(type_dist),
        "by_domain": dict(domain_dist),
        "severity_mismatches": severity_pairs,
        "resolution_strategies": dict(strategy_dist),
    }


@router.get("/{conflict_id}")
def get_conflict(conflict_id: int):
    """Get detailed information about a specific conflict."""
    conflict = _conflict_store.get(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    # Add recommendation
    conflict_copy = dict(conflict)
    conflict_copy["recommendation"] = _get_recommendation(conflict)

    return conflict_copy


@router.post("/{conflict_id}/resolve")
def resolve_conflict(conflict_id: int, resolution: ConflictResolution):
    """
    Resolve a conflict with a chosen strategy.

    Strategies:
    - keep_both: Accept both policies as valid (document reasoning)
    - merge: Combine policies into one (manual follow-up)
    - deprecate_one: Mark one policy for deprecation
    - escalate: Flag for senior governance review
    """
    conflict = _conflict_store.get(conflict_id)
    if not conflict:
        raise HTTPException(status_code=404, detail="Conflict not found")

    if conflict["status"] == "resolved":
        raise HTTPException(status_code=409, detail="Conflict already resolved")

    valid_strategies = ["keep_both", "merge", "deprecate_one", "escalate"]
    if resolution.strategy not in valid_strategies:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid strategy. Must be one of: {', '.join(valid_strategies)}"
        )

    conflict["status"] = "resolved"
    conflict["resolution"] = {
        "strategy": resolution.strategy,
        "notes": resolution.resolution_notes,
        "resolved_by": resolution.resolved_by,
        "resolved_at": datetime.utcnow().isoformat(),
    }

    return conflict


@router.post("/reset")
def reset_conflicts():
    """Reset all conflict data (for testing/admin purposes)."""
    _reset_store()
    return {"message": "Conflict store reset", "total": 0}


# ── Helpers ──────────────────────────────────────────────────────────────

def _count_by_type(conflicts: list) -> dict:
    counts = defaultdict(int)
    for c in conflicts:
        counts[c["type"]] += 1
    return dict(counts)


def _get_recommendation(conflict: dict) -> dict:
    """Generate a resolution recommendation based on conflict type."""
    ctype = conflict["type"]

    if ctype == "severity_mismatch":
        sev_a = SEVERITY_RANK.get(conflict["policy_a"]["severity"], 0)
        sev_b = SEVERITY_RANK.get(conflict["policy_b"]["severity"], 0)
        higher = conflict["policy_a"] if sev_a >= sev_b else conflict["policy_b"]
        return {
            "strategy": "merge",
            "reason": f"Align both policies to the higher severity ({higher['severity']}) for consistent enforcement",
            "action": f"Consider updating the lower-severity policy to match '{higher['title']}'",
        }
    elif ctype == "contradiction":
        return {
            "strategy": "escalate",
            "reason": "Contradictory policies require governance board review to determine the correct rule",
            "action": "Escalate to the governance committee for a binding decision",
        }
    elif ctype == "redundancy":
        return {
            "strategy": "deprecate_one",
            "reason": "Redundant policies add maintenance burden without additional protection",
            "action": "Deprecate the older or less comprehensive policy and consolidate into one",
        }
    else:  # overlap
        return {
            "strategy": "keep_both",
            "reason": "Overlapping policies may serve different aspects of the same concern",
            "action": "Review both policies to confirm they complement rather than duplicate each other",
        }

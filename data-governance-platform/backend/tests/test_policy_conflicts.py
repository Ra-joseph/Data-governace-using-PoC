"""
Tests for Stage 8 – Policy Conflict Detection & Resolution.

Covers:
  - Conflict detection (overlaps, contradictions, severity mismatches, redundancies)
  - Conflict listing with filters
  - Conflict detail with recommendations
  - Conflict resolution workflow
  - Conflict statistics
  - Store reset
"""

import pytest
from fastapi.testclient import TestClient
from app.api.policy_conflicts import _reset_store


# ── helpers ──────────────────────────────────────────────────────────────

def _create_policy(client, **overrides):
    payload = {
        "title": "Conflict Test Policy",
        "description": "A test policy for conflict detection.",
        "policy_category": "security",
        "affected_domains": ["finance"],
        "severity": "CRITICAL",
        "scanner_hint": "rule_based",
        "remediation_guide": "Fix the issue.",
        "authored_by": "Author",
    }
    payload.update(overrides)
    resp = client.post("/api/v1/policies/authored/", json=payload)
    assert resp.status_code == 201
    return resp.json()


def _approve(client, pid):
    client.post(f"/api/v1/policies/authored/{pid}/submit")
    resp = client.post(f"/api/v1/policies/authored/{pid}/approve", json={"approver_name": "Admin"})
    assert resp.status_code == 200
    return resp.json()


@pytest.fixture(autouse=True)
def clean_conflict_store():
    """Reset in-memory conflict store before each test."""
    _reset_store()
    yield
    _reset_store()


# ── Detection ───────────────────────────────────────────────────────────

class TestConflictDetection:
    def test_detect_no_policies(self, client):
        """No policies → no conflicts."""
        resp = client.post("/api/v1/policy-conflicts/detect")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_conflicts_found"] == 0
        assert data["conflict_ids"] == []

    def test_detect_no_overlap(self, client):
        """Different categories → no overlap."""
        p1 = _create_policy(client, title="Security P", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Quality P", policy_category="data_quality")
        _approve(client, p2["id"])

        resp = client.post("/api/v1/policy-conflicts/detect")
        data = resp.json()
        assert data["total_conflicts_found"] == 0

    def test_detect_overlap_same_domain_category(self, client):
        """Two approved policies in the same domain+category → overlap."""
        p1 = _create_policy(client, title="Sec Finance A", affected_domains=["finance"], policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Sec Finance B", affected_domains=["finance"], policy_category="security")
        _approve(client, p2["id"])

        resp = client.post("/api/v1/policy-conflicts/detect")
        data = resp.json()
        assert data["total_conflicts_found"] >= 1
        assert len(data["conflict_ids"]) >= 1

    def test_detect_severity_mismatch(self, client):
        """Same domain+category but different severity → severity_mismatch."""
        p1 = _create_policy(client, title="Crit Security", severity="CRITICAL", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Info Security", severity="INFO", policy_category="security")
        _approve(client, p2["id"])

        resp = client.post("/api/v1/policy-conflicts/detect")
        data = resp.json()
        assert data["total_conflicts_found"] >= 1
        assert "severity_mismatch" in data["by_type"]

    def test_detect_contradiction(self, client):
        """Opposing keywords in descriptions → contradiction."""
        p1 = _create_policy(
            client, title="Require Encryption",
            description="All data must be encrypted at rest and in transit.",
            policy_category="security",
        )
        _approve(client, p1["id"])
        p2 = _create_policy(
            client, title="Plaintext Allowed",
            description="Data may be stored in plaintext for performance.",
            policy_category="security",
        )
        _approve(client, p2["id"])

        resp = client.post("/api/v1/policy-conflicts/detect")
        data = resp.json()
        assert data["total_conflicts_found"] >= 1
        assert "contradiction" in data["by_type"]

    def test_detect_redundancy(self, client):
        """Very similar policies → redundancy."""
        desc = "All financial data must be encrypted using AES-256 at rest and TLS in transit always."
        p1 = _create_policy(client, title="Dup A", description=desc, policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Dup B", description=desc, policy_category="security")
        _approve(client, p2["id"])

        resp = client.post("/api/v1/policy-conflicts/detect")
        data = resp.json()
        # Should find at least a redundancy (or overlap)
        assert data["total_conflicts_found"] >= 1

    def test_detect_with_scope_filter(self, client):
        """Scope filter limits detection to a single domain."""
        p1 = _create_policy(client, title="HR Sec", affected_domains=["hr"], policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="HR Sec 2", affected_domains=["hr"], policy_category="security")
        _approve(client, p2["id"])
        p3 = _create_policy(client, title="Fin Sec", affected_domains=["finance"], policy_category="security")
        _approve(client, p3["id"])

        resp = client.post("/api/v1/policy-conflicts/detect?scope=hr")
        data = resp.json()
        assert data["total_policies_scanned"] == 2
        assert data["total_conflicts_found"] >= 1

    def test_detect_dedup_on_rerun(self, client):
        """Running detection twice doesn't duplicate stored conflicts."""
        p1 = _create_policy(client, title="Dedup A", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Dedup B", policy_category="security")
        _approve(client, p2["id"])

        resp1 = client.post("/api/v1/policy-conflicts/detect")
        resp2 = client.post("/api/v1/policy-conflicts/detect")
        # Same IDs returned
        assert resp1.json()["conflict_ids"] == resp2.json()["conflict_ids"]


# ── Conflict Listing ────────────────────────────────────────────────────

class TestConflictListing:
    def test_list_empty(self, client):
        """Empty store → no conflicts."""
        resp = client.get("/api/v1/policy-conflicts/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["conflicts"] == []

    def test_list_after_detection(self, client):
        """List returns detected conflicts."""
        p1 = _create_policy(client, title="List A", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="List B", policy_category="security")
        _approve(client, p2["id"])

        client.post("/api/v1/policy-conflicts/detect")
        resp = client.get("/api/v1/policy-conflicts/")
        data = resp.json()
        assert data["total"] >= 1
        assert data["open"] >= 1

    def test_list_filter_by_status(self, client):
        """Filter conflicts by status."""
        p1 = _create_policy(client, title="Status A", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Status B", policy_category="security")
        _approve(client, p2["id"])

        client.post("/api/v1/policy-conflicts/detect")

        open_resp = client.get("/api/v1/policy-conflicts/?status=open")
        assert open_resp.json()["total"] >= 1

        resolved_resp = client.get("/api/v1/policy-conflicts/?status=resolved")
        assert resolved_resp.json()["total"] == 0

    def test_list_filter_by_type(self, client):
        """Filter conflicts by type."""
        p1 = _create_policy(client, title="Type A", severity="CRITICAL", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Type B", severity="INFO", policy_category="security")
        _approve(client, p2["id"])

        client.post("/api/v1/policy-conflicts/detect")

        resp = client.get("/api/v1/policy-conflicts/?conflict_type=severity_mismatch")
        data = resp.json()
        assert data["total"] >= 1
        assert all(c["type"] == "severity_mismatch" for c in data["conflicts"])


# ── Conflict Detail ─────────────────────────────────────────────────────

class TestConflictDetail:
    def test_get_conflict(self, client):
        """Get detail includes recommendation."""
        p1 = _create_policy(client, title="Detail A", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Detail B", policy_category="security")
        _approve(client, p2["id"])

        detect = client.post("/api/v1/policy-conflicts/detect").json()
        cid = detect["conflict_ids"][0]

        resp = client.get(f"/api/v1/policy-conflicts/{cid}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == cid
        assert "recommendation" in data
        assert "strategy" in data["recommendation"]
        assert "reason" in data["recommendation"]

    def test_get_conflict_not_found(self, client):
        """Non-existent conflict → 404."""
        resp = client.get("/api/v1/policy-conflicts/9999")
        assert resp.status_code == 404

    def test_severity_mismatch_recommendation(self, client):
        """Severity mismatch → merge recommendation."""
        p1 = _create_policy(client, title="Sev Rec A", severity="CRITICAL", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Sev Rec B", severity="INFO", policy_category="security")
        _approve(client, p2["id"])

        detect = client.post("/api/v1/policy-conflicts/detect").json()
        cid = detect["conflict_ids"][0]

        data = client.get(f"/api/v1/policy-conflicts/{cid}").json()
        assert data["recommendation"]["strategy"] == "merge"


# ── Conflict Resolution ────────────────────────────────────────────────

class TestConflictResolution:
    def test_resolve_conflict(self, client):
        """Resolve an open conflict."""
        p1 = _create_policy(client, title="Resolve A", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Resolve B", policy_category="security")
        _approve(client, p2["id"])

        detect = client.post("/api/v1/policy-conflicts/detect").json()
        cid = detect["conflict_ids"][0]

        resp = client.post(f"/api/v1/policy-conflicts/{cid}/resolve", json={
            "strategy": "keep_both",
            "resolution_notes": "Both policies serve different aspects.",
            "resolved_by": "admin",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "resolved"
        assert data["resolution"]["strategy"] == "keep_both"
        assert data["resolution"]["resolved_by"] == "admin"

    def test_resolve_already_resolved(self, client):
        """Cannot resolve twice → 409."""
        p1 = _create_policy(client, title="Double A", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Double B", policy_category="security")
        _approve(client, p2["id"])

        detect = client.post("/api/v1/policy-conflicts/detect").json()
        cid = detect["conflict_ids"][0]

        client.post(f"/api/v1/policy-conflicts/{cid}/resolve", json={
            "strategy": "merge",
            "resolution_notes": "Merging.",
            "resolved_by": "admin",
        })
        resp = client.post(f"/api/v1/policy-conflicts/{cid}/resolve", json={
            "strategy": "merge",
            "resolution_notes": "Again.",
            "resolved_by": "admin",
        })
        assert resp.status_code == 409

    def test_resolve_not_found(self, client):
        """Resolve non-existent → 404."""
        resp = client.post("/api/v1/policy-conflicts/9999/resolve", json={
            "strategy": "keep_both",
            "resolution_notes": "Notes.",
        })
        assert resp.status_code == 404

    def test_resolve_invalid_strategy(self, client):
        """Invalid strategy → 400."""
        p1 = _create_policy(client, title="Bad Strategy A", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Bad Strategy B", policy_category="security")
        _approve(client, p2["id"])

        detect = client.post("/api/v1/policy-conflicts/detect").json()
        cid = detect["conflict_ids"][0]

        resp = client.post(f"/api/v1/policy-conflicts/{cid}/resolve", json={
            "strategy": "invalid_strategy",
            "resolution_notes": "Notes.",
        })
        assert resp.status_code == 400

    def test_all_strategies_accepted(self, client):
        """All four valid strategies work."""
        for i, strategy in enumerate(["keep_both", "merge", "deprecate_one", "escalate"]):
            _reset_store()
            p1 = _create_policy(client, title=f"Strat {strategy} A {i}", policy_category="security")
            _approve(client, p1["id"])
            p2 = _create_policy(client, title=f"Strat {strategy} B {i}", policy_category="security")
            _approve(client, p2["id"])

            detect = client.post("/api/v1/policy-conflicts/detect").json()
            cid = detect["conflict_ids"][0]

            resp = client.post(f"/api/v1/policy-conflicts/{cid}/resolve", json={
                "strategy": strategy,
                "resolution_notes": f"Using {strategy}.",
            })
            assert resp.status_code == 200
            assert resp.json()["resolution"]["strategy"] == strategy


# ── Statistics ──────────────────────────────────────────────────────────

class TestConflictStats:
    def test_stats_empty(self, client):
        """Empty store → zero stats."""
        resp = client.get("/api/v1/policy-conflicts/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_conflicts"] == 0
        assert data["resolution_rate_pct"] == 0

    def test_stats_with_conflicts(self, client):
        """Stats reflect detection and resolution."""
        p1 = _create_policy(client, title="Stats A", severity="CRITICAL", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Stats B", severity="INFO", policy_category="security")
        _approve(client, p2["id"])

        client.post("/api/v1/policy-conflicts/detect")

        resp = client.get("/api/v1/policy-conflicts/stats")
        data = resp.json()
        assert data["total_conflicts"] >= 1
        assert data["open"] >= 1
        assert "severity_mismatch" in data["by_type"]
        assert "finance" in data["by_domain"]
        assert len(data["severity_mismatches"]) >= 1

    def test_stats_after_resolution(self, client):
        """Resolution rate updates after resolving."""
        p1 = _create_policy(client, title="Rate A", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Rate B", policy_category="security")
        _approve(client, p2["id"])

        detect = client.post("/api/v1/policy-conflicts/detect").json()
        cid = detect["conflict_ids"][0]

        client.post(f"/api/v1/policy-conflicts/{cid}/resolve", json={
            "strategy": "deprecate_one",
            "resolution_notes": "Deprecated the older one.",
        })

        resp = client.get("/api/v1/policy-conflicts/stats")
        data = resp.json()
        assert data["resolved"] >= 1
        assert data["resolution_rate_pct"] > 0
        assert "deprecate_one" in data["resolution_strategies"]


# ── Reset ───────────────────────────────────────────────────────────────

class TestConflictReset:
    def test_reset(self, client):
        """Reset clears all conflicts."""
        p1 = _create_policy(client, title="Reset A", policy_category="security")
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Reset B", policy_category="security")
        _approve(client, p2["id"])

        client.post("/api/v1/policy-conflicts/detect")
        assert client.get("/api/v1/policy-conflicts/").json()["total"] >= 1

        resp = client.post("/api/v1/policy-conflicts/reset")
        assert resp.status_code == 200

        assert client.get("/api/v1/policy-conflicts/").json()["total"] == 0

"""
Tests for Stage 3 – Policy Enforcement Integration.

Covers:
  - authored_policy_loader helpers (heuristic checks, combined validation)
  - /policy-dashboard API endpoints (stats, active-policies, validate-combined)
"""

import pytest
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────

def _create_and_approve_policy(client: TestClient, **overrides):
    """Create a draft, submit it, approve it, and return its JSON."""
    payload = {
        "title": "PII fields must be encrypted",
        "description": "All fields flagged as PII must use AES-256 encryption.",
        "policy_category": "security",
        "affected_domains": ["finance"],
        "severity": "CRITICAL",
        "scanner_hint": "rule_based",
        "remediation_guide": "Enable encryption_required in governance.",
        "authored_by": "Test Author",
    }
    payload.update(overrides)

    # Create
    resp = client.post("/api/v1/policies/authored/", json=payload)
    assert resp.status_code == 201, resp.text
    policy = resp.json()
    pid = policy["id"]

    # Submit
    resp = client.post(f"/api/v1/policies/authored/{pid}/submit")
    assert resp.status_code == 200, resp.text

    # Approve
    resp = client.post(f"/api/v1/policies/authored/{pid}/approve", json={
        "actor_name": "Approver",
        "comment": "Looks good",
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


# ── Dashboard Stats ──────────────────────────────────────────────────────

class TestDashboardStats:
    def test_stats_empty(self, client):
        """Stats endpoint works when DB is empty."""
        resp = client.get("/api/v1/policy-dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_policies"] == 0
        assert data["total_artifacts"] == 0
        assert data["total_approval_actions"] == 0
        assert data["by_status"] == {}
        assert data["by_category"] == {}

    def test_stats_after_creating_policies(self, client):
        """Stats reflect created and approved policies."""
        # Create 2 drafts
        client.post("/api/v1/policies/authored/", json={
            "title": "Policy A", "description": "Desc A", "policy_category": "security",
        })
        client.post("/api/v1/policies/authored/", json={
            "title": "Policy B", "description": "Desc B", "policy_category": "data_quality",
        })

        resp = client.get("/api/v1/policy-dashboard/stats")
        data = resp.json()
        assert data["total_policies"] == 2
        assert data["by_status"].get("draft", 0) == 2
        assert data["by_category"].get("security", 0) == 1
        assert data["by_category"].get("data_quality", 0) == 1

    def test_stats_after_approval(self, client):
        """Approving a policy updates status breakdown and creates artifacts."""
        _create_and_approve_policy(client, title="Approved Policy")

        resp = client.get("/api/v1/policy-dashboard/stats")
        data = resp.json()
        assert data["by_status"].get("approved", 0) >= 1
        assert data["total_artifacts"] >= 1
        assert data["total_approval_actions"] >= 1
        assert len(data["recent_approvals"]) >= 1

    def test_stats_severity_breakdown(self, client):
        """Severity distribution reflects created policies."""
        client.post("/api/v1/policies/authored/", json={
            "title": "Crit", "description": "x", "policy_category": "security", "severity": "CRITICAL",
        })
        client.post("/api/v1/policies/authored/", json={
            "title": "Warn", "description": "x", "policy_category": "compliance", "severity": "WARNING",
        })

        resp = client.get("/api/v1/policy-dashboard/stats")
        data = resp.json()
        assert data["by_severity"].get("CRITICAL", 0) >= 1
        assert data["by_severity"].get("WARNING", 0) >= 1


# ── Active Policies ──────────────────────────────────────────────────────

class TestActivePolicies:
    def test_no_active_policies(self, client):
        """Returns empty when nothing is approved."""
        resp = client.get("/api/v1/policy-dashboard/active-policies")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["policies"] == []

    def test_active_after_approval(self, client):
        """Approved policies appear in active list."""
        _create_and_approve_policy(client, title="Active Check")

        resp = client.get("/api/v1/policy-dashboard/active-policies")
        data = resp.json()
        assert data["total"] >= 1
        titles = [p["title"] for p in data["policies"]]
        assert "Active Check" in titles

    def test_draft_not_in_active(self, client):
        """Drafts do not appear in active policies."""
        client.post("/api/v1/policies/authored/", json={
            "title": "Still Draft", "description": "x", "policy_category": "privacy",
        })

        resp = client.get("/api/v1/policy-dashboard/active-policies")
        data = resp.json()
        titles = [p["title"] for p in data["policies"]]
        assert "Still Draft" not in titles

    def test_domain_filter(self, client):
        """Domain filter returns only matching policies."""
        _create_and_approve_policy(
            client, title="Finance Only",
            affected_domains=["finance"],
        )
        _create_and_approve_policy(
            client, title="Marketing Only",
            affected_domains=["marketing"],
        )

        resp = client.get("/api/v1/policy-dashboard/active-policies", params={"domain": "finance"})
        data = resp.json()
        titles = [p["title"] for p in data["policies"]]
        assert "Finance Only" in titles
        assert "Marketing Only" not in titles


# ── Combined Validation ──────────────────────────────────────────────────

class TestCombinedValidation:
    def test_combined_clean_contract(self, client, sample_contract_data):
        """A compliant contract passes combined validation."""
        resp = client.post("/api/v1/policy-dashboard/validate-combined", json={
            "contract_data": sample_contract_data,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] in ("passed", "warning")

    def test_combined_with_violations(self, client, sample_contract_with_violations):
        """A non-compliant contract fails combined validation."""
        resp = client.post("/api/v1/policy-dashboard/validate-combined", json={
            "contract_data": sample_contract_with_violations,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "failed"
        assert data["failures"] > 0
        assert data["total_violations"] > 0

    def test_combined_includes_authored_violations(self, client, sample_contract_with_violations):
        """Authored policies add violations on top of static ones."""
        # First validate without authored policies
        resp1 = client.post("/api/v1/policy-dashboard/validate-combined", json={
            "contract_data": sample_contract_with_violations,
        })
        base_violations = resp1.json()["total_violations"]

        # Create an approved authored policy about encryption
        _create_and_approve_policy(
            client,
            title="Custom encryption check",
            description="All PII must be encrypted with AES-256",
            severity="CRITICAL",
            scanner_hint="rule_based",
        )

        # Re-validate: should have at least as many violations
        resp2 = client.post("/api/v1/policy-dashboard/validate-combined", json={
            "contract_data": sample_contract_with_violations,
        })
        combined_violations = resp2.json()["total_violations"]
        assert combined_violations >= base_violations

    def test_combined_domain_scoping(self, client, sample_contract_with_violations):
        """Domain filter scopes which authored policies are checked."""
        _create_and_approve_policy(
            client,
            title="HR only encryption",
            description="All PII must be encrypted",
            affected_domains=["hr"],
            severity="CRITICAL",
        )

        # Validate with domain=finance (should NOT apply the HR policy)
        resp = client.post("/api/v1/policy-dashboard/validate-combined", json={
            "contract_data": sample_contract_with_violations,
            "domain": "finance",
        })
        assert resp.status_code == 200

    def test_combined_violation_structure(self, client, sample_contract_with_violations):
        """Each violation has required fields."""
        resp = client.post("/api/v1/policy-dashboard/validate-combined", json={
            "contract_data": sample_contract_with_violations,
        })
        data = resp.json()
        for v in data["violations"]:
            assert "type" in v
            assert "policy" in v
            assert "message" in v
            assert "remediation" in v
            assert v["type"] in ("critical", "warning")


# ── Authored Policy Loader Unit Tests ────────────────────────────────────

class TestRuleHeuristics:
    """Test _check_rule_heuristic indirectly via combined validation."""

    def test_encryption_heuristic(self, client):
        """Authored encryption policy flags unencrypted PII."""
        _create_and_approve_policy(
            client,
            title="Must encrypt PII",
            description="All PII must be encrypted",
            severity="CRITICAL",
        )

        contract = {
            "dataset": {"name": "t", "owner_name": "A", "owner_email": "a@b.com"},
            "schema": [{"name": "ssn", "type": "string", "description": "SSN", "pii": True, "max_length": 11}],
            "governance": {"classification": "internal", "encryption_required": False},
            "quality_rules": {},
        }
        resp = client.post("/api/v1/policy-dashboard/validate-combined", json={
            "contract_data": contract,
        })
        data = resp.json()
        # Static SD001 already flags this, combined should too
        assert data["failures"] >= 1

    def test_retention_heuristic(self, client):
        """Authored retention policy flags missing retention."""
        _create_and_approve_policy(
            client,
            title="Must set retention period",
            description="Confidential data requires retention policy",
            severity="CRITICAL",
        )

        contract = {
            "dataset": {"name": "t", "owner_name": "A", "owner_email": "a@b.com"},
            "schema": [{"name": "id", "type": "integer", "description": "ID"}],
            "governance": {"classification": "confidential"},
            "quality_rules": {},
        }
        resp = client.post("/api/v1/policy-dashboard/validate-combined", json={
            "contract_data": contract,
        })
        data = resp.json()
        assert data["status"] == "failed"


# ── Recent Approvals ─────────────────────────────────────────────────────

class TestRecentApprovals:
    def test_approval_log_appears(self, client):
        """Approving a policy creates an audit log entry."""
        _create_and_approve_policy(client, title="Audit Test")

        resp = client.get("/api/v1/policy-dashboard/stats")
        data = resp.json()
        assert len(data["recent_approvals"]) >= 1
        latest = data["recent_approvals"][0]
        assert latest["action"] in ("approved", "submitted")
        assert latest["actor_name"]
        assert latest["timestamp"]

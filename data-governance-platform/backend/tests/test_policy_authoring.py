"""
Tests for the policy authoring API (Stage 1).

Covers the full CRUD + approval workflow:
  - Create policy draft
  - List / filter / get policies
  - Update a draft
  - Submit for approval (with remediation guard)
  - Approve and verify version snapshot
  - Reject with mandatory comment
  - Edge-case guards (status transitions, missing fields)
"""

import pytest
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────

def _create_policy(client: TestClient, **overrides):
    """Helper to create a policy draft and return its JSON."""
    payload = {
        "title": "PII fields must be encrypted",
        "description": "All fields flagged as PII must use AES-256 encryption at rest and TLS in transit.",
        "policy_category": "security",
        "affected_domains": ["finance", "marketing"],
        "severity": "CRITICAL",
        "scanner_hint": "auto",
        "remediation_guide": "Step 1: identify PII columns. Step 2: apply encryption.",
        "authored_by": "Alice Tester",
    }
    payload.update(overrides)
    resp = client.post("/api/v1/policies/authored/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


# ── CREATE ───────────────────────────────────────────────────────────────

class TestCreatePolicy:
    def test_create_minimal(self, client):
        resp = client.post("/api/v1/policies/authored/", json={
            "title": "Test policy",
            "description": "All datasets must have an owner.",
            "policy_category": "compliance",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "Test policy"
        assert data["status"] == "draft"
        assert data["version"] == 1
        assert data["severity"] == "WARNING"  # default
        assert data["scanner_hint"] == "auto"  # default
        assert data["authored_by"] == "Data Governance Expert"  # default
        assert data["policy_uid"]  # UUID generated

    def test_create_full(self, client):
        data = _create_policy(client)
        assert data["title"] == "PII fields must be encrypted"
        assert data["severity"] == "CRITICAL"
        assert data["policy_category"] == "security"
        assert "finance" in data["affected_domains"]

    def test_create_invalid_category(self, client):
        resp = client.post("/api/v1/policies/authored/", json={
            "title": "Bad",
            "description": "x",
            "policy_category": "invalid_cat",
        })
        assert resp.status_code == 422

    def test_create_missing_title(self, client):
        resp = client.post("/api/v1/policies/authored/", json={
            "description": "x",
            "policy_category": "security",
        })
        assert resp.status_code == 422


# ── LIST / GET ───────────────────────────────────────────────────────────

class TestListAndGet:
    def test_list_empty(self, client):
        resp = client.get("/api/v1/policies/authored/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["policies"] == []
        assert data["total"] == 0

    def test_list_with_policies(self, client):
        _create_policy(client, title="A")
        _create_policy(client, title="B")
        resp = client.get("/api/v1/policies/authored/")
        data = resp.json()
        assert data["total"] == 2

    def test_filter_by_status(self, client):
        _create_policy(client, title="Draft One")
        resp = client.get("/api/v1/policies/authored/", params={"status": "approved"})
        assert resp.json()["total"] == 0
        resp = client.get("/api/v1/policies/authored/", params={"status": "draft"})
        assert resp.json()["total"] == 1

    def test_filter_by_category(self, client):
        _create_policy(client, title="Sec", policy_category="security")
        _create_policy(client, title="Priv", policy_category="privacy")
        resp = client.get("/api/v1/policies/authored/", params={"category": "privacy"})
        assert resp.json()["total"] == 1
        assert resp.json()["policies"][0]["title"] == "Priv"

    def test_get_detail(self, client):
        p = _create_policy(client)
        resp = client.get(f"/api/v1/policies/authored/{p['id']}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == p["title"]
        assert "versions" in data
        assert "artifacts" in data
        assert "approval_logs" in data

    def test_get_not_found(self, client):
        resp = client.get("/api/v1/policies/authored/99999")
        assert resp.status_code == 404


# ── UPDATE ───────────────────────────────────────────────────────────────

class TestUpdatePolicy:
    def test_update_draft(self, client):
        p = _create_policy(client)
        resp = client.patch(f"/api/v1/policies/authored/{p['id']}", json={
            "title": "Updated Title",
            "severity": "INFO",
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title"
        assert resp.json()["severity"] == "INFO"

    def test_update_non_draft_fails(self, client):
        p = _create_policy(client)
        # submit first
        client.post(f"/api/v1/policies/authored/{p['id']}/submit")
        resp = client.patch(f"/api/v1/policies/authored/{p['id']}", json={
            "title": "Nope",
        })
        assert resp.status_code == 400
        assert "draft" in resp.json()["detail"].lower()


# ── SUBMIT ───────────────────────────────────────────────────────────────

class TestSubmitPolicy:
    def test_submit_success(self, client):
        p = _create_policy(client)
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/submit")
        assert resp.status_code == 200
        assert resp.json()["status"] == "pending_approval"

    def test_submit_without_remediation(self, client):
        p = _create_policy(client, remediation_guide="")
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/submit")
        assert resp.status_code == 422
        assert "remediation" in resp.json()["detail"].lower()

    def test_submit_already_submitted(self, client):
        p = _create_policy(client)
        client.post(f"/api/v1/policies/authored/{p['id']}/submit")
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/submit")
        assert resp.status_code == 400


# ── APPROVE ──────────────────────────────────────────────────────────────

class TestApprovePolicy:
    def test_approve_success(self, client):
        p = _create_policy(client)
        client.post(f"/api/v1/policies/authored/{p['id']}/submit")
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/approve", json={
            "approver_name": "Bob Approver",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"

        # Verify version snapshot was created
        detail = client.get(f"/api/v1/policies/authored/{p['id']}").json()
        assert len(detail["versions"]) == 1
        assert detail["versions"][0]["status"] == "approved"
        assert detail["versions"][0]["approved_by"] == "Bob Approver"

        # Verify audit log
        assert len(detail["approval_logs"]) >= 2  # submitted + approved

    def test_approve_draft_fails(self, client):
        p = _create_policy(client)
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/approve", json={
            "approver_name": "Bob",
        })
        assert resp.status_code == 400

    def test_approve_default_approver(self, client):
        p = _create_policy(client)
        client.post(f"/api/v1/policies/authored/{p['id']}/submit")
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/approve", json={})
        assert resp.status_code == 200


# ── REJECT ───────────────────────────────────────────────────────────────

class TestRejectPolicy:
    def test_reject_success(self, client):
        p = _create_policy(client)
        client.post(f"/api/v1/policies/authored/{p['id']}/submit")
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/reject", json={
            "approver_name": "Carol Reviewer",
            "comment": "Needs more detail on encryption standards used.",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"

        detail = client.get(f"/api/v1/policies/authored/{p['id']}").json()
        assert any(log["action"] == "rejected" for log in detail["approval_logs"])
        assert any("encryption" in (log.get("comment") or "") for log in detail["approval_logs"])

    def test_reject_short_comment_fails(self, client):
        p = _create_policy(client)
        client.post(f"/api/v1/policies/authored/{p['id']}/submit")
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/reject", json={
            "approver_name": "Carol",
            "comment": "too short",  # < 10 chars
        })
        assert resp.status_code == 422

    def test_reject_missing_comment_fails(self, client):
        p = _create_policy(client)
        client.post(f"/api/v1/policies/authored/{p['id']}/submit")
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/reject", json={
            "approver_name": "Carol",
        })
        assert resp.status_code == 422

    def test_reject_draft_fails(self, client):
        p = _create_policy(client)
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/reject", json={
            "approver_name": "Carol",
            "comment": "This is a long enough rejection comment.",
        })
        assert resp.status_code == 400


# ── YAML ARTIFACT ────────────────────────────────────────────────────────

class TestYamlArtifact:
    def test_no_yaml_before_approval(self, client):
        p = _create_policy(client)
        resp = client.get(f"/api/v1/policies/authored/{p['id']}/yaml")
        assert resp.status_code == 404


# ── DOMAIN FILTER ────────────────────────────────────────────────────────

class TestDomainFilter:
    def test_domain_policies_empty(self, client):
        resp = client.get("/api/v1/policies/authored/domains/finance/policies")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

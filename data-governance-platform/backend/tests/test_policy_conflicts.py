"""
Tests for Stage 8 – Policy Exception Management.

Covers:
  - Failure detection (scanning approved policies for enforcement failures)
  - Exception request lifecycle (create, list, get)
  - Board approval / rejection workflow
  - Deployment gate (domain allowed/blocked)
  - Statistics
  - Store reset
"""

import pytest
from app.api.policy_conflicts import _reset_stores, _failure_store, _exception_store


# ── helpers ──────────────────────────────────────────────────────────────

def _create_policy(client, **overrides):
    payload = {
        "title": "Exception Test Policy",
        "description": "A test policy for exception management.",
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


def _seed_failure(failure_id="FAIL-1-finance", domain="finance", policy_id=1, policy_title="Test Policy"):
    """Manually seed a failure into the store for unit testing the exception workflow."""
    _failure_store[failure_id] = {
        "failure_id": failure_id,
        "policy_id": policy_id,
        "policy_title": policy_title,
        "policy_category": "security",
        "severity": "CRITICAL",
        "domain": domain,
        "failing_contracts": [],
        "total_failing": 0,
        "detected_at": "2024-01-01T00:00:00",
    }


@pytest.fixture(autouse=True)
def clean_stores():
    """Reset in-memory stores before each test."""
    _reset_stores()
    yield
    _reset_stores()


# ── Failure Detection ───────────────────────────────────────────────────

class TestFailureDetection:
    def test_detect_no_policies(self, client):
        """No approved policies → no failures."""
        resp = client.post("/api/v1/policy-exceptions/detect-failures")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_failures"] == 0
        assert data["failures"] == []

    def test_detect_with_approved_policy_no_contracts(self, client):
        """Approved policy but no contracts → no failures."""
        p = _create_policy(client, title="No Contracts Policy")
        _approve(client, p["id"])

        resp = client.post("/api/v1/policy-exceptions/detect-failures")
        data = resp.json()
        assert data["policies_scanned"] >= 1
        # No contracts exist so no failures
        assert data["total_failures"] == 0

    def test_detect_domain_scoping(self, client):
        """Domain filter limits which policies are scanned."""
        p1 = _create_policy(client, title="HR Policy", affected_domains=["hr"])
        _approve(client, p1["id"])
        p2 = _create_policy(client, title="Finance Policy", affected_domains=["finance"])
        _approve(client, p2["id"])

        resp = client.post("/api/v1/policy-exceptions/detect-failures?domain=hr")
        data = resp.json()
        # Only 1 policy scanned (hr)
        assert data["policies_scanned"] == 1


class TestFailureListing:
    def test_list_failures_empty(self, client):
        resp = client.get("/api/v1/policy-exceptions/failures")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    def test_list_failures_with_data(self, client):
        _seed_failure("FAIL-10-finance", "finance", 10, "Finance Encryption")
        _seed_failure("FAIL-11-hr", "hr", 11, "HR Privacy")

        resp = client.get("/api/v1/policy-exceptions/failures")
        data = resp.json()
        assert data["total"] == 2

    def test_list_failures_domain_filter(self, client):
        _seed_failure("FAIL-10-finance", "finance", 10, "Finance Encryption")
        _seed_failure("FAIL-11-hr", "hr", 11, "HR Privacy")

        resp = client.get("/api/v1/policy-exceptions/failures?domain=finance")
        data = resp.json()
        assert data["total"] == 1
        assert data["failures"][0]["domain"] == "finance"

    def test_failures_annotated_with_exception_status(self, client):
        _seed_failure("FAIL-10-finance", "finance", 10, "Finance Encryption")

        # Create an exception
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-10-finance",
            "domain": "finance",
            "policy_id": 10,
            "policy_title": "Finance Encryption",
            "justification": "Business need",
            "business_impact": "Revenue loss",
        })

        resp = client.get("/api/v1/policy-exceptions/failures")
        f = resp.json()["failures"][0]
        assert f["exception_status"] == "pending_review"
        assert f["exception_id"] is not None


# ── Exception Requests ──────────────────────────────────────────────────

class TestExceptionRequests:
    def test_create_exception(self, client):
        """Create an exception request for a known failure."""
        _seed_failure()

        resp = client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance",
            "domain": "finance",
            "policy_id": 1,
            "policy_title": "Test Policy",
            "justification": "Critical business deadline",
            "business_impact": "Revenue impact of $1M/day",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert data["status"] == "pending_review"
        assert data["justification"] == "Critical business deadline"

    def test_create_exception_unknown_failure(self, client):
        """Exception for non-existent failure → 404."""
        resp = client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-999-unknown",
            "domain": "unknown",
            "policy_id": 999,
            "policy_title": "Unknown",
            "justification": "Test",
            "business_impact": "Test",
        })
        assert resp.status_code == 404

    def test_create_exception_duplicate(self, client):
        """Cannot create two pending exceptions for the same failure → 409."""
        _seed_failure()

        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance",
            "domain": "finance",
            "policy_id": 1,
            "policy_title": "Test Policy",
            "justification": "First request",
            "business_impact": "Impact",
        })
        resp = client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance",
            "domain": "finance",
            "policy_id": 1,
            "policy_title": "Test Policy",
            "justification": "Second request",
            "business_impact": "Impact",
        })
        assert resp.status_code == 409

    def test_list_requests(self, client):
        _seed_failure("FAIL-1-finance")
        _seed_failure("FAIL-2-hr", "hr", 2, "HR Policy")

        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Test Policy",
            "justification": "J1", "business_impact": "B1",
        })
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-2-hr", "domain": "hr",
            "policy_id": 2, "policy_title": "HR Policy",
            "justification": "J2", "business_impact": "B2",
        })

        resp = client.get("/api/v1/policy-exceptions/requests")
        data = resp.json()
        assert data["total"] == 2
        assert data["pending"] == 2

    def test_list_requests_filter_by_status(self, client):
        _seed_failure()
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Test",
            "justification": "J", "business_impact": "B",
        })
        # Approve it
        client.post("/api/v1/policy-exceptions/requests/1/approve", json={
            "decided_by": "Board", "comments": "OK",
        })

        pending = client.get("/api/v1/policy-exceptions/requests?status=pending_review").json()
        assert pending["total"] == 0

        approved = client.get("/api/v1/policy-exceptions/requests?status=approved").json()
        assert approved["total"] == 1

    def test_list_requests_filter_by_domain(self, client):
        _seed_failure("FAIL-1-finance")
        _seed_failure("FAIL-2-hr", "hr", 2, "HR Policy")

        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Fin",
            "justification": "J1", "business_impact": "B1",
        })
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-2-hr", "domain": "hr",
            "policy_id": 2, "policy_title": "HR",
            "justification": "J2", "business_impact": "B2",
        })

        resp = client.get("/api/v1/policy-exceptions/requests?domain=finance")
        assert resp.json()["total"] == 1

    def test_get_request(self, client):
        _seed_failure()
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Test",
            "justification": "Justification", "business_impact": "Impact",
        })

        resp = client.get("/api/v1/policy-exceptions/requests/1")
        assert resp.status_code == 200
        assert resp.json()["justification"] == "Justification"

    def test_get_request_not_found(self, client):
        resp = client.get("/api/v1/policy-exceptions/requests/999")
        assert resp.status_code == 404


# ── Board Approval / Rejection ──────────────────────────────────────────

class TestBoardDecisions:
    def _create_pending_exception(self, client):
        _seed_failure()
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Test",
            "justification": "Need to deploy", "business_impact": "Lost revenue",
        })

    def test_approve(self, client):
        self._create_pending_exception(client)

        resp = client.post("/api/v1/policy-exceptions/requests/1/approve", json={
            "decided_by": "Governance Board",
            "comments": "Approved with conditions",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "approved"
        assert data["decision"]["decided_by"] == "Governance Board"
        assert data["decision"]["action"] == "approved"

    def test_reject(self, client):
        self._create_pending_exception(client)

        resp = client.post("/api/v1/policy-exceptions/requests/1/reject", json={
            "decided_by": "Governance Board",
            "comments": "Risk too high – fix the violation first",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "rejected"
        assert data["decision"]["action"] == "rejected"

    def test_approve_already_approved(self, client):
        self._create_pending_exception(client)
        client.post("/api/v1/policy-exceptions/requests/1/approve", json={
            "decided_by": "Board", "comments": "OK",
        })

        resp = client.post("/api/v1/policy-exceptions/requests/1/approve", json={
            "decided_by": "Board", "comments": "Again",
        })
        assert resp.status_code == 409

    def test_reject_already_rejected(self, client):
        self._create_pending_exception(client)
        client.post("/api/v1/policy-exceptions/requests/1/reject", json={
            "decided_by": "Board", "comments": "No",
        })

        resp = client.post("/api/v1/policy-exceptions/requests/1/reject", json={
            "decided_by": "Board", "comments": "Again",
        })
        assert resp.status_code == 409

    def test_approve_not_found(self, client):
        resp = client.post("/api/v1/policy-exceptions/requests/999/approve", json={
            "decided_by": "Board", "comments": "OK",
        })
        assert resp.status_code == 404

    def test_reject_not_found(self, client):
        resp = client.post("/api/v1/policy-exceptions/requests/999/reject", json={
            "decided_by": "Board", "comments": "No",
        })
        assert resp.status_code == 404

    def test_re_raise_after_rejection(self, client):
        """After rejection, a new exception can be raised for the same failure."""
        _seed_failure()
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Test",
            "justification": "First try", "business_impact": "Impact",
        })
        client.post("/api/v1/policy-exceptions/requests/1/reject", json={
            "decided_by": "Board", "comments": "No",
        })

        # Re-raise should succeed since the previous one was rejected
        resp = client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Test",
            "justification": "Second try with more context", "business_impact": "Updated impact",
        })
        assert resp.status_code == 200
        assert resp.json()["id"] == 2


# ── Deployment Gate ─────────────────────────────────────────────────────

class TestDeploymentGate:
    def test_gate_no_failures(self, client):
        """No failures → deploy allowed."""
        resp = client.get("/api/v1/policy-exceptions/deployment-gate/finance")
        assert resp.status_code == 200
        data = resp.json()
        assert data["allowed"] is True
        assert data["total_failures"] == 0
        assert data["blockers"] == []

    def test_gate_failure_no_exception(self, client):
        """Failure with no exception → blocked."""
        _seed_failure()

        resp = client.get("/api/v1/policy-exceptions/deployment-gate/finance")
        data = resp.json()
        assert data["allowed"] is False
        assert data["unresolved"] == 1
        assert len(data["blockers"]) == 1
        assert "No exception raised" in data["blockers"][0]["reason"]

    def test_gate_failure_pending_exception(self, client):
        """Failure with pending exception → blocked."""
        _seed_failure()
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Test",
            "justification": "J", "business_impact": "B",
        })

        resp = client.get("/api/v1/policy-exceptions/deployment-gate/finance")
        data = resp.json()
        assert data["allowed"] is False
        assert data["pending_exceptions"] == 1
        assert "pending board review" in data["blockers"][0]["reason"]

    def test_gate_failure_approved_exception(self, client):
        """Failure with approved exception → allowed."""
        _seed_failure()
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Test",
            "justification": "J", "business_impact": "B",
        })
        client.post("/api/v1/policy-exceptions/requests/1/approve", json={
            "decided_by": "Board", "comments": "Approved",
        })

        resp = client.get("/api/v1/policy-exceptions/deployment-gate/finance")
        data = resp.json()
        assert data["allowed"] is True
        assert data["approved_exceptions"] == 1
        assert data["blockers"] == []

    def test_gate_failure_rejected_exception(self, client):
        """Failure with rejected exception → blocked."""
        _seed_failure()
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Test",
            "justification": "J", "business_impact": "B",
        })
        client.post("/api/v1/policy-exceptions/requests/1/reject", json={
            "decided_by": "Board", "comments": "No",
        })

        resp = client.get("/api/v1/policy-exceptions/deployment-gate/finance")
        data = resp.json()
        assert data["allowed"] is False
        assert data["rejected_exceptions"] == 1
        assert "rejected" in data["blockers"][0]["reason"].lower()

    def test_gate_mixed_failures(self, client):
        """Multiple failures: some approved, some not → blocked."""
        _seed_failure("FAIL-1-finance", "finance", 1, "Policy A")
        _seed_failure("FAIL-2-finance", "finance", 2, "Policy B")

        # Approve only the first
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Policy A",
            "justification": "J", "business_impact": "B",
        })
        client.post("/api/v1/policy-exceptions/requests/1/approve", json={
            "decided_by": "Board", "comments": "OK",
        })

        resp = client.get("/api/v1/policy-exceptions/deployment-gate/finance")
        data = resp.json()
        assert data["allowed"] is False
        assert data["approved_exceptions"] == 1
        assert data["unresolved"] == 1

    def test_gate_all_approved(self, client):
        """All failures have approved exceptions → allowed."""
        _seed_failure("FAIL-1-finance", "finance", 1, "Policy A")
        _seed_failure("FAIL-2-finance", "finance", 2, "Policy B")

        for fid, pid, title in [("FAIL-1-finance", 1, "Policy A"), ("FAIL-2-finance", 2, "Policy B")]:
            client.post("/api/v1/policy-exceptions/", json={
                "failure_id": fid, "domain": "finance",
                "policy_id": pid, "policy_title": title,
                "justification": "J", "business_impact": "B",
            })

        # Approve both
        client.post("/api/v1/policy-exceptions/requests/1/approve", json={"decided_by": "Board", "comments": "OK"})
        client.post("/api/v1/policy-exceptions/requests/2/approve", json={"decided_by": "Board", "comments": "OK"})

        resp = client.get("/api/v1/policy-exceptions/deployment-gate/finance")
        data = resp.json()
        assert data["allowed"] is True
        assert data["approved_exceptions"] == 2

    def test_gate_different_domains_independent(self, client):
        """Failure in finance doesn't block hr."""
        _seed_failure("FAIL-1-finance", "finance", 1, "Finance Policy")

        resp_hr = client.get("/api/v1/policy-exceptions/deployment-gate/hr")
        assert resp_hr.json()["allowed"] is True

        resp_fin = client.get("/api/v1/policy-exceptions/deployment-gate/finance")
        assert resp_fin.json()["allowed"] is False


# ── Statistics ──────────────────────────────────────────────────────────

class TestExceptionStats:
    def test_stats_empty(self, client):
        resp = client.get("/api/v1/policy-exceptions/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_failures"] == 0
        assert data["total_exceptions"] == 0
        assert data["approval_rate_pct"] == 0

    def test_stats_with_data(self, client):
        _seed_failure("FAIL-1-finance", "finance", 1, "Fin Policy")
        _seed_failure("FAIL-2-hr", "hr", 2, "HR Policy")

        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Fin Policy",
            "justification": "J", "business_impact": "B",
        })
        client.post("/api/v1/policy-exceptions/requests/1/approve", json={
            "decided_by": "Board", "comments": "OK",
        })

        resp = client.get("/api/v1/policy-exceptions/stats")
        data = resp.json()
        assert data["total_failures"] == 2
        assert data["total_exceptions"] == 1
        assert data["approved"] == 1
        assert data["approval_rate_pct"] == 100.0
        assert "finance" in data["failures_by_domain"]
        assert "hr" in data["failures_by_domain"]
        assert "finance" in data["domains_deployable"]
        assert "hr" in data["domains_blocked"]


# ── Reset ───────────────────────────────────────────────────────────────

class TestStoreReset:
    def test_reset(self, client):
        _seed_failure()
        client.post("/api/v1/policy-exceptions/", json={
            "failure_id": "FAIL-1-finance", "domain": "finance",
            "policy_id": 1, "policy_title": "Test",
            "justification": "J", "business_impact": "B",
        })

        resp = client.post("/api/v1/policy-exceptions/reset")
        assert resp.status_code == 200

        assert client.get("/api/v1/policy-exceptions/failures").json()["total"] == 0
        assert client.get("/api/v1/policy-exceptions/requests").json()["total"] == 0

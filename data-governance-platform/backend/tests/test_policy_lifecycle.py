"""
Tests for Stage 4 – Policy Versioning & Lifecycle Management.

Covers:
  - Version history endpoint
  - Version diff endpoint
  - Revise (re-draft) workflow
  - Deprecate workflow
  - Timeline endpoint
  - Multi-version lifecycle (approve → revise → approve again)
"""

import pytest
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────

def _create_policy(client: TestClient, **overrides):
    payload = {
        "title": "Encryption Required",
        "description": "All PII fields must be encrypted at rest.",
        "policy_category": "security",
        "affected_domains": ["finance"],
        "severity": "CRITICAL",
        "scanner_hint": "rule_based",
        "remediation_guide": "Enable encryption_required in governance metadata.",
        "authored_by": "Author A",
    }
    payload.update(overrides)
    resp = client.post("/api/v1/policies/authored/", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _submit(client, pid):
    resp = client.post(f"/api/v1/policies/authored/{pid}/submit")
    assert resp.status_code == 200, resp.text
    return resp.json()


def _approve(client, pid, approver="Approver A"):
    resp = client.post(f"/api/v1/policies/authored/{pid}/approve", json={
        "approver_name": approver,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def _reject(client, pid, approver="Approver A", comment="Needs more detail on implementation steps"):
    resp = client.post(f"/api/v1/policies/authored/{pid}/reject", json={
        "approver_name": approver,
        "comment": comment,
    })
    assert resp.status_code == 200, resp.text
    return resp.json()


def _approve_full(client, **overrides):
    """Create, submit, and approve a policy."""
    p = _create_policy(client, **overrides)
    _submit(client, p["id"])
    return _approve(client, p["id"])


# ── Version History ──────────────────────────────────────────────────────

class TestVersionHistory:
    def test_no_versions_for_draft(self, client):
        """A fresh draft has no version snapshots yet."""
        p = _create_policy(client)
        resp = client.get(f"/api/v1/policies/authored/{p['id']}/versions")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_versions"] == 0
        assert data["current_version"] == 1
        assert data["current_status"] == "draft"

    def test_one_version_after_approval(self, client):
        """Approving creates one version snapshot."""
        p = _approve_full(client)
        resp = client.get(f"/api/v1/policies/authored/{p['id']}/versions")
        data = resp.json()
        assert data["total_versions"] == 1
        v = data["versions"][0]
        assert v["version"] == 1
        assert v["status"] == "approved"
        assert v["has_artifact"] is True
        assert v["approved_by"] == "Approver A"

    def test_rejected_version_snapshot(self, client):
        """Rejecting also creates a version snapshot."""
        p = _create_policy(client)
        _submit(client, p["id"])
        _reject(client, p["id"])

        resp = client.get(f"/api/v1/policies/authored/{p['id']}/versions")
        data = resp.json()
        assert data["total_versions"] == 1
        assert data["versions"][0]["status"] == "rejected"
        assert data["versions"][0]["has_artifact"] is False

    def test_not_found(self, client):
        resp = client.get("/api/v1/policies/authored/9999/versions")
        assert resp.status_code == 404


# ── Version Diff ─────────────────────────────────────────────────────────

class TestVersionDiff:
    def test_diff_first_version(self, client):
        """Diff for v1 compares against empty baseline."""
        p = _approve_full(client)
        resp = client.get(f"/api/v1/policies/authored/{p['id']}/versions/1/diff")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == 1
        assert data["compared_to"] is None
        # First version has changes (everything is new)
        assert len(data["changes"]) > 0
        fields_changed = [c["field"] for c in data["changes"]]
        assert "title" in fields_changed
        assert "status" in fields_changed

    def test_diff_second_version(self, client):
        """Diff for v2 compares against v1."""
        p = _approve_full(client, title="Original Title")
        pid = p["id"]

        # Revise
        client.post(f"/api/v1/policies/authored/{pid}/revise")

        # Update the title
        client.patch(f"/api/v1/policies/authored/{pid}", json={"title": "Updated Title"})

        # Submit and approve v2
        _submit(client, pid)
        _approve(client, pid, approver="Approver B")

        resp = client.get(f"/api/v1/policies/authored/{pid}/versions/2/diff")
        data = resp.json()
        assert data["version"] == 2
        assert data["compared_to"] == 1
        fields_changed = [c["field"] for c in data["changes"]]
        assert "title" in fields_changed
        title_change = next(c for c in data["changes"] if c["field"] == "title")
        assert title_change["old_value"] == "Original Title"
        assert title_change["new_value"] == "Updated Title"

    def test_diff_includes_yaml(self, client):
        """Diff includes YAML artifacts when available."""
        p = _approve_full(client)
        resp = client.get(f"/api/v1/policies/authored/{p['id']}/versions/1/diff")
        data = resp.json()
        assert data["yaml_diff"] is not None
        assert data["yaml_diff"]["current_yaml"] is not None
        assert data["yaml_diff"]["previous_yaml"] is None  # No previous for v1

    def test_diff_version_not_found(self, client):
        p = _approve_full(client)
        resp = client.get(f"/api/v1/policies/authored/{p['id']}/versions/99/diff")
        assert resp.status_code == 404


# ── Revise (Re-draft) ───────────────────────────────────────────────────

class TestRevise:
    def test_revise_approved(self, client):
        """Revising an approved policy creates a new draft at version+1."""
        p = _approve_full(client)
        assert p["version"] == 1
        assert p["status"] == "approved"

        resp = client.post(f"/api/v1/policies/authored/{p['id']}/revise")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "draft"
        assert data["version"] == 2

    def test_revise_rejected(self, client):
        """Can also revise a rejected policy."""
        p = _create_policy(client)
        _submit(client, p["id"])
        _reject(client, p["id"])

        resp = client.post(f"/api/v1/policies/authored/{p['id']}/revise")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "draft"
        assert data["version"] == 2

    def test_revise_draft_fails(self, client):
        """Cannot revise a draft — it's already editable."""
        p = _create_policy(client)
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/revise")
        assert resp.status_code == 400

    def test_revise_pending_fails(self, client):
        """Cannot revise while pending approval."""
        p = _create_policy(client)
        _submit(client, p["id"])
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/revise")
        assert resp.status_code == 400

    def test_revised_policy_editable(self, client):
        """After revision, the draft can be edited again."""
        p = _approve_full(client)
        client.post(f"/api/v1/policies/authored/{p['id']}/revise")

        resp = client.patch(f"/api/v1/policies/authored/{p['id']}", json={
            "title": "Revised Title",
        })
        assert resp.status_code == 200
        assert resp.json()["title"] == "Revised Title"


# ── Deprecate ────────────────────────────────────────────────────────────

class TestDeprecate:
    def test_deprecate_approved(self, client):
        """Deprecating an approved policy sets status to deprecated."""
        p = _approve_full(client)
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/deprecate", json={
            "approver_name": "Admin",
        })
        assert resp.status_code == 200
        assert resp.json()["status"] == "deprecated"

    def test_deprecate_draft_fails(self, client):
        """Cannot deprecate a draft."""
        p = _create_policy(client)
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/deprecate", json={
            "approver_name": "Admin",
        })
        assert resp.status_code == 400

    def test_deprecate_rejected_fails(self, client):
        """Cannot deprecate a rejected policy."""
        p = _create_policy(client)
        _submit(client, p["id"])
        _reject(client, p["id"])
        resp = client.post(f"/api/v1/policies/authored/{p['id']}/deprecate", json={
            "approver_name": "Admin",
        })
        assert resp.status_code == 400

    def test_deprecated_not_active(self, client):
        """Deprecated policies don't show up in active-policies."""
        p = _approve_full(client, title="Soon Deprecated")
        client.post(f"/api/v1/policies/authored/{p['id']}/deprecate", json={
            "approver_name": "Admin",
        })

        resp = client.get("/api/v1/policy-dashboard/active-policies")
        titles = [pol["title"] for pol in resp.json()["policies"]]
        assert "Soon Deprecated" not in titles


# ── Timeline ─────────────────────────────────────────────────────────────

class TestTimeline:
    def test_timeline_draft_only(self, client):
        """Fresh draft has a 'created' event."""
        p = _create_policy(client)
        resp = client.get(f"/api/v1/policies/authored/{p['id']}/timeline")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_events"] == 1
        assert data["events"][0]["type"] == "created"
        assert data["events"][0]["actor"] == "Author A"

    def test_timeline_full_lifecycle(self, client):
        """Full lifecycle: create → submit → approve → revise → submit → approve → deprecate."""
        p = _create_policy(client)
        pid = p["id"]

        _submit(client, pid)
        _approve(client, pid)
        client.post(f"/api/v1/policies/authored/{pid}/revise")
        _submit(client, pid)
        _approve(client, pid, approver="Approver B")
        client.post(f"/api/v1/policies/authored/{pid}/deprecate", json={
            "approver_name": "Admin",
        })

        resp = client.get(f"/api/v1/policies/authored/{pid}/timeline")
        data = resp.json()

        event_types = [e["type"] for e in data["events"]]
        assert event_types[0] == "created"
        assert "submitted" in event_types
        assert "approved" in event_types
        assert "revised" in event_types
        assert "deprecated" in event_types
        assert data["current_status"] == "deprecated"

    def test_timeline_rejection_path(self, client):
        """Timeline includes rejection events."""
        p = _create_policy(client)
        pid = p["id"]
        _submit(client, pid)
        _reject(client, pid, comment="Missing compliance details in the policy")

        resp = client.get(f"/api/v1/policies/authored/{pid}/timeline")
        data = resp.json()
        event_types = [e["type"] for e in data["events"]]
        assert "rejected" in event_types

    def test_timeline_not_found(self, client):
        resp = client.get("/api/v1/policies/authored/9999/timeline")
        assert resp.status_code == 404


# ── Multi-version Lifecycle ──────────────────────────────────────────────

class TestMultiVersionLifecycle:
    def test_approve_revise_approve(self, client):
        """Full v1→v2 lifecycle with version history and artifacts."""
        p = _create_policy(client, title="V1 Title")
        pid = p["id"]

        # v1: submit → approve
        _submit(client, pid)
        _approve(client, pid)

        # Revise to v2
        client.post(f"/api/v1/policies/authored/{pid}/revise")
        client.patch(f"/api/v1/policies/authored/{pid}", json={
            "title": "V2 Title", "severity": "WARNING",
        })
        _submit(client, pid)
        _approve(client, pid, approver="Approver B")

        # Check version history
        resp = client.get(f"/api/v1/policies/authored/{pid}/versions")
        data = resp.json()
        assert data["total_versions"] == 2
        assert data["current_version"] == 2

        # Both versions have artifacts
        for v in data["versions"]:
            assert v["has_artifact"] is True

        # Check v2 diff
        resp = client.get(f"/api/v1/policies/authored/{pid}/versions/2/diff")
        diff = resp.json()
        assert diff["compared_to"] == 1
        fields_changed = [c["field"] for c in diff["changes"]]
        assert "title" in fields_changed
        assert "severity" in fields_changed

    def test_three_versions(self, client):
        """Three versions produce three snapshots."""
        p = _create_policy(client)
        pid = p["id"]

        # v1
        _submit(client, pid)
        _approve(client, pid)

        # v2
        client.post(f"/api/v1/policies/authored/{pid}/revise")
        _submit(client, pid)
        _approve(client, pid)

        # v3
        client.post(f"/api/v1/policies/authored/{pid}/revise")
        _submit(client, pid)
        _approve(client, pid)

        resp = client.get(f"/api/v1/policies/authored/{pid}/versions")
        data = resp.json()
        assert data["total_versions"] == 3
        assert data["current_version"] == 3

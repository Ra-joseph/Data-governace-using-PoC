"""
Tests for Stage 6 – Policy Export, Import & Sharing.

Covers:
  - Single policy export (JSON + YAML)
  - Bundle export with filters
  - Bundle import (create, dedupe, validation)
  - Template catalog (list, filter, get, instantiate)
"""

import json
import yaml
import pytest
from fastapi.testclient import TestClient


# ── helpers ──────────────────────────────────────────────────────────────

def _create_policy(client, **overrides):
    payload = {
        "title": "Export Test Policy",
        "description": "Test policy for export/import.",
        "policy_category": "security",
        "affected_domains": ["finance"],
        "severity": "CRITICAL",
        "scanner_hint": "rule_based",
        "remediation_guide": "Apply encryption to all PII fields.",
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


# ── Single Export ────────────────────────────────────────────────────────

class TestSingleExport:
    def test_export_json(self, client):
        """Export a policy as JSON."""
        p = _create_policy(client, title="Export JSON")
        resp = client.get(f"/api/v1/policy-exchange/export/{p['id']}?format=json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Export JSON"
        assert data["policy_uid"] == p["policy_uid"]
        assert data["policy_category"] == "security"

    def test_export_yaml(self, client):
        """Export a policy as YAML."""
        p = _create_policy(client, title="Export YAML")
        resp = client.get(f"/api/v1/policy-exchange/export/{p['id']}?format=yaml")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/yaml")
        parsed = yaml.safe_load(resp.text)
        assert parsed["title"] == "Export YAML"

    def test_export_with_artifact(self, client):
        """Approved policy export includes artifact data."""
        p = _create_policy(client, title="Export With Art")
        _approve(client, p["id"])

        resp = client.get(f"/api/v1/policy-exchange/export/{p['id']}?format=json")
        data = resp.json()
        assert "artifact" in data
        assert data["artifact"]["yaml_content"] is not None
        assert data["artifact"]["scanner_type"] in ("rule_based", "ai_semantic")

    def test_export_not_found(self, client):
        resp = client.get("/api/v1/policy-exchange/export/9999?format=json")
        assert resp.status_code == 404


# ── Bundle Export ────────────────────────────────────────────────────────

class TestBundleExport:
    def test_export_bundle_empty(self, client):
        """Export bundle with no matching policies."""
        resp = client.get("/api/v1/policy-exchange/export-bundle?format=json")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_policies"] == 0
        assert data["policies"] == []

    def test_export_bundle_all(self, client):
        """Export all policies."""
        _create_policy(client, title="Bundle A")
        _create_policy(client, title="Bundle B")

        resp = client.get("/api/v1/policy-exchange/export-bundle?format=json")
        data = resp.json()
        assert data["total_policies"] == 2
        assert data["bundle_format_version"] == "1.0"
        titles = [p["title"] for p in data["policies"]]
        assert "Bundle A" in titles
        assert "Bundle B" in titles

    def test_export_bundle_filter_status(self, client):
        """Filter bundle by status."""
        p = _create_policy(client, title="Approved Only")
        _approve(client, p["id"])
        _create_policy(client, title="Draft Only")

        resp = client.get("/api/v1/policy-exchange/export-bundle?format=json&status=approved")
        data = resp.json()
        titles = [p["title"] for p in data["policies"]]
        assert "Approved Only" in titles
        assert "Draft Only" not in titles

    def test_export_bundle_filter_category(self, client):
        """Filter bundle by category."""
        _create_policy(client, title="Security P", policy_category="security")
        _create_policy(client, title="Compliance P", policy_category="compliance")

        resp = client.get("/api/v1/policy-exchange/export-bundle?format=json&category=security")
        data = resp.json()
        assert data["total_policies"] == 1
        assert data["policies"][0]["title"] == "Security P"

    def test_export_bundle_yaml(self, client):
        """Export bundle as YAML."""
        _create_policy(client, title="YAML Bundle")
        resp = client.get("/api/v1/policy-exchange/export-bundle?format=yaml")
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/yaml")
        parsed = yaml.safe_load(resp.text)
        assert parsed["total_policies"] >= 1


# ── Import ───────────────────────────────────────────────────────────────

class TestImport:
    def test_import_single(self, client):
        """Import a single policy."""
        resp = client.post("/api/v1/policy-exchange/import", json={
            "bundle_name": "Test Import",
            "imported_by": "Admin",
            "policies": [{
                "title": "Imported Policy",
                "description": "This was imported.",
                "policy_category": "compliance",
                "severity": "WARNING",
            }],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["created"] == 1
        assert data["skipped"] == 0
        assert data["errors"] == 0
        assert data["created_policies"][0]["title"] == "Imported Policy"

    def test_import_multiple(self, client):
        """Import multiple policies at once."""
        resp = client.post("/api/v1/policy-exchange/import", json={
            "bundle_name": "Multi Import",
            "imported_by": "Admin",
            "policies": [
                {"title": "Import A", "description": "A", "policy_category": "security"},
                {"title": "Import B", "description": "B", "policy_category": "privacy"},
                {"title": "Import C", "description": "C", "policy_category": "data_quality"},
            ],
        })
        data = resp.json()
        assert data["created"] == 3

    def test_import_duplicate_skipped(self, client):
        """Duplicate titles are skipped."""
        _create_policy(client, title="Already Exists")

        resp = client.post("/api/v1/policy-exchange/import", json={
            "bundle_name": "Dupe Test",
            "imported_by": "Admin",
            "policies": [
                {"title": "Already Exists", "description": "x", "policy_category": "security"},
            ],
        })
        data = resp.json()
        assert data["created"] == 0
        assert data["skipped"] == 1
        assert data["skipped_policies"][0]["reason"] == "Policy with same title already exists"

    def test_import_invalid_category(self, client):
        """Invalid category produces an error entry."""
        resp = client.post("/api/v1/policy-exchange/import", json={
            "bundle_name": "Bad Cat",
            "imported_by": "Admin",
            "policies": [
                {"title": "Bad Category", "description": "x", "policy_category": "nonexistent"},
            ],
        })
        data = resp.json()
        assert data["errors"] == 1
        assert "Invalid category" in data["error_details"][0]["error"]

    def test_import_defaults(self, client):
        """Default values are applied for optional fields."""
        resp = client.post("/api/v1/policy-exchange/import", json={
            "bundle_name": "Defaults",
            "imported_by": "Admin",
            "policies": [
                {"title": "Minimal Import", "description": "Minimal", "policy_category": "sla"},
            ],
        })
        data = resp.json()
        assert data["created"] == 1
        # Verify the created policy has defaults
        pid = data["created_policies"][0]["id"]
        resp2 = client.get(f"/api/v1/policies/authored/{pid}")
        policy = resp2.json()
        assert policy["severity"] == "WARNING"
        assert policy["scanner_hint"] == "auto"
        assert policy["status"] == "draft"
        assert policy["version"] == 1

    def test_roundtrip_export_import(self, client):
        """Export then import produces equivalent policies."""
        p = _create_policy(client, title="Roundtrip Test")
        _approve(client, p["id"])

        # Export
        export_resp = client.get("/api/v1/policy-exchange/export-bundle?format=json&status=approved")
        bundle = export_resp.json()
        assert bundle["total_policies"] >= 1

        # Convert exported policies into import format
        import_policies = []
        for ep in bundle["policies"]:
            import_policies.append({
                "title": ep["title"] + " (imported)",
                "description": ep["description"],
                "policy_category": ep["policy_category"],
                "severity": ep["severity"],
                "scanner_hint": ep["scanner_hint"],
                "remediation_guide": ep.get("remediation_guide"),
                "affected_domains": ep.get("affected_domains", ["ALL"]),
            })

        # Import
        import_resp = client.post("/api/v1/policy-exchange/import", json={
            "bundle_name": "Roundtrip",
            "imported_by": "Admin",
            "policies": import_policies,
        })
        assert import_resp.json()["created"] == len(import_policies)


# ── Templates ────────────────────────────────────────────────────────────

class TestTemplates:
    def test_list_templates(self, client):
        """List all builtin templates."""
        resp = client.get("/api/v1/policy-exchange/templates")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 5
        for tmpl in data["templates"]:
            assert "id" in tmpl
            assert "name" in tmpl
            assert "category" in tmpl
            assert "tags" in tmpl
            assert "policy_data" in tmpl

    def test_filter_by_category(self, client):
        """Filter templates by category."""
        resp = client.get("/api/v1/policy-exchange/templates?category=security")
        data = resp.json()
        assert all(t["category"] == "security" for t in data["templates"])

    def test_filter_by_tag(self, client):
        """Filter templates by tag."""
        resp = client.get("/api/v1/policy-exchange/templates?tag=encryption")
        data = resp.json()
        assert data["total"] >= 1
        assert all("encryption" in t["tags"] for t in data["templates"])

    def test_get_template(self, client):
        """Get a specific template by ID."""
        resp = client.get("/api/v1/policy-exchange/templates/tmpl-pii-encryption")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "tmpl-pii-encryption"
        assert data["name"] == "PII Encryption Required"

    def test_get_template_not_found(self, client):
        resp = client.get("/api/v1/policy-exchange/templates/nonexistent")
        assert resp.status_code == 404

    def test_instantiate_template(self, client):
        """Instantiate a template creates a draft policy."""
        resp = client.post("/api/v1/policy-exchange/templates/tmpl-data-retention/instantiate?authored_by=Tester")
        assert resp.status_code == 200
        data = resp.json()
        assert data["template_id"] == "tmpl-data-retention"
        assert data["created_policy"]["status"] == "draft"
        assert data["created_policy"]["category"] == "compliance"

        # Verify the policy exists
        pid = data["created_policy"]["id"]
        resp2 = client.get(f"/api/v1/policies/authored/{pid}")
        assert resp2.status_code == 200
        assert resp2.json()["title"] == "Data retention policy required"

    def test_instantiate_duplicate_409(self, client):
        """Instantiating same template twice gives 409."""
        client.post("/api/v1/policy-exchange/templates/tmpl-owner-required/instantiate")
        resp = client.post("/api/v1/policy-exchange/templates/tmpl-owner-required/instantiate")
        assert resp.status_code == 409

    def test_instantiate_not_found(self, client):
        resp = client.post("/api/v1/policy-exchange/templates/fake-id/instantiate")
        assert resp.status_code == 404

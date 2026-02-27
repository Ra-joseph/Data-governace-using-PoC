"""
Tests for Stage 2: Policy conversion engine and artifact generation.

Covers:
  - convert_policy_to_yaml: YAML/JSON generation, scanner resolution, rule DSL
  - Approve workflow: artifact auto-generation after approval
  - Preview endpoint: YAML preview without commit
  - Git integration: graceful degradation when Git fails
"""

import json
import yaml
import pytest
from fastapi.testclient import TestClient


# ── Converter unit tests ─────────────────────────────────────────────────

from app.services.policy_converter import (
    convert_policy_to_yaml,
    _name_from_title,
    _build_rule_expression,
    _resolve_scanner,
    _generate_policy_id,
)


class TestConverterHelpers:
    def test_name_from_title(self):
        assert _name_from_title("PII fields must be encrypted") == "pii_fields_must_be_encrypted"
        assert _name_from_title("Data Quality — completeness!") == "data_quality_completeness"
        assert _name_from_title("") == ""

    def test_generate_policy_id_security(self):
        pid = _generate_policy_id("security", "abc123def456")
        assert pid.startswith("SD")
        assert len(pid) >= 4

    def test_generate_policy_id_data_quality(self):
        pid = _generate_policy_id("data_quality", "abc123def456")
        assert pid.startswith("DQ")

    def test_generate_policy_id_unknown_category(self):
        pid = _generate_policy_id("custom_stuff", "abc123def456")
        assert pid.startswith("POL")

    def test_resolve_scanner_auto_deterministic(self):
        assert _resolve_scanner("auto", True) == "rule_based"

    def test_resolve_scanner_auto_non_deterministic(self):
        assert _resolve_scanner("auto", False) == "ai_semantic"

    def test_resolve_scanner_explicit(self):
        assert _resolve_scanner("rule_based", False) == "rule_based"
        assert _resolve_scanner("ai_semantic", True) == "ai_semantic"

    def test_build_rule_pii_encryption(self):
        rule, is_det = _build_rule_expression(
            "All PII fields must be encrypted at rest using AES-256"
        )
        assert is_det is True
        assert len(rule) > 10

    def test_build_rule_retention(self):
        rule, is_det = _build_rule_expression(
            "Confidential data must have a retention policy of at least 7 years"
        )
        assert is_det is True

    def test_build_rule_semantic_fallback(self):
        rule, is_det = _build_rule_expression(
            "Ensure data aligns with departmental business glossary terms"
        )
        assert is_det is False
        assert "glossary" in rule.lower()


class TestConvertPolicyToYaml:
    def _sample_conversion(self, **overrides):
        defaults = dict(
            policy_uid="12345678-abcd-1234-abcd-123456789abc",
            title="PII fields must be encrypted",
            description="All fields flagged as PII must use AES-256 encryption at rest.",
            policy_category="security",
            affected_domains=["finance", "marketing"],
            severity="CRITICAL",
            scanner_hint="auto",
            remediation_guide="Step 1: Enable encryption.",
            effective_date=None,
            authored_by="Alice",
            version=1,
        )
        defaults.update(overrides)
        return convert_policy_to_yaml(**defaults)

    def test_returns_required_keys(self):
        result = self._sample_conversion()
        assert "yaml_content" in result
        assert "json_content" in result
        assert "scanner_type" in result
        assert "policy_id" in result

    def test_yaml_is_valid(self):
        result = self._sample_conversion()
        doc = yaml.safe_load(result["yaml_content"])
        assert "policies" in doc
        assert len(doc["policies"]) == 1
        assert doc["policies"][0]["severity"] == "critical"

    def test_json_is_valid(self):
        result = self._sample_conversion()
        doc = json.loads(result["json_content"])
        assert "policies" in doc
        assert doc["metadata"]["category"] == "security"
        assert doc["metadata"]["affected_domains"] == ["finance", "marketing"]

    def test_scanner_resolved_rule_based(self):
        result = self._sample_conversion(
            description="All PII fields must be encrypted at rest"
        )
        assert result["scanner_type"] == "rule_based"

    def test_scanner_resolved_ai_semantic(self):
        result = self._sample_conversion(
            description="Ensure data aligns with business glossary terms",
            scanner_hint="auto",
        )
        assert result["scanner_type"] == "ai_semantic"

    def test_explicit_scanner_override(self):
        result = self._sample_conversion(scanner_hint="ai_semantic")
        assert result["scanner_type"] == "ai_semantic"

    def test_semantic_has_prompt_template(self):
        result = self._sample_conversion(
            description="Ensure data aligns with business glossary terms",
            scanner_hint="auto",
        )
        doc = yaml.safe_load(result["yaml_content"])
        assert "prompt_template" in doc["policies"][0]

    def test_rule_based_no_prompt_template(self):
        result = self._sample_conversion(
            description="All PII fields must be encrypted at rest"
        )
        doc = yaml.safe_load(result["yaml_content"])
        assert "prompt_template" not in doc["policies"][0]

    def test_effective_date_in_metadata(self):
        from datetime import date
        result = self._sample_conversion(effective_date=date(2026, 3, 1))
        doc = yaml.safe_load(result["yaml_content"])
        assert doc["metadata"]["effective_date"] == "2026-03-01"

    def test_version_in_yaml(self):
        result = self._sample_conversion(version=3)
        doc = yaml.safe_load(result["yaml_content"])
        assert doc["version"] == "3.0.0"

    def test_remediation_in_policy(self):
        result = self._sample_conversion(remediation_guide="Fix it now.")
        doc = yaml.safe_load(result["yaml_content"])
        assert "Fix it now" in doc["policies"][0]["remediation"]


# ── API integration tests ────────────────────────────────────────────────

def _create_and_submit(client: TestClient):
    """Helper: create a policy, then submit it for approval."""
    resp = client.post("/api/v1/policies/authored/", json={
        "title": "PII must be encrypted",
        "description": "All fields flagged as PII must use AES-256 encryption at rest.",
        "policy_category": "security",
        "severity": "CRITICAL",
        "remediation_guide": "Step 1: Enable encryption. Step 2: Revalidate.",
        "authored_by": "Tester",
    })
    assert resp.status_code == 201
    pid = resp.json()["id"]
    client.post(f"/api/v1/policies/authored/{pid}/submit")
    return pid


class TestApproveGeneratesArtifact:
    def test_approve_creates_artifact(self, client):
        pid = _create_and_submit(client)
        resp = client.post(f"/api/v1/policies/authored/{pid}/approve", json={
            "approver_name": "Bob",
        })
        assert resp.status_code == 200

        # Fetch detail and check artifacts
        detail = client.get(f"/api/v1/policies/authored/{pid}").json()
        assert len(detail["artifacts"]) == 1
        art = detail["artifacts"][0]
        assert art["version"] == 1
        assert "yaml_content" in art and len(art["yaml_content"]) > 50
        assert "json_content" in art and len(art["json_content"]) > 50
        assert art["scanner_type"] in ("rule_based", "ai_semantic")

    def test_artifact_yaml_is_valid(self, client):
        pid = _create_and_submit(client)
        client.post(f"/api/v1/policies/authored/{pid}/approve", json={
            "approver_name": "Bob",
        })
        detail = client.get(f"/api/v1/policies/authored/{pid}").json()
        art = detail["artifacts"][0]
        doc = yaml.safe_load(art["yaml_content"])
        assert "policies" in doc
        assert doc["policies"][0]["severity"] == "critical"

    def test_artifact_json_is_valid(self, client):
        pid = _create_and_submit(client)
        client.post(f"/api/v1/policies/authored/{pid}/approve", json={
            "approver_name": "Bob",
        })
        detail = client.get(f"/api/v1/policies/authored/{pid}").json()
        art = detail["artifacts"][0]
        doc = json.loads(art["json_content"])
        assert doc["metadata"]["category"] == "security"

    def test_get_yaml_endpoint(self, client):
        pid = _create_and_submit(client)
        client.post(f"/api/v1/policies/authored/{pid}/approve", json={
            "approver_name": "Bob",
        })
        resp = client.get(f"/api/v1/policies/authored/{pid}/yaml")
        assert resp.status_code == 200
        data = resp.json()
        assert "yaml_content" in data
        assert data["scanner_type"] in ("rule_based", "ai_semantic")


class TestPreviewEndpoint:
    def test_preview_draft(self, client):
        resp = client.post("/api/v1/policies/authored/", json={
            "title": "Completeness must be 95%",
            "description": "All datasets must have completeness threshold >= 95",
            "policy_category": "data_quality",
            "remediation_guide": "Set completeness threshold to 95 or higher.",
        })
        pid = resp.json()["id"]

        preview = client.get(f"/api/v1/policies/authored/{pid}/preview-yaml")
        assert preview.status_code == 200
        data = preview.json()
        assert data["is_preview"] is True
        assert "yaml_content" in data
        assert "json_content" in data
        assert data["scanner_type"] in ("rule_based", "ai_semantic")
        assert data["policy_id_generated"]

    def test_preview_does_not_create_artifact(self, client):
        resp = client.post("/api/v1/policies/authored/", json={
            "title": "Test preview",
            "description": "Some description about data quality",
            "policy_category": "data_quality",
        })
        pid = resp.json()["id"]

        client.get(f"/api/v1/policies/authored/{pid}/preview-yaml")

        detail = client.get(f"/api/v1/policies/authored/{pid}").json()
        assert len(detail["artifacts"]) == 0

    def test_preview_valid_yaml(self, client):
        resp = client.post("/api/v1/policies/authored/", json={
            "title": "Freshness SLA required",
            "description": "All temporal datasets must have a freshness SLA",
            "policy_category": "sla",
            "remediation_guide": "Add freshness_sla to quality_rules section.",
        })
        pid = resp.json()["id"]

        preview = client.get(f"/api/v1/policies/authored/{pid}/preview-yaml")
        doc = yaml.safe_load(preview.json()["yaml_content"])
        assert "policies" in doc
        assert len(doc["policies"]) == 1

    def test_preview_not_found(self, client):
        resp = client.get("/api/v1/policies/authored/99999/preview-yaml")
        assert resp.status_code == 404

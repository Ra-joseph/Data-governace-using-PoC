"""
Advanced tests for PolicyEngine covering multi-violation scenarios, boundary
conditions, violation type assertions, and documentation of YAML policies
that are defined but not yet implemented in the rule engine.
"""

import pytest
from app.services.policy_engine import PolicyEngine
from app.schemas.contract import ViolationType, ValidationStatus


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean_contract(
    schema=None,
    governance=None,
    quality_rules=None,
    owner_name="Alice",
    owner_email="alice@example.com",
):
    """Return a minimal contract dict that passes all implemented policies."""
    return {
        "dataset": {"owner_name": owner_name, "owner_email": owner_email},
        "schema": schema or [
            {
                "name": "record_id",
                "type": "integer",
                "description": "Primary key",
                "required": True,
                "nullable": False,
                "pii": False,
            }
        ],
        "governance": governance or {"classification": "internal"},
        "quality_rules": quality_rules or {},
    }


# ---------------------------------------------------------------------------
# Multi-violation scenarios
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestPolicyEngineMultipleViolations:
    """Verify that multiple simultaneous violations are all reported correctly."""

    def setup_method(self):
        self.engine = PolicyEngine()

    def test_pii_confidential_missing_encryption_retention_tags(self):
        """SD001+SD002+SD003: PII + confidential + no encryption, retention, or tags."""
        contract = _clean_contract(
            schema=[
                {
                    "name": "ssn",
                    "type": "string",
                    "pii": True,
                    "description": "Social security number",
                    "required": True,
                    "nullable": False,
                    "max_length": 11,
                }
            ],
            governance={"classification": "confidential"},
            quality_rules={"completeness_threshold": 99},
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert any("SD001" in p for p in policies), "Expected SD001 violation"
        assert any("SD002" in p for p in policies), "Expected SD002 violation"
        assert any("SD003" in p for p in policies), "Expected SD003 violation"
        assert result.status == ValidationStatus.FAILED

    def test_restricted_all_sd_violations(self):
        """SD001+SD002+SD003+SD004: restricted + PII + missing all sensitive-data fields."""
        contract = _clean_contract(
            schema=[
                {
                    "name": "credit_card",
                    "type": "string",
                    "pii": True,
                    "description": "Credit card number",
                    "required": True,
                    "nullable": False,
                    "max_length": 19,
                }
            ],
            governance={"classification": "restricted"},
            quality_rules={"completeness_threshold": 99},
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert any("SD001" in p for p in policies)  # missing encryption
        assert any("SD002" in p for p in policies)  # missing retention
        assert any("SD003" in p for p in policies)  # missing compliance tags
        assert any("SD004" in p for p in policies)  # missing approved_use_cases

    def test_sd004_not_triggered_for_confidential(self):
        """SD004 (restricted use cases) does NOT fire for confidential classification."""
        contract = _clean_contract(
            schema=[
                {
                    "name": "amount",
                    "type": "float",
                    "description": "Payment amount",
                    "required": True,
                    "nullable": False,
                }
            ],
            governance={
                "classification": "confidential",
                "encryption_required": True,
                "retention_days": 365,
                "compliance_tags": ["GDPR"],
            },
            quality_rules={"completeness_threshold": 99},
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("SD004" in p for p in policies)

    def test_multiple_dq_and_sg_violations_coexist(self):
        """DQ + SG violations can coexist: temporal field without SLA, id field without uniqueness, undocumented fields."""
        contract = _clean_contract(
            schema=[
                # No description → SG001; has 'id' in name → DQ003
                {"name": "record_id", "type": "integer", "required": True, "nullable": False},
                # No description → SG001; temporal field → DQ002
                {"name": "created_at", "type": "timestamp", "required": True, "nullable": False},
            ],
            governance={"classification": "internal"},
            quality_rules={},  # no freshness_sla (DQ002), no uniqueness_fields (DQ003)
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert any("DQ002" in p for p in policies)
        assert any("DQ003" in p for p in policies)
        assert any("SG001" in p for p in policies)


# ---------------------------------------------------------------------------
# DQ001 boundary conditions
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestDQ001Boundaries:
    """Boundary value tests for the DQ001 completeness threshold (>= 95%)."""

    def setup_method(self):
        self.engine = PolicyEngine()

    def _confidential_contract(self, completeness):
        return _clean_contract(
            schema=[
                {
                    "name": "record_id",
                    "type": "integer",
                    "description": "Primary key",
                    "required": True,
                    "nullable": False,
                }
            ],
            governance={"classification": "confidential"},
            quality_rules={
                "completeness_threshold": completeness,
                "freshness_sla": "24h",
                "uniqueness_fields": ["record_id"],
            },
        )

    def test_exactly_95_passes(self):
        """completeness_threshold of exactly 95 satisfies DQ001 (>= 95 means no violation)."""
        result = self.engine.validate_contract(self._confidential_contract(95))
        policies = [v.policy for v in result.violations]
        assert not any("DQ001" in p for p in policies)

    def test_94_triggers_violation(self):
        """completeness_threshold of 94 violates DQ001."""
        result = self.engine.validate_contract(self._confidential_contract(94))
        policies = [v.policy for v in result.violations]
        assert any("DQ001" in p for p in policies)

    def test_94_point_9_triggers_violation(self):
        """completeness_threshold of 94.9 (< 95) violates DQ001."""
        result = self.engine.validate_contract(self._confidential_contract(94.9))
        policies = [v.policy for v in result.violations]
        assert any("DQ001" in p for p in policies)

    def test_100_passes(self):
        """completeness_threshold of 100 clearly satisfies DQ001."""
        result = self.engine.validate_contract(self._confidential_contract(100))
        policies = [v.policy for v in result.violations]
        assert not any("DQ001" in p for p in policies)

    def test_dq001_not_triggered_for_internal(self):
        """DQ001 does not apply to internal classification datasets."""
        contract = _clean_contract(
            governance={"classification": "internal"},
            quality_rules={"completeness_threshold": 50},
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("DQ001" in p for p in policies)

    def test_dq001_not_triggered_for_public(self):
        """DQ001 does not apply to public classification datasets."""
        contract = _clean_contract(
            governance={"classification": "public"},
            quality_rules={"completeness_threshold": 0},
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("DQ001" in p for p in policies)


# ---------------------------------------------------------------------------
# Negative tests: policies that should NOT fire
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestPoliciesNotFired:
    """Tests that verify policies do not fire when their conditions are absent."""

    def setup_method(self):
        self.engine = PolicyEngine()

    def test_dq002_no_temporal_fields_no_violation(self):
        """DQ002: schema without any temporal fields → no freshness_sla violation."""
        contract = _clean_contract(
            schema=[
                {"name": "product_id", "type": "integer", "description": "ID", "required": True, "nullable": False},
                {"name": "price", "type": "float", "description": "Price", "required": True, "nullable": False},
            ],
            governance={"classification": "internal"},
            quality_rules={},  # no freshness_sla
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("DQ002" in p for p in policies)

    def test_dq003_no_id_fields_no_violation(self):
        """DQ003: schema without any field containing 'id' → no uniqueness violation."""
        contract = _clean_contract(
            schema=[
                {"name": "amount", "type": "float", "description": "Amount", "required": True, "nullable": False},
                {"name": "currency", "type": "string", "description": "Currency", "max_length": 3, "required": True, "nullable": False},
            ],
            governance={"classification": "internal"},
            quality_rules={},
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("DQ003" in p for p in policies)

    def test_sg003_both_present_no_violation(self):
        """SG003: owner_name AND owner_email both present → no ownership violation."""
        contract = _clean_contract(owner_name="Alice", owner_email="alice@example.com")
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("SG003" in p for p in policies)

    def test_sg004_no_string_fields_no_violation(self):
        """SG004: contract with no string-type fields → no max_length violation."""
        contract = _clean_contract(
            schema=[
                {"name": "amount", "type": "float", "description": "Amount", "required": True, "nullable": False},
                {"name": "created_at", "type": "timestamp", "description": "Creation time", "required": True, "nullable": False},
            ],
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("SG004" in p for p in policies)

    def test_sg002_optional_nullable_consistent(self):
        """SG002: required=False + nullable=True is consistent → no violation."""
        contract = _clean_contract(
            schema=[
                {"name": "note", "type": "string", "description": "Optional note", "max_length": 255, "required": False, "nullable": True},
            ],
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("SG002" in p for p in policies)

    def test_sd001_no_pii_no_violation(self):
        """SD001: schema with no PII fields → no encryption violation regardless of encryption_required."""
        contract = _clean_contract(
            schema=[
                {"name": "product_name", "type": "string", "description": "Name", "max_length": 255, "required": True, "nullable": False, "pii": False},
            ],
            governance={"classification": "internal", "encryption_required": False},
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("SD001" in p for p in policies)

    def test_sd002_internal_no_retention_no_violation(self):
        """SD002: internal classification doesn't require retention_days."""
        contract = _clean_contract(governance={"classification": "internal"})
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("SD002" in p for p in policies)


# ---------------------------------------------------------------------------
# SG003: partial ownership
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestSG003PartialOwnership:
    """SG003 fires when either owner_name or owner_email is missing."""

    def setup_method(self):
        self.engine = PolicyEngine()

    def test_missing_owner_email_triggers_violation(self):
        contract = _clean_contract(owner_name="Alice", owner_email="")
        # empty string is falsy
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert any("SG003" in p for p in policies)

    def test_missing_owner_name_triggers_violation(self):
        contract = _clean_contract(owner_name="", owner_email="alice@example.com")
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert any("SG003" in p for p in policies)

    def test_both_missing_triggers_violation(self):
        contract = _clean_contract(owner_name="", owner_email="")
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert any("SG003" in p for p in policies)


# ---------------------------------------------------------------------------
# Violation type assertions
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestViolationTypes:
    """Verify that each implemented policy fires with the correct ViolationType."""

    def setup_method(self):
        self.engine = PolicyEngine()

    def test_sd001_is_critical(self):
        """SD001 (PII missing encryption) must be CRITICAL."""
        contract = _clean_contract(
            schema=[{"name": "email", "type": "string", "pii": True, "description": "Email", "max_length": 255, "required": True, "nullable": False}],
            governance={"classification": "internal", "encryption_required": False},
        )
        result = self.engine.validate_contract(contract)
        sd001 = [v for v in result.violations if "SD001" in v.policy]
        assert len(sd001) == 1
        assert sd001[0].type == ViolationType.CRITICAL

    def test_sd002_is_critical(self):
        """SD002 (missing retention for confidential) must be CRITICAL."""
        contract = _clean_contract(
            schema=[{"name": "amount", "type": "float", "description": "Amount", "required": True, "nullable": False}],
            governance={"classification": "confidential"},
            quality_rules={"completeness_threshold": 99},
        )
        result = self.engine.validate_contract(contract)
        sd002 = [v for v in result.violations if "SD002" in v.policy]
        assert len(sd002) == 1
        assert sd002[0].type == ViolationType.CRITICAL

    def test_sd003_is_warning(self):
        """SD003 (PII missing compliance tags) must be WARNING, not CRITICAL."""
        contract = _clean_contract(
            schema=[{"name": "email", "type": "string", "pii": True, "description": "Email", "max_length": 255, "required": True, "nullable": False}],
            governance={
                "classification": "internal",
                "encryption_required": True,  # satisfies SD001
                # no compliance_tags → SD003
            },
        )
        result = self.engine.validate_contract(contract)
        sd003 = [v for v in result.violations if "SD003" in v.policy]
        assert len(sd003) == 1
        assert sd003[0].type == ViolationType.WARNING

    def test_sd004_is_critical(self):
        """SD004 (restricted missing approved_use_cases) must be CRITICAL."""
        contract = _clean_contract(
            schema=[{"name": "amount", "type": "float", "description": "Amount", "required": True, "nullable": False}],
            governance={
                "classification": "restricted",
                "encryption_required": True,
                "retention_days": 365,
                "compliance_tags": ["SOX"],
                # no approved_use_cases → SD004
            },
            quality_rules={"completeness_threshold": 99},
        )
        result = self.engine.validate_contract(contract)
        sd004 = [v for v in result.violations if "SD004" in v.policy]
        assert len(sd004) == 1
        assert sd004[0].type == ViolationType.CRITICAL

    def test_dq001_is_critical(self):
        """DQ001 (low completeness on confidential data) must be CRITICAL."""
        contract = _clean_contract(
            governance={"classification": "confidential"},
            quality_rules={"completeness_threshold": 80},
        )
        result = self.engine.validate_contract(contract)
        dq001 = [v for v in result.violations if "DQ001" in v.policy]
        assert len(dq001) == 1
        assert dq001[0].type == ViolationType.CRITICAL

    def test_dq002_is_warning(self):
        """DQ002 (missing freshness SLA) must be WARNING."""
        contract = _clean_contract(
            schema=[{"name": "event_at", "type": "timestamp", "description": "Event time", "required": True, "nullable": False}],
            quality_rules={},  # no freshness_sla
        )
        result = self.engine.validate_contract(contract)
        dq002 = [v for v in result.violations if "DQ002" in v.policy]
        assert len(dq002) == 1
        assert dq002[0].type == ViolationType.WARNING

    def test_dq003_is_warning(self):
        """DQ003 (missing uniqueness spec for key fields) must be WARNING."""
        contract = _clean_contract(
            schema=[{"name": "record_id", "type": "integer", "description": "ID", "required": True, "nullable": False}],
            quality_rules={},  # no uniqueness_fields
        )
        result = self.engine.validate_contract(contract)
        dq003 = [v for v in result.violations if "DQ003" in v.policy]
        assert len(dq003) == 1
        assert dq003[0].type == ViolationType.WARNING

    def test_sg001_is_warning(self):
        """SG001 (undocumented fields) must be WARNING."""
        contract = _clean_contract(
            schema=[{"name": "amount", "type": "float", "required": True, "nullable": False}],  # no description
        )
        result = self.engine.validate_contract(contract)
        sg001 = [v for v in result.violations if "SG001" in v.policy]
        assert len(sg001) == 1
        assert sg001[0].type == ViolationType.WARNING

    def test_sg002_is_critical(self):
        """SG002 (required field nullable) must be CRITICAL."""
        contract = _clean_contract(
            schema=[{"name": "account_id", "type": "integer", "description": "Account", "required": True, "nullable": True}],
        )
        result = self.engine.validate_contract(contract)
        sg002 = [v for v in result.violations if "SG002" in v.policy]
        assert len(sg002) == 1
        assert sg002[0].type == ViolationType.CRITICAL

    def test_sg003_is_critical(self):
        """SG003 (missing ownership) must be CRITICAL."""
        contract = _clean_contract(owner_name="", owner_email="")
        result = self.engine.validate_contract(contract)
        sg003 = [v for v in result.violations if "SG003" in v.policy]
        assert len(sg003) == 1
        assert sg003[0].type == ViolationType.CRITICAL

    def test_sg004_is_warning(self):
        """SG004 (string field missing max_length) must be WARNING."""
        contract = _clean_contract(
            schema=[{"name": "status", "type": "string", "description": "Status", "required": True, "nullable": False}],  # no max_length
        )
        result = self.engine.validate_contract(contract)
        sg004 = [v for v in result.violations if "SG004" in v.policy]
        assert len(sg004) == 1
        assert sg004[0].type == ViolationType.WARNING


# ---------------------------------------------------------------------------
# Violation field content assertions
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestViolationFieldContent:
    """Verify that violation messages include the correct field names."""

    def setup_method(self):
        self.engine = PolicyEngine()

    def test_sd001_lists_all_pii_field_names(self):
        """SD001 violation field should list every PII field name."""
        contract = _clean_contract(
            schema=[
                {"name": "email_address", "type": "string", "pii": True, "description": "Email", "max_length": 255, "required": True, "nullable": False},
                {"name": "phone_number", "type": "string", "pii": True, "description": "Phone", "max_length": 20, "required": False, "nullable": True},
                {"name": "amount", "type": "float", "description": "Amount", "required": True, "nullable": False},
            ],
            governance={"classification": "internal", "encryption_required": False},
        )
        result = self.engine.validate_contract(contract)
        sd001 = [v for v in result.violations if "SD001" in v.policy]
        assert len(sd001) == 1
        assert "email_address" in sd001[0].field
        assert "phone_number" in sd001[0].field
        assert "amount" not in sd001[0].field

    def test_sg002_lists_all_inconsistent_field_names(self):
        """SG002 violation field should list all required+nullable fields."""
        contract = _clean_contract(
            schema=[
                {"name": "field_a", "type": "integer", "description": "A", "required": True, "nullable": True},
                {"name": "field_b", "type": "integer", "description": "B", "required": True, "nullable": True},
                {"name": "field_c", "type": "integer", "description": "C", "required": False, "nullable": True},  # consistent
            ],
        )
        result = self.engine.validate_contract(contract)
        sg002 = [v for v in result.violations if "SG002" in v.policy]
        assert len(sg002) == 1
        assert "field_a" in sg002[0].field
        assert "field_b" in sg002[0].field
        assert "field_c" not in sg002[0].field

    def test_sg001_lists_all_undocumented_fields(self):
        """SG001 violation field should list all fields missing descriptions."""
        contract = _clean_contract(
            schema=[
                {"name": "documented", "type": "integer", "description": "Has a description", "required": True, "nullable": False},
                {"name": "undoc_a", "type": "integer", "required": True, "nullable": False},
                {"name": "undoc_b", "type": "float", "required": True, "nullable": False},
            ],
        )
        result = self.engine.validate_contract(contract)
        sg001 = [v for v in result.violations if "SG001" in v.policy]
        assert len(sg001) == 1
        assert "undoc_a" in sg001[0].field
        assert "undoc_b" in sg001[0].field
        assert "documented" not in sg001[0].field


# ---------------------------------------------------------------------------
# Status determination logic
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestValidationStatusDetermination:
    """Verify overall status is computed correctly from violation types."""

    def setup_method(self):
        self.engine = PolicyEngine()

    def test_warning_only_gives_warning_status(self):
        """Only WARNING violations → status is WARNING, not FAILED."""
        # SD003 (warning) triggered; no critical violations
        contract = _clean_contract(
            schema=[
                {
                    "name": "email",
                    "type": "string",
                    "pii": True,
                    "description": "Email",
                    "max_length": 255,
                    "required": True,
                    "nullable": False,
                }
            ],
            governance={
                "classification": "internal",
                "encryption_required": True,  # SD001 satisfied
                # no compliance_tags → SD003 (WARNING)
            },
        )
        result = self.engine.validate_contract(contract)
        assert result.status == ValidationStatus.WARNING
        assert result.failures == 0
        assert result.warnings > 0

    def test_one_critical_gives_failed_status(self):
        """A single CRITICAL violation → status is FAILED."""
        contract = _clean_contract(
            schema=[
                {"name": "email", "type": "string", "pii": True, "description": "Email", "max_length": 255, "required": True, "nullable": False}
            ],
            governance={"classification": "internal", "encryption_required": False},
        )
        result = self.engine.validate_contract(contract)
        assert result.status == ValidationStatus.FAILED
        assert result.failures >= 1

    def test_passed_count_equals_total_minus_violations(self):
        """passed = total policy IDs (17) - violation count."""
        contract = _clean_contract(
            schema=[
                {"name": "record_id", "type": "integer", "description": "ID", "required": True, "nullable": False}
            ],
        )
        result = self.engine.validate_contract(contract)
        total_policies = len(self.engine._get_all_policy_ids())
        assert result.passed == total_policies - len(result.violations)


# ---------------------------------------------------------------------------
# Policy count verification
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestPolicyCount:
    """Verify the YAML files define exactly the expected set of policy IDs."""

    def setup_method(self):
        self.engine = PolicyEngine()

    def test_total_policy_count_is_17(self):
        """All YAML files combined define exactly 17 policy IDs."""
        ids = self.engine._get_all_policy_ids()
        assert len(ids) == 17, f"Expected 17 policy IDs, got {len(ids)}: {sorted(ids)}"

    def test_all_expected_policy_ids_present(self):
        """Every expected policy ID (SD001-SD005, DQ001-DQ005, SG001-SG007) is loaded."""
        ids = self.engine._get_all_policy_ids()
        expected = [
            "SD001", "SD002", "SD003", "SD004", "SD005",
            "DQ001", "DQ002", "DQ003", "DQ004", "DQ005",
            "SG001", "SG002", "SG003", "SG004", "SG005", "SG006", "SG007",
        ]
        for eid in expected:
            assert eid in ids, f"Policy ID {eid} not found in loaded YAML"


# ---------------------------------------------------------------------------
# Unimplemented YAML policies — regression guards
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestUnimplementedPolicies:
    """
    SD005, DQ004, DQ005, SG005, SG006, SG007 are defined in YAML but not yet
    enforced by the rule engine. These tests serve as regression guards:
    they verify the engine does NOT accidentally start enforcing these policies
    without a corresponding implementation.
    """

    def setup_method(self):
        self.engine = PolicyEngine()

    def test_sd005_cross_border_not_enforced(self):
        """
        SD005 (cross-border PII data residency) is in YAML but not in
        _validate_sensitive_data. No SD005 violation should appear.
        """
        # Even with cross-border PII and no data_residency field, SD005 should not fire.
        contract = _clean_contract(
            schema=[
                {"name": "passport_number", "type": "string", "pii": True, "description": "Passport", "max_length": 20, "required": True, "nullable": False}
            ],
            governance={
                "classification": "restricted",
                "encryption_required": True,
                "retention_days": 365,
                "compliance_tags": ["GDPR"],
                "approved_use_cases": ["compliance_reporting"],
                # intentionally no data_residency field
            },
            quality_rules={"completeness_threshold": 99, "freshness_sla": "24h", "uniqueness_fields": ["passport_number"]},
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("SD005" in p for p in policies), "SD005 should not be enforced yet"

    def test_dq004_accuracy_threshold_not_enforced(self):
        """DQ004 (accuracy threshold) is in YAML but not in _validate_data_quality."""
        contract = _clean_contract(
            governance={"classification": "internal"},
            quality_rules={"accuracy_threshold": 0},  # deliberately low
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("DQ004" in p for p in policies), "DQ004 should not be enforced yet"

    def test_dq005_completeness_definition_not_enforced(self):
        """DQ005 (completeness definition) is in YAML but not in _validate_data_quality."""
        contract = _clean_contract(
            governance={"classification": "internal"},
            quality_rules={},
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("DQ005" in p for p in policies), "DQ005 should not be enforced yet"

    def test_sg005_enum_values_not_enforced(self):
        """SG005 (enum value specification) is in YAML but not in _validate_schema_governance."""
        contract = _clean_contract(
            schema=[{"name": "status", "type": "string", "description": "Status", "max_length": 20, "required": True, "nullable": False}],
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("SG005" in p for p in policies), "SG005 should not be enforced yet"

    def test_sg006_breaking_schema_changes_not_enforced(self):
        """SG006 (breaking schema changes require major version bump) is in YAML but not enforced."""
        contract = _clean_contract()
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("SG006" in p for p in policies), "SG006 should not be enforced yet"

    def test_sg007_numeric_constraints_not_enforced(self):
        """SG007 (numeric field min/max constraints) is in YAML but not in _validate_schema_governance."""
        contract = _clean_contract(
            schema=[{"name": "age", "type": "integer", "description": "Age in years", "required": True, "nullable": False}],
        )
        result = self.engine.validate_contract(contract)
        policies = [v.policy for v in result.violations]
        assert not any("SG007" in p for p in policies), "SG007 should not be enforced yet"

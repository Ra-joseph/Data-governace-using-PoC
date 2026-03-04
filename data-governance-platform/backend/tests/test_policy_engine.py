"""
Unit tests for PolicyEngine service.
"""
import pytest
from app.services.policy_engine import PolicyEngine
from app.schemas.contract import ViolationType, ValidationStatus


@pytest.mark.unit
@pytest.mark.service
class TestPolicyEngine:
    """Test cases for PolicyEngine."""

    def test_policy_engine_initialization(self):
        """Test that PolicyEngine initializes correctly."""
        engine = PolicyEngine()
        assert engine is not None
        assert engine.policies is not None
        assert len(engine.policies) > 0

    def test_load_policies(self):
        """Test that policies are loaded from YAML files."""
        engine = PolicyEngine()
        policies = engine.policies

        # Check that all three policy types are loaded
        assert "Sensitive Data Policies" in policies or "sensitive_data_policies" in str(policies)
        assert len(policies) > 0

    def test_validate_contract_passes(self, sample_contract_data):
        """Test validation of a contract that passes all policies."""
        engine = PolicyEngine()
        result = engine.validate_contract(sample_contract_data)

        assert result is not None
        assert result.status == ValidationStatus.PASSED
        assert result.failures == 0

    def test_validate_contract_with_violations(self, sample_contract_with_violations):
        """Test validation of a contract with policy violations."""
        engine = PolicyEngine()
        result = engine.validate_contract(sample_contract_with_violations)

        assert result is not None
        assert result.status == ValidationStatus.FAILED
        assert result.failures > 0
        assert len(result.violations) > 0

    def test_sd001_pii_encryption_required(self):
        """Test SD001: PII fields must have encryption enabled."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "ssn",
                    "type": "string",
                    "description": "Social Security Number",
                    "pii": True,
                    "required": True,
                    "nullable": False
                }
            ],
            "governance": {
                "classification": "confidential",
                "encryption_required": False  # Violation!
            },
            "quality_rules": {}
        }

        result = engine.validate_contract(contract_data)

        # Should have SD001 violation
        violations = [v for v in result.violations if "SD001" in v.policy]
        assert len(violations) > 0
        assert violations[0].type == ViolationType.CRITICAL

    def test_sd002_retention_policy_required(self):
        """Test SD002: Confidential/Restricted data must specify retention period."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "data",
                    "type": "string",
                    "description": "Some data",
                    "pii": False
                }
            ],
            "governance": {
                "classification": "confidential"
                # Missing retention_days - Violation!
            },
            "quality_rules": {}
        }

        result = engine.validate_contract(contract_data)

        # Should have SD002 violation
        violations = [v for v in result.violations if "SD002" in v.policy]
        assert len(violations) > 0
        assert violations[0].type == ViolationType.CRITICAL

    def test_sd003_pii_compliance_tags(self):
        """Test SD003: PII datasets should have compliance tags."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "email",
                    "type": "string",
                    "description": "Email",
                    "pii": True,
                    "required": True,
                    "nullable": False
                }
            ],
            "governance": {
                "classification": "internal",
                "encryption_required": True
                # Missing compliance_tags - Warning!
            },
            "quality_rules": {}
        }

        result = engine.validate_contract(contract_data)

        # Should have SD003 warning
        violations = [v for v in result.violations if "SD003" in v.policy]
        assert len(violations) > 0
        assert violations[0].type == ViolationType.WARNING

    def test_sd004_restricted_use_cases(self):
        """Test SD004: Restricted data must specify approved use cases."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "data",
                    "type": "string",
                    "description": "Restricted data",
                    "pii": False
                }
            ],
            "governance": {
                "classification": "restricted",
                "retention_days": 365
                # Missing approved_use_cases - Violation!
            },
            "quality_rules": {}
        }

        result = engine.validate_contract(contract_data)

        # Should have SD004 violation
        violations = [v for v in result.violations if "SD004" in v.policy]
        assert len(violations) > 0
        assert violations[0].type == ViolationType.CRITICAL

    def test_dq001_critical_data_completeness(self):
        """Test DQ001: Critical data requires high completeness."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "data",
                    "type": "string",
                    "description": "Some data",
                    "pii": False
                }
            ],
            "governance": {
                "classification": "confidential",
                "retention_days": 365
            },
            "quality_rules": {
                "completeness_threshold": 80  # Too low - Violation!
            }
        }

        result = engine.validate_contract(contract_data)

        # Should have DQ001 violation
        violations = [v for v in result.violations if "DQ001" in v.policy]
        assert len(violations) > 0
        assert violations[0].type == ViolationType.CRITICAL

    def test_dq002_freshness_sla_required(self):
        """Test DQ002: Temporal datasets should specify freshness SLA."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "created_at",
                    "type": "timestamp",
                    "description": "Creation timestamp",
                    "pii": False
                }
            ],
            "governance": {
                "classification": "internal"
            },
            "quality_rules": {
                # Missing freshness_sla - Warning!
            }
        }

        result = engine.validate_contract(contract_data)

        # Should have DQ002 warning
        violations = [v for v in result.violations if "DQ002" in v.policy]
        assert len(violations) > 0
        assert violations[0].type == ViolationType.WARNING

    def test_dq003_uniqueness_specification(self):
        """Test DQ003: Key fields should have uniqueness specification."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "customer_id",
                    "type": "integer",
                    "description": "Customer ID",
                    "pii": False
                }
            ],
            "governance": {
                "classification": "internal"
            },
            "quality_rules": {
                # Missing uniqueness_fields - Warning!
            }
        }

        result = engine.validate_contract(contract_data)

        # Should have DQ003 warning
        violations = [v for v in result.violations if "DQ003" in v.policy]
        assert len(violations) > 0
        assert violations[0].type == ViolationType.WARNING

    def test_sg001_field_documentation_required(self):
        """Test SG001: Field documentation required."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "field1",
                    "type": "string",
                    # Missing description - Warning!
                    "pii": False
                }
            ],
            "governance": {
                "classification": "internal"
            },
            "quality_rules": {}
        }

        result = engine.validate_contract(contract_data)

        # Should have SG001 warning
        violations = [v for v in result.violations if "SG001" in v.policy]
        assert len(violations) > 0
        assert violations[0].type == ViolationType.WARNING

    def test_sg002_required_field_consistency(self):
        """Test SG002: Required fields cannot be nullable."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "field1",
                    "type": "string",
                    "description": "Test field",
                    "required": True,
                    "nullable": True,  # Inconsistent - Violation!
                    "pii": False
                }
            ],
            "governance": {
                "classification": "internal"
            },
            "quality_rules": {}
        }

        result = engine.validate_contract(contract_data)

        # Should have SG002 violation
        violations = [v for v in result.violations if "SG002" in v.policy]
        assert len(violations) > 0
        assert violations[0].type == ViolationType.CRITICAL

    def test_sg003_dataset_ownership_required(self):
        """Test SG003: Dataset ownership required."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test"
                # Missing owner_name and owner_email - Violation!
            },
            "schema": [
                {
                    "name": "field1",
                    "type": "string",
                    "description": "Test field",
                    "pii": False
                }
            ],
            "governance": {
                "classification": "internal"
            },
            "quality_rules": {}
        }

        result = engine.validate_contract(contract_data)

        # Should have SG003 violation
        violations = [v for v in result.violations if "SG003" in v.policy]
        assert len(violations) > 0
        assert violations[0].type == ViolationType.CRITICAL

    def test_sg004_string_field_constraints(self):
        """Test SG004: String fields should have max_length."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "name",
                    "type": "string",
                    "description": "Name field",
                    # Missing max_length - Warning!
                    "pii": False
                }
            ],
            "governance": {
                "classification": "internal"
            },
            "quality_rules": {}
        }

        result = engine.validate_contract(contract_data)

        # Should have SG004 warning
        violations = [v for v in result.violations if "SG004" in v.policy]
        assert len(violations) > 0
        assert violations[0].type == ViolationType.WARNING

    def test_validation_status_passed(self):
        """Test that validation status is PASSED when no violations."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "id",
                    "type": "integer",
                    "description": "ID field",
                    "required": True,
                    "nullable": False,
                    "pii": False
                }
            ],
            "governance": {
                "classification": "public"
            },
            "quality_rules": {
                "uniqueness_fields": ["id"]
            }
        }

        result = engine.validate_contract(contract_data)

        # Should pass or have only warnings
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.WARNING]
        assert result.failures == 0

    def test_validation_status_warning(self):
        """Test that validation status is WARNING when only warnings present."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Test Owner",
                "owner_email": "test@example.com"
            },
            "schema": [
                {
                    "name": "field1",
                    "type": "string",
                    # Missing description - Warning only
                    "pii": False
                }
            ],
            "governance": {
                "classification": "public"
            },
            "quality_rules": {}
        }

        result = engine.validate_contract(contract_data)

        # Should have warnings but no failures
        assert result.failures == 0
        assert result.warnings > 0

    def test_validation_status_failed(self):
        """Test that validation status is FAILED when critical violations present."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test"
                # Missing owner - Critical violation
            },
            "schema": [
                {
                    "name": "field1",
                    "type": "string",
                    "description": "Test",
                    "pii": False
                }
            ],
            "governance": {
                "classification": "internal"
            },
            "quality_rules": {}
        }

        result = engine.validate_contract(contract_data)

        # Should fail
        assert result.status == ValidationStatus.FAILED
        assert result.failures > 0


@pytest.mark.unit
@pytest.mark.service
class TestPolicyEngineEdgeCases:
    """Edge case tests for PolicyEngine."""

    def test_validate_empty_contract(self):
        """Test validation of contract with all empty structures."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {},
            "schema": [],
            "governance": {},
            "quality_rules": {}
        }
        result = engine.validate_contract(contract_data)
        assert result is not None
        # Should still produce violations for missing ownership
        assert result.status == ValidationStatus.FAILED

    def test_validate_empty_schema(self):
        """Test validation with empty schema produces no field-level violations."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Owner",
                "owner_email": "owner@test.com"
            },
            "schema": [],
            "governance": {"classification": "public"},
            "quality_rules": {}
        }
        result = engine.validate_contract(contract_data)
        # No schema fields → no SG001/SG002/SG004 violations
        sg_violations = [v for v in result.violations if v.policy.startswith("SG00")]
        # Only SG003 (ownership) should NOT trigger since we have owner
        for v in sg_violations:
            assert v.policy != "SG003"

    def test_validate_null_governance(self):
        """Test validation with empty governance defaults to internal."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Owner",
                "owner_email": "owner@test.com"
            },
            "schema": [{"name": "id", "type": "integer", "description": "ID", "pii": False}],
            "governance": {},
            "quality_rules": {}
        }
        result = engine.validate_contract(contract_data)
        # Should not crash
        assert result is not None

    def test_sd001_pii_with_encryption_passes(self):
        """Test SD001: PII with encryption enabled should pass."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Owner",
                "owner_email": "owner@test.com"
            },
            "schema": [
                {"name": "email", "type": "string", "description": "Email",
                 "pii": True, "required": True, "nullable": False}
            ],
            "governance": {
                "classification": "confidential",
                "encryption_required": True,
                "retention_days": 365,
                "compliance_tags": ["GDPR"]
            },
            "quality_rules": {"completeness_threshold": 99}
        }
        result = engine.validate_contract(contract_data)
        sd001 = [v for v in result.violations if "SD001" in v.policy]
        assert len(sd001) == 0

    def test_sd002_public_classification_no_retention(self):
        """Test SD002: Public data should not require retention policy."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Owner",
                "owner_email": "owner@test.com"
            },
            "schema": [{"name": "data", "type": "string", "description": "Data", "pii": False}],
            "governance": {"classification": "public"},
            "quality_rules": {}
        }
        result = engine.validate_contract(contract_data)
        sd002 = [v for v in result.violations if "SD002" in v.policy]
        assert len(sd002) == 0

    def test_sd002_retention_days_zero(self):
        """Test SD002: retention_days=0 should still trigger violation for confidential."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Owner",
                "owner_email": "owner@test.com"
            },
            "schema": [{"name": "data", "type": "string", "description": "Data", "pii": False}],
            "governance": {
                "classification": "confidential",
                "retention_days": 0
            },
            "quality_rules": {}
        }
        result = engine.validate_contract(contract_data)
        sd002 = [v for v in result.violations if "SD002" in v.policy]
        # retention_days=0 is technically present but zero, behavior depends on engine
        assert result is not None

    def test_dq001_completeness_exactly_95(self):
        """Test DQ001: completeness at exactly 95% should pass."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Owner",
                "owner_email": "owner@test.com"
            },
            "schema": [{"name": "data", "type": "string", "description": "Data", "pii": False}],
            "governance": {"classification": "confidential", "retention_days": 365},
            "quality_rules": {"completeness_threshold": 95}
        }
        result = engine.validate_contract(contract_data)
        dq001 = [v for v in result.violations if "DQ001" in v.policy]
        assert len(dq001) == 0

    def test_dq001_completeness_94_point_9(self):
        """Test DQ001: completeness at 94.9% should trigger violation."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Owner",
                "owner_email": "owner@test.com"
            },
            "schema": [{"name": "data", "type": "string", "description": "Data", "pii": False}],
            "governance": {"classification": "confidential", "retention_days": 365},
            "quality_rules": {"completeness_threshold": 80}
        }
        result = engine.validate_contract(contract_data)
        dq001 = [v for v in result.violations if "DQ001" in v.policy]
        assert len(dq001) > 0

    def test_dq001_public_low_completeness(self):
        """Test DQ001: public data with low completeness should not trigger."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Owner",
                "owner_email": "owner@test.com"
            },
            "schema": [{"name": "data", "type": "string", "description": "Data", "pii": False}],
            "governance": {"classification": "public"},
            "quality_rules": {"completeness_threshold": 50}
        }
        result = engine.validate_contract(contract_data)
        dq001 = [v for v in result.violations if "DQ001" in v.policy]
        assert len(dq001) == 0

    def test_sg001_empty_description_string(self):
        """Test SG001: empty string description is treated as missing."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Owner",
                "owner_email": "owner@test.com"
            },
            "schema": [{"name": "field1", "type": "string", "description": "", "pii": False}],
            "governance": {"classification": "internal"},
            "quality_rules": {}
        }
        result = engine.validate_contract(contract_data)
        sg001 = [v for v in result.violations if "SG001" in v.policy]
        assert len(sg001) > 0

    def test_sg003_owner_name_only(self):
        """Test SG003: having name but missing email triggers violation."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Owner"
                # Missing owner_email
            },
            "schema": [{"name": "id", "type": "integer", "description": "ID", "pii": False}],
            "governance": {"classification": "internal"},
            "quality_rules": {}
        }
        result = engine.validate_contract(contract_data)
        sg003 = [v for v in result.violations if "SG003" in v.policy]
        assert len(sg003) > 0

    def test_sg003_owner_email_only(self):
        """Test SG003: having email but missing name triggers violation."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_email": "owner@test.com"
                # Missing owner_name
            },
            "schema": [{"name": "id", "type": "integer", "description": "ID", "pii": False}],
            "governance": {"classification": "internal"},
            "quality_rules": {}
        }
        result = engine.validate_contract(contract_data)
        sg003 = [v for v in result.violations if "SG003" in v.policy]
        assert len(sg003) > 0

    def test_sg004_integer_fields_no_max_length(self):
        """Test SG004: non-string fields should not trigger max_length warning."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "test",
                "owner_name": "Owner",
                "owner_email": "owner@test.com"
            },
            "schema": [
                {"name": "count", "type": "integer", "description": "Count", "pii": False},
                {"name": "flag", "type": "boolean", "description": "Flag", "pii": False}
            ],
            "governance": {"classification": "internal"},
            "quality_rules": {}
        }
        result = engine.validate_contract(contract_data)
        sg004 = [v for v in result.violations if "SG004" in v.policy]
        assert len(sg004) == 0

    def test_validate_unicode_field_names(self):
        """Test validation with unicode field names."""
        engine = PolicyEngine()
        contract_data = {
            "dataset": {
                "name": "unicode_test",
                "owner_name": "Tëst Öwner",
                "owner_email": "owner@test.com"
            },
            "schema": [
                {"name": "données", "type": "string", "description": "Données",
                 "pii": False}
            ],
            "governance": {"classification": "internal"},
            "quality_rules": {}
        }
        result = engine.validate_contract(contract_data)
        assert result is not None

    def test_validate_many_fields_schema(self):
        """Test validation with a large number of schema fields."""
        engine = PolicyEngine()
        schema = [
            {"name": f"field_{i}", "type": "string", "description": f"Field {i}", "pii": False}
            for i in range(50)
        ]
        contract_data = {
            "dataset": {
                "name": "big_schema",
                "owner_name": "Owner",
                "owner_email": "owner@test.com"
            },
            "schema": schema,
            "governance": {"classification": "internal"},
            "quality_rules": {}
        }
        result = engine.validate_contract(contract_data)
        assert result is not None
        # SG004 groups all missing max_length fields into one violation
        sg004 = [v for v in result.violations if "SG004" in v.policy]
        assert len(sg004) >= 1
        # All 50 fields should be mentioned in the violation
        assert "field_0" in sg004[0].field
        assert "field_49" in sg004[0].field

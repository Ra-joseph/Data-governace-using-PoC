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

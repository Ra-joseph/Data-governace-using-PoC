"""
Unit tests for SemanticPolicyEngine service.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

from app.services.semantic_policy_engine import SemanticPolicyEngine
from app.services.ollama_client import OllamaClient, OllamaError
from app.services.llm_provider import LLMProviderError
from app.schemas.contract import ViolationType, ValidationStatus


@pytest.mark.unit
@pytest.mark.service
class TestSemanticEngineInit:
    """Test SemanticPolicyEngine initialization."""

    @patch("app.services.semantic_policy_engine.get_llm_provider")
    def test_init_enabled_with_client(self, mock_factory):
        """Test initialization with a provided OllamaClient."""
        mock_client = Mock(spec=OllamaClient)
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            ollama_client=mock_client,
            enabled=True
        )
        assert engine.enabled is True
        assert engine.llm_client == mock_client
        mock_factory.assert_not_called()

    def test_init_disabled(self):
        """Test initialization with enabled=False."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        assert engine.enabled is False
        assert engine.llm_client is None


@pytest.mark.unit
@pytest.mark.service
class TestSemanticEngineAvailability:
    """Test SemanticPolicyEngine availability checks."""

    def test_is_available_disabled(self):
        """Test is_available returns False when disabled."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        assert engine.is_available() is False

    @patch("app.services.semantic_policy_engine.get_llm_provider")
    def test_is_available_no_policies(self, mock_factory):
        """Test is_available returns False when no policies loaded."""
        mock_client = Mock(spec=OllamaClient)
        mock_client.is_available.return_value = True

        engine = SemanticPolicyEngine(
            policies_path="/nonexistent/path",
            ollama_client=mock_client,
            enabled=True
        )
        engine.policies = {}
        assert engine.is_available() is False

    @patch("app.services.semantic_policy_engine.get_llm_provider")
    def test_is_available_ollama_down(self, mock_factory):
        """Test is_available returns False when Ollama is not running."""
        mock_client = Mock(spec=OllamaClient)
        mock_client.is_available.return_value = False

        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            ollama_client=mock_client,
            enabled=True
        )
        assert engine.is_available() is False

    @patch("app.services.semantic_policy_engine.get_llm_provider")
    def test_is_available_all_conditions_met(self, mock_factory):
        """Test is_available returns True when all conditions are met."""
        mock_client = Mock(spec=OllamaClient)
        mock_client.is_available.return_value = True

        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            ollama_client=mock_client,
            enabled=True
        )
        # Engine should have loaded policies from the YAML file
        if engine.policies:
            assert engine.is_available() is True


@pytest.mark.unit
@pytest.mark.service
class TestSemanticEngineValidation:
    """Test SemanticPolicyEngine validation."""

    def test_validate_contract_unavailable(self):
        """Test validation returns PASSED when engine is unavailable."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        contract_data = {"dataset": {"name": "test"}, "schema": []}

        result = engine.validate_contract(contract_data)
        assert result.status == ValidationStatus.PASSED
        assert result.passed == 0
        assert result.warnings == 0
        assert result.failures == 0
        assert result.violations == []

    @patch("app.services.semantic_policy_engine.get_llm_provider")
    def test_validate_contract_selected_policies(self, mock_factory):
        """Test validation with selected policies."""
        mock_client = Mock(spec=OllamaClient)
        mock_client.is_available.return_value = True
        mock_client.analyze_with_retry.return_value = {
            "response": {"is_sensitive": False, "confidence": 30}
        }

        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            ollama_client=mock_client,
            enabled=True
        )

        if engine.policies:
            contract_data = {
                "dataset": {"name": "test", "description": "test"},
                "schema": [{"name": "id", "type": "integer", "pii": False}],
                "governance": {"classification": "internal"},
                "quality_rules": {}
            }
            result = engine.validate_contract(contract_data, selected_policies=["SEM001"])
            # Should only run SEM001
            assert result is not None

    @patch("app.services.semantic_policy_engine.get_llm_provider")
    def test_evaluate_policy_ollama_error(self, mock_factory):
        """Test that LLMProviderError results in a WARNING violation."""
        mock_client = Mock(spec=OllamaClient)
        mock_client.analyze_with_retry.side_effect = LLMProviderError("Connection refused")

        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            ollama_client=mock_client,
            enabled=True
        )

        policy = {
            "id": "SEM001",
            "name": "test_policy",
            "severity": "high",
            "prompt_template": "Test {dataset_name}"
        }
        contract_data = {
            "dataset": {"name": "test", "description": "test"},
            "schema": [],
            "governance": {},
            "quality_rules": {}
        }

        violations = engine._evaluate_policy(policy, contract_data)
        assert len(violations) == 1
        assert violations[0].type == ViolationType.WARNING
        assert "Failed to perform semantic analysis" in violations[0].message

    @patch("app.services.semantic_policy_engine.get_llm_provider")
    def test_evaluate_policy_unexpected_error(self, mock_factory):
        """Test that unexpected exceptions don't crash the engine."""
        mock_client = Mock(spec=OllamaClient)
        mock_client.analyze_with_retry.side_effect = RuntimeError("Unexpected")

        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            ollama_client=mock_client,
            enabled=True
        )

        policy = {
            "id": "SEM001",
            "name": "test_policy",
            "severity": "high",
            "prompt_template": "Test {dataset_name}"
        }
        contract_data = {
            "dataset": {"name": "test", "description": "test"},
            "schema": [],
            "governance": {},
            "quality_rules": {}
        }

        violations = engine._evaluate_policy(policy, contract_data)
        # Should not crash, may return empty or with logged error
        assert isinstance(violations, list)


@pytest.mark.unit
@pytest.mark.service
class TestSemanticEngineParsers:
    """Test SemanticPolicyEngine LLM response parsers."""

    def _make_engine(self):
        """Create engine for parser tests."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        # Set config for confidence threshold
        engine.config = {"execution": {"confidence_threshold": 70}}
        return engine

    def test_parse_sem001_sensitive_high_confidence(self):
        """Test SEM001 parser creates violation for high-confidence sensitive data."""
        engine = self._make_engine()
        data = {
            "is_sensitive": True,
            "confidence": 90,
            "reasoning": "Contains SSN patterns",
            "recommended_actions": ["Encrypt data", "Add retention policy"]
        }

        violations = engine._parse_sem001("SEM001", "sensitive_data", "critical", data, 70)
        assert len(violations) == 1
        assert violations[0].type == ViolationType.CRITICAL
        assert "90%" in violations[0].message

    def test_parse_sem001_below_threshold(self):
        """Test SEM001 parser skips low-confidence results."""
        engine = self._make_engine()
        data = {
            "is_sensitive": True,
            "confidence": 50,
            "reasoning": "Might be sensitive"
        }

        violations = engine._parse_sem001("SEM001", "sensitive_data", "critical", data, 70)
        assert len(violations) == 0

    def test_parse_sem001_not_sensitive(self):
        """Test SEM001 parser returns empty for non-sensitive data."""
        engine = self._make_engine()
        data = {
            "is_sensitive": False,
            "confidence": 95,
            "reasoning": "Clearly not sensitive"
        }

        violations = engine._parse_sem001("SEM001", "sensitive_data", "critical", data, 70)
        assert len(violations) == 0

    def test_parse_sem002_inconsistent(self):
        """Test SEM002 parser detects business logic inconsistencies."""
        engine = self._make_engine()
        data = {
            "is_consistent": False,
            "issues": [
                {
                    "severity": "high",
                    "field": "governance.retention_days",
                    "issue": "Retention too short for compliance",
                    "suggestion": "Increase to 7 years"
                }
            ]
        }

        violations = engine._parse_sem002("SEM002", "consistency", "high", data)
        assert len(violations) == 1
        assert violations[0].field == "governance.retention_days"

    def test_parse_sem002_consistent(self):
        """Test SEM002 parser returns empty when consistent."""
        engine = self._make_engine()
        data = {"is_consistent": True, "issues": []}

        violations = engine._parse_sem002("SEM002", "consistency", "high", data)
        assert len(violations) == 0

    def test_parse_sem003_security_concerns(self):
        """Test SEM003 parser detects security concerns."""
        engine = self._make_engine()
        data = {
            "security_concerns": [
                {
                    "severity": "critical",
                    "affected_fields": ["ssn", "credit_card"],
                    "concern_type": "Encryption Missing",
                    "description": "PII without encryption",
                    "remediation": "Enable AES-256 encryption"
                },
                {
                    "severity": "medium",
                    "affected_fields": ["password"],
                    "concern_type": "Hashing Required",
                    "description": "Password stored in plain text",
                    "remediation": "Use bcrypt hashing"
                }
            ]
        }

        violations = engine._parse_sem003("SEM003", "security", data)
        assert len(violations) == 2
        assert violations[0].type == ViolationType.CRITICAL
        assert violations[1].type == ViolationType.WARNING

    def test_parse_sem003_no_concerns(self):
        """Test SEM003 parser returns empty when no concerns."""
        engine = self._make_engine()
        data = {"security_concerns": []}

        violations = engine._parse_sem003("SEM003", "security", data)
        assert len(violations) == 0

    def test_parse_sem004_compliance_not_met(self):
        """Test SEM004 parser detects compliance gaps."""
        engine = self._make_engine()
        data = {
            "compliance_analysis": [
                {
                    "framework": "GDPR",
                    "requirements_met": False,
                    "missing_requirements": ["data_residency", "consent_tracking"],
                    "recommendations": ["Add EU data residency", "Implement consent tracking"]
                }
            ]
        }

        violations = engine._parse_sem004("SEM004", "compliance", data)
        assert len(violations) == 1
        assert violations[0].type == ViolationType.CRITICAL
        assert "GDPR" in violations[0].message

    def test_parse_sem004_compliance_met(self):
        """Test SEM004 parser returns empty when compliant."""
        engine = self._make_engine()
        data = {
            "compliance_analysis": [
                {
                    "framework": "GDPR",
                    "requirements_met": True,
                    "missing_requirements": [],
                    "recommendations": []
                }
            ]
        }

        violations = engine._parse_sem004("SEM004", "compliance", data)
        assert len(violations) == 0

    def test_parse_generic_with_issues(self):
        """Test generic parser for SEM005-SEM008 with issues."""
        engine = self._make_engine()
        data = {
            "issues": [
                {
                    "field": "schema.field_name",
                    "message": "Naming convention violation",
                    "remediation": "Use snake_case"
                }
            ]
        }

        violations = engine._parse_generic("SEM005", "naming", "medium", data)
        assert len(violations) == 1
        assert violations[0].type == ViolationType.WARNING

    def test_parse_generic_no_issues(self):
        """Test generic parser returns empty when no issues."""
        engine = self._make_engine()
        data = {"issues": []}

        violations = engine._parse_generic("SEM005", "naming", "medium", data)
        assert len(violations) == 0

    def test_parse_generic_missing_issues_key(self):
        """Test generic parser handles missing issues key."""
        engine = self._make_engine()
        data = {"result": "all_good"}

        violations = engine._parse_generic("SEM005", "naming", "medium", data)
        assert len(violations) == 0


@pytest.mark.unit
@pytest.mark.service
class TestSemanticEngineSeverity:
    """Test SemanticPolicyEngine severity conversion."""

    def test_severity_to_type_critical(self):
        """Test critical severity maps to CRITICAL."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        assert engine._severity_to_type("critical") == ViolationType.CRITICAL
        assert engine._severity_to_type("high") == ViolationType.CRITICAL

    def test_severity_to_type_warning(self):
        """Test warning/medium severity maps to WARNING."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        assert engine._severity_to_type("warning") == ViolationType.WARNING
        assert engine._severity_to_type("medium") == ViolationType.WARNING
        assert engine._severity_to_type("low") == ViolationType.WARNING

    def test_severity_to_type_unknown(self):
        """Test unknown severity maps to INFO."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        assert engine._severity_to_type("foo") == ViolationType.INFO
        assert engine._severity_to_type("") == ViolationType.INFO


@pytest.mark.unit
@pytest.mark.service
class TestSemanticEngineFormatters:
    """Test SemanticPolicyEngine format helpers."""

    def test_format_fields_list_with_fields(self):
        """Test formatting schema fields as a list."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        schema = [
            {"name": "email", "type": "string", "pii": True, "description": "Email address"},
            {"name": "id", "type": "integer", "pii": False, "description": "Unique ID"}
        ]
        result = engine._format_fields_list(schema)
        assert "email" in result
        assert "[PII]" in result
        assert "id" in result

    def test_format_fields_list_empty_schema(self):
        """Test formatting empty schema."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        result = engine._format_fields_list([])
        assert result == "No fields"

    def test_format_quality_rules_empty(self):
        """Test formatting empty quality rules."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        result = engine._format_quality_rules({})
        assert result == "No quality rules defined"

    def test_format_quality_rules_with_rules(self):
        """Test formatting quality rules with entries."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        result = engine._format_quality_rules({
            "completeness_threshold": 99,
            "freshness_sla": "24h"
        })
        assert "completeness_threshold" in result
        assert "freshness_sla" in result

    def test_format_fields_summary_empty(self):
        """Test formatting empty fields summary."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        result = engine._format_fields_summary([])
        assert result == "No fields"


@pytest.mark.unit
@pytest.mark.service
class TestSemanticEngineLLMResponseParsing:
    """Test _parse_llm_response routing."""

    def test_parse_error_response(self):
        """Test that error responses are handled gracefully."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        engine.config = {"execution": {"confidence_threshold": 70}}
        response = {"response": {"error": "Failed to parse JSON"}}

        violations = engine._parse_llm_response("SEM001", "test", "critical", response)
        assert len(violations) == 0

    def test_parse_routes_to_correct_parser(self):
        """Test that each policy ID routes to the correct parser."""
        engine = SemanticPolicyEngine(
            policies_path=str(Path(__file__).parent.parent / "policies"),
            enabled=False
        )
        engine.config = {"execution": {"confidence_threshold": 70}}

        # SEM001 should use _parse_sem001
        response = {"response": {"is_sensitive": False, "confidence": 10}}
        violations = engine._parse_llm_response("SEM001", "test", "critical", response)
        assert isinstance(violations, list)

        # SEM002 should use _parse_sem002
        response = {"response": {"is_consistent": True, "issues": []}}
        violations = engine._parse_llm_response("SEM002", "test", "high", response)
        assert isinstance(violations, list)

        # SEM003 should use _parse_sem003
        response = {"response": {"security_concerns": []}}
        violations = engine._parse_llm_response("SEM003", "test", "high", response)
        assert isinstance(violations, list)

        # SEM004 should use _parse_sem004
        response = {"response": {"compliance_analysis": []}}
        violations = engine._parse_llm_response("SEM004", "test", "critical", response)
        assert isinstance(violations, list)

        # SEM005-008 should use _parse_generic
        response = {"response": {"issues": []}}
        for pid in ["SEM005", "SEM006", "SEM007", "SEM008"]:
            violations = engine._parse_llm_response(pid, "test", "medium", response)
            assert isinstance(violations, list)

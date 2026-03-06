"""
API endpoint tests for semantic scanning routes.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock

from app.services.semantic_policy_engine import SemanticPolicyEngine
from app.services.ollama_client import OllamaClient, OllamaError
from app.schemas.contract import ValidationStatus, ValidationResult, ViolationType, Violation
from app.models.contract import Contract


@pytest.mark.api
class TestSemanticHealthEndpoint:
    """Test GET /api/v1/semantic/health."""

    @patch("app.api.semantic.settings", Mock(ENABLE_LLM_VALIDATION=True))
    @patch("app.api.semantic.SemanticPolicyEngine")
    def test_semantic_health_available(self, mock_engine_cls, client):
        """Test health check when semantic scanning is available."""
        mock_engine = Mock()
        mock_engine.is_available.return_value = True
        mock_engine.llm_client = Mock()
        mock_engine.llm_client.is_available.return_value = True
        mock_engine.llm_client.list_models.return_value = ["mistral:7b"]
        mock_engine.llm_client.model = "mistral:7b"
        mock_engine.policies = {"policies": [{"id": "SEM001"}, {"id": "SEM002"}]}
        mock_engine_cls.return_value = mock_engine

        response = client.get("/api/v1/semantic/health")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True
        assert data["ollama_running"] is True
        assert "mistral:7b" in data["available_models"]
        assert data["policies_loaded"] == 2

    @patch("app.api.semantic.SemanticPolicyEngine")
    def test_semantic_health_unavailable(self, mock_engine_cls, client):
        """Test health check when Ollama is not running."""
        mock_engine = Mock()
        mock_engine.is_available.return_value = False
        mock_engine.llm_client = Mock()
        mock_engine.llm_client.is_available.return_value = False
        mock_engine.policies = {"policies": []}
        mock_engine_cls.return_value = mock_engine

        response = client.get("/api/v1/semantic/health")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False

    @patch("app.api.semantic.settings", Mock(ENABLE_LLM_VALIDATION=True))
    @patch("app.api.semantic.SemanticPolicyEngine")
    def test_semantic_health_exception(self, mock_engine_cls, client):
        """Test health check graceful error handling."""
        mock_engine_cls.side_effect = Exception("Init failed")

        response = client.get("/api/v1/semantic/health")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert "Error" in data["message"]


@pytest.mark.api
class TestSemanticPoliciesEndpoint:
    """Test GET /api/v1/semantic/policies."""

    @patch("app.api.semantic.SemanticPolicyEngine")
    def test_semantic_policies_list(self, mock_engine_cls, client):
        """Test listing semantic policies."""
        mock_engine = Mock()
        mock_engine.policies = {
            "policies": [
                {"id": "SEM001", "name": "sensitive_data", "severity": "critical",
                 "description": "Detect sensitive data patterns"},
                {"id": "SEM002", "name": "consistency", "severity": "high",
                 "description": "Check business logic consistency"}
            ]
        }
        mock_engine_cls.return_value = mock_engine

        response = client.get("/api/v1/semantic/policies")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["policies"]) == 2
        assert data["policies"][0]["id"] == "SEM001"

    @patch("app.api.semantic.SemanticPolicyEngine")
    def test_semantic_policies_empty(self, mock_engine_cls, client):
        """Test listing when no policies are loaded."""
        mock_engine = Mock()
        mock_engine.policies = {"policies": []}
        mock_engine_cls.return_value = mock_engine

        response = client.get("/api/v1/semantic/policies")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["policies"] == []


@pytest.mark.api
class TestSemanticValidateEndpoint:
    """Test POST /api/v1/semantic/validate."""

    @patch("app.api.semantic.SemanticPolicyEngine")
    def test_semantic_validate_contract_not_found(self, mock_engine_cls, client):
        """Test validation with non-existent contract returns 404."""
        response = client.post("/api/v1/semantic/validate", json={
            "contract_id": 99999
        })
        assert response.status_code == 404

    @patch("app.api.semantic.SemanticPolicyEngine")
    def test_semantic_validate_not_available(self, mock_engine_cls, client, db, sample_dataset):
        """Test validation when semantic engine not available returns 503."""
        # Create a contract
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={"dataset": {"name": "test"}, "schema": []},
            schema_hash="abc",
            governance_rules={},
            validation_status="passed"
        )
        db.add(contract)
        db.commit()

        mock_engine = Mock()
        mock_engine.is_available.return_value = False
        mock_engine_cls.return_value = mock_engine

        response = client.post("/api/v1/semantic/validate", json={
            "contract_id": contract.id
        })
        assert response.status_code == 503

    @patch("app.api.semantic.SemanticPolicyEngine")
    def test_semantic_validate_success(self, mock_engine_cls, client, db, sample_dataset):
        """Test successful semantic validation."""
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={
                "dataset": {"name": "test"},
                "schema": [{"name": "id", "type": "integer", "pii": False}],
                "governance": {"classification": "internal"},
                "quality_rules": {}
            },
            schema_hash="abc",
            governance_rules={},
            validation_status="passed"
        )
        db.add(contract)
        db.commit()

        mock_engine = Mock()
        mock_engine.is_available.return_value = True
        mock_engine.validate_contract.return_value = ValidationResult(
            status=ValidationStatus.PASSED,
            passed=5,
            warnings=0,
            failures=0,
            violations=[]
        )
        mock_engine_cls.return_value = mock_engine

        response = client.post("/api/v1/semantic/validate", json={
            "contract_id": contract.id
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "passed"
        assert data["passed"] == 5

    @patch("app.api.semantic.SemanticPolicyEngine")
    def test_semantic_validate_with_selected_policies(self, mock_engine_cls, client, db, sample_dataset):
        """Test validation with specific policy selection."""
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={"dataset": {"name": "test"}, "schema": [], "governance": {}, "quality_rules": {}},
            schema_hash="abc",
            governance_rules={},
            validation_status="passed"
        )
        db.add(contract)
        db.commit()

        mock_engine = Mock()
        mock_engine.is_available.return_value = True
        mock_engine.validate_contract.return_value = ValidationResult(
            status=ValidationStatus.PASSED, passed=1, warnings=0, failures=0, violations=[]
        )
        mock_engine_cls.return_value = mock_engine

        response = client.post("/api/v1/semantic/validate", json={
            "contract_id": contract.id,
            "selected_policies": ["SEM001"]
        })
        assert response.status_code == 200

        # Verify selected_policies was passed
        mock_engine.validate_contract.assert_called_once()
        call_kwargs = mock_engine.validate_contract.call_args
        assert call_kwargs[1]["selected_policies"] == ["SEM001"]


@pytest.mark.api
class TestSemanticModelsEndpoint:
    """Test GET /api/v1/semantic/models."""

    @patch("app.api.semantic.settings", Mock(ENABLE_LLM_VALIDATION=True))
    @patch("app.api.semantic.get_ollama_client")
    def test_list_models_success(self, mock_factory, client):
        """Test listing available Ollama models."""
        mock_client = Mock()
        mock_client.is_available.return_value = True
        mock_client.list_models.return_value = ["mistral:7b", "llama2:7b"]
        mock_client.model = "mistral:7b"
        mock_factory.return_value = mock_client

        response = client.get("/api/v1/semantic/models")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["current_model"] == "mistral:7b"
        assert "recommended_models" in data

    @patch("app.api.semantic.settings", Mock(ENABLE_LLM_VALIDATION=True))
    @patch("app.api.semantic.get_ollama_client")
    def test_list_models_ollama_down(self, mock_factory, client):
        """Test listing models when Ollama is not running."""
        mock_client = Mock()
        mock_client.is_available.return_value = False
        mock_factory.return_value = mock_client

        response = client.get("/api/v1/semantic/models")
        assert response.status_code == 503


@pytest.mark.api
class TestLLMValidationDisabled:
    """Test semantic endpoints when ENABLE_LLM_VALIDATION is False (default)."""

    def test_health_returns_disabled_message(self, client):
        """Health endpoint returns disabled status when LLM validation is off."""
        response = client.get("/api/v1/semantic/health")
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
        assert data["current_model"] == "disabled"
        assert data["policies_loaded"] == 0
        assert "disabled by configuration" in data["message"]
        assert "ENABLE_LLM_VALIDATION" in data["message"]

    def test_models_returns_disabled_message(self, client):
        """Models endpoint returns empty list when LLM validation is off."""
        response = client.get("/api/v1/semantic/models")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["current_model"] == "disabled"
        assert data["models"] == []
        assert "disabled by configuration" in data["message"]

    def test_pull_model_returns_disabled_message(self, client):
        """Pull model endpoint returns disabled message when LLM validation is off."""
        response = client.post("/api/v1/semantic/models/pull/mistral:7b")
        assert response.status_code == 200
        data = response.json()
        assert "disabled by configuration" in data["message"]
        assert data["model"] == "mistral:7b"
        assert "ENABLE_LLM_VALIDATION" in data["note"]

    def test_validate_returns_503_when_disabled(self, client, db, sample_dataset):
        """Validate endpoint returns 503 when LLM validation is disabled."""
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Test",
            machine_readable={"dataset": {"name": "test"}, "schema": []},
            schema_hash="test",
            governance_rules={},
            validation_status="passed"
        )
        db.add(contract)
        db.commit()

        response = client.post("/api/v1/semantic/validate", json={
            "contract_id": contract.id
        })
        assert response.status_code == 503

    def test_policies_list_works_regardless_of_flag(self, client):
        """Policies listing works even when LLM validation is disabled."""
        response = client.get("/api/v1/semantic/policies")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "policies" in data
        # Policies should still be listed (they come from YAML, not Ollama)

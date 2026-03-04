"""
API endpoint tests for orchestration routes.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock

from app.services.policy_orchestrator import (
    PolicyOrchestrator,
    ValidationStrategy,
    RiskLevel,
    ContractAnalysis,
    OrchestrationDecision,
)
from app.schemas.contract import ValidationStatus, ValidationResult, ViolationType, Violation
from app.models.contract import Contract


@pytest.mark.api
class TestOrchestrationStrategiesEndpoint:
    """Test GET /api/v1/orchestration/strategies."""

    def test_list_strategies(self, client):
        """Test listing all validation strategies."""
        response = client.get("/api/v1/orchestration/strategies")
        assert response.status_code == 200
        data = response.json()
        assert "strategies" in data
        assert len(data["strategies"]) == 4

        strategy_names = [s["name"] for s in data["strategies"]]
        assert "FAST" in strategy_names
        assert "BALANCED" in strategy_names
        assert "THOROUGH" in strategy_names
        assert "ADAPTIVE" in strategy_names

        assert data["default"] == "ADAPTIVE"


@pytest.mark.api
class TestOrchestrationAnalyzeEndpoint:
    """Test POST /api/v1/orchestration/analyze."""

    @patch("app.api.orchestration.PolicyOrchestrator")
    def test_analyze_contract_success(self, mock_orch_cls, client, db, sample_dataset):
        """Test successful contract analysis."""
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={
                "dataset": {"name": "test"},
                "schema": [{"name": "email", "type": "string", "pii": True}],
                "governance": {
                    "classification": "confidential",
                    "compliance_tags": ["GDPR"]
                }
            },
            schema_hash="abc",
            governance_rules={},
            validation_status="passed"
        )
        db.add(contract)
        db.commit()

        mock_orch = Mock()
        mock_orch._analyze_contract.return_value = ContractAnalysis(
            risk_level=RiskLevel.HIGH,
            has_pii=True,
            has_sensitive_data=True,
            classification="confidential",
            complexity_score=65,
            requires_compliance=True,
            compliance_frameworks=["GDPR"],
            field_count=1,
            concerns=["Contains PII", "GDPR compliance required"]
        )
        mock_orch.get_recommended_strategy.return_value = (
            ValidationStrategy.THOROUGH,
            "High risk contract with PII and GDPR compliance"
        )
        mock_orch_cls.return_value = mock_orch

        response = client.post("/api/v1/orchestration/analyze", json={
            "contract_id": contract.id
        })
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"].upper() == "HIGH"
        assert data["has_pii"] is True
        assert data["classification"] == "confidential"
        assert data["recommended_strategy"].upper() == "THOROUGH"

    def test_analyze_contract_not_found(self, client):
        """Test analysis of non-existent contract returns 404."""
        response = client.post("/api/v1/orchestration/analyze", json={
            "contract_id": 99999
        })
        assert response.status_code == 404

    @patch("app.api.orchestration.PolicyOrchestrator")
    def test_analyze_empty_contract(self, mock_orch_cls, client, db, sample_dataset):
        """Test analysis of a simple, low-risk contract."""
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={
                "dataset": {"name": "simple"},
                "schema": [{"name": "id", "type": "integer", "pii": False}],
                "governance": {"classification": "public", "compliance_tags": []}
            },
            schema_hash="abc",
            governance_rules={},
            validation_status="passed"
        )
        db.add(contract)
        db.commit()

        mock_orch = Mock()
        mock_orch._analyze_contract.return_value = ContractAnalysis(
            risk_level=RiskLevel.LOW,
            has_pii=False,
            has_sensitive_data=False,
            classification="public",
            complexity_score=10,
            requires_compliance=False,
            compliance_frameworks=[],
            field_count=1,
            concerns=[]
        )
        mock_orch.get_recommended_strategy.return_value = (
            ValidationStrategy.FAST,
            "Low risk contract"
        )
        mock_orch_cls.return_value = mock_orch

        response = client.post("/api/v1/orchestration/analyze", json={
            "contract_id": contract.id
        })
        assert response.status_code == 200
        data = response.json()
        assert data["risk_level"].upper() == "LOW"
        assert data["complexity_score"] == 10
        assert data["recommended_strategy"].upper() == "FAST"


@pytest.mark.api
class TestOrchestrationValidateEndpoint:
    """Test POST /api/v1/orchestration/validate."""

    @patch("app.api.orchestration.PolicyOrchestrator")
    def test_validate_fast_strategy(self, mock_orch_cls, client, db, sample_dataset):
        """Test validation with FAST strategy."""
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={
                "dataset": {"name": "test", "owner_name": "Owner", "owner_email": "o@e.com"},
                "schema": [{"name": "id", "type": "integer", "pii": False, "description": "ID"}],
                "governance": {"classification": "internal"}
            },
            schema_hash="abc",
            governance_rules={},
            validation_status="passed"
        )
        db.add(contract)
        db.commit()

        mock_orch = Mock()
        mock_orch.validate_contract.return_value = ValidationResult(
            status=ValidationStatus.PASSED,
            passed=10,
            warnings=0,
            failures=0,
            violations=[],
            metadata={"strategy": "fast", "risk_level": "LOW"}
        )
        mock_orch_cls.return_value = mock_orch

        response = client.post("/api/v1/orchestration/validate", json={
            "contract_id": contract.id,
            "strategy": "fast"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "passed"
        assert data["passed"] == 10

    def test_validate_contract_not_found(self, client):
        """Test validation with non-existent contract returns 404."""
        response = client.post("/api/v1/orchestration/validate", json={
            "contract_id": 99999,
            "strategy": "fast"
        })
        assert response.status_code == 404

    @patch("app.api.orchestration.PolicyOrchestrator")
    def test_validate_with_violations(self, mock_orch_cls, client, db, sample_dataset):
        """Test validation that returns violations."""
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={
                "dataset": {"name": "test"},
                "schema": [{"name": "ssn", "type": "string", "pii": True}],
                "governance": {"classification": "confidential", "encryption_required": False}
            },
            schema_hash="abc",
            governance_rules={},
            validation_status="failed"
        )
        db.add(contract)
        db.commit()

        mock_orch = Mock()
        mock_orch.validate_contract.return_value = ValidationResult(
            status=ValidationStatus.FAILED,
            passed=5,
            warnings=1,
            failures=2,
            violations=[
                Violation(
                    type=ViolationType.CRITICAL,
                    policy="SD001",
                    field="ssn",
                    message="PII field without encryption",
                    remediation="Enable AES-256 encryption"
                )
            ]
        )
        mock_orch_cls.return_value = mock_orch

        response = client.post("/api/v1/orchestration/validate", json={
            "contract_id": contract.id,
            "strategy": "thorough"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["failures"] == 2
        assert len(data["violations"]) == 1
        assert data["violations"][0]["policy"] == "SD001"


@pytest.mark.api
class TestOrchestrationRecommendEndpoint:
    """Test POST /api/v1/orchestration/recommend-strategy."""

    @patch("app.api.orchestration.PolicyOrchestrator")
    def test_recommend_strategy(self, mock_orch_cls, client, db, sample_dataset):
        """Test strategy recommendation endpoint."""
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={
                "dataset": {"name": "test"},
                "schema": [{"name": "id", "type": "integer", "pii": False}],
                "governance": {"classification": "internal"}
            },
            schema_hash="abc",
            governance_rules={},
            validation_status="passed"
        )
        db.add(contract)
        db.commit()

        mock_orch = Mock()
        mock_orch.get_recommended_strategy.return_value = (
            ValidationStrategy.FAST,
            "Low risk, simple schema"
        )
        mock_orch._analyze_contract.return_value = ContractAnalysis(
            risk_level=RiskLevel.LOW,
            has_pii=False,
            has_sensitive_data=False,
            classification="internal",
            complexity_score=15,
            requires_compliance=False,
            compliance_frameworks=[],
            field_count=1,
            concerns=[]
        )
        mock_orch._make_orchestration_decision.return_value = OrchestrationDecision(
            strategy=ValidationStrategy.FAST,
            use_rule_based=True,
            use_semantic=False,
            semantic_policies=None,
            estimated_time_seconds=0.05,
            reasoning="Low risk contract"
        )
        mock_orch_cls.return_value = mock_orch

        response = client.post("/api/v1/orchestration/recommend-strategy", json={
            "contract_id": contract.id
        })
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_strategy"].upper() == "FAST"
        assert data["will_use_rule_based"] is True
        assert data["will_use_semantic"] is False

    def test_recommend_strategy_not_found(self, client):
        """Test recommendation for non-existent contract returns 404."""
        response = client.post("/api/v1/orchestration/recommend-strategy", json={
            "contract_id": 99999
        })
        assert response.status_code == 404


@pytest.mark.api
class TestOrchestrationStatsEndpoint:
    """Test GET /api/v1/orchestration/stats."""

    @patch("app.api.orchestration.PolicyOrchestrator")
    def test_get_stats(self, mock_orch_cls, client):
        """Test orchestration stats endpoint."""
        mock_orch = Mock()
        mock_orch.semantic_engine.is_available.return_value = False
        mock_orch.rule_engine._get_all_policy_ids.return_value = [f"SD{i:03d}" for i in range(1, 6)]
        mock_orch.semantic_engine.policies = {"policies": [{"id": f"SEM{i:03d}"} for i in range(1, 9)]}
        mock_orch_cls.return_value = mock_orch

        response = client.get("/api/v1/orchestration/stats")
        assert response.status_code == 200
        data = response.json()
        assert "engines" in data
        assert "strategies" in data
        assert data["engines"]["rule_based"]["available"] is True
        assert data["total_policies"] >= 5

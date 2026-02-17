"""
Tests for policy orchestration engine.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from app.services.policy_orchestrator import (
    PolicyOrchestrator,
    ValidationStrategy,
    RiskLevel,
    ContractAnalysis,
    OrchestrationDecision
)
from app.schemas.contract import ValidationStatus, ViolationType, Violation


class TestContractAnalysis:
    """Test contract analysis functionality."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator instance."""
        return PolicyOrchestrator(enable_semantic=False)

    @pytest.fixture
    def simple_contract(self):
        """Simple, low-risk contract."""
        return {
            'dataset': {'name': 'simple_data'},
            'schema': [
                {'name': 'id', 'type': 'integer', 'pii': False},
                {'name': 'count', 'type': 'integer', 'pii': False}
            ],
            'governance': {
                'classification': 'internal',
                'compliance_tags': []
            }
        }

    @pytest.fixture
    def complex_pii_contract(self):
        """Complex contract with PII and compliance."""
        return {
            'dataset': {'name': 'customer_data'},
            'schema': [
                {'name': 'customer_id', 'type': 'integer', 'pii': False},
                {'name': 'ssn', 'type': 'string', 'pii': True},
                {'name': 'email', 'type': 'string', 'pii': True},
                {'name': 'phone', 'type': 'string', 'pii': True},
                {'name': 'address', 'type': 'string', 'pii': True},
                {'name': 'dob', 'type': 'date', 'pii': True}
            ],
            'governance': {
                'classification': 'confidential',
                'compliance_tags': ['GDPR', 'CCPA'],
                'encryption_required': True
            }
        }

    def test_analyze_simple_contract(self, orchestrator, simple_contract):
        """Test analysis of simple contract."""
        analysis = orchestrator._analyze_contract(simple_contract)

        assert analysis.risk_level == RiskLevel.LOW
        assert analysis.has_pii is False
        assert analysis.has_sensitive_data is False
        assert analysis.classification == 'internal'
        assert analysis.field_count == 2
        assert analysis.complexity_score < 30

    def test_analyze_complex_pii_contract(self, orchestrator, complex_pii_contract):
        """Test analysis of complex PII contract."""
        analysis = orchestrator._analyze_contract(complex_pii_contract)

        assert analysis.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert analysis.has_pii is True
        assert analysis.has_sensitive_data is True
        assert analysis.classification == 'confidential'
        assert analysis.requires_compliance is True
        assert 'GDPR' in analysis.compliance_frameworks
        assert analysis.field_count == 6
        assert analysis.complexity_score > 50

    def test_complexity_calculation(self, orchestrator):
        """Test complexity score calculation."""
        # High complexity contract
        complex_contract = {
            'dataset': {'name': 'complex'},
            'schema': [
                {'name': f'field_{i}', 'type': 'string', 'pii': i < 5}
                for i in range(25)  # 25 fields, 5 PII
            ],
            'governance': {
                'classification': 'restricted',
                'compliance_tags': ['GDPR', 'HIPAA', 'PCI-DSS']
            }
        }

        analysis = orchestrator._analyze_contract(complex_contract)
        assert analysis.complexity_score >= 70


class TestValidationStrategies:
    """Test validation strategy selection."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator with mocked engines."""
        return PolicyOrchestrator(enable_semantic=True)

    @pytest.fixture
    def low_risk_contract(self):
        """Low risk contract."""
        return {
            'dataset': {'name': 'simple'},
            'schema': [{'name': 'id', 'type': 'integer', 'pii': False}],
            'governance': {'classification': 'public', 'compliance_tags': []}
        }

    @pytest.fixture
    def high_risk_contract(self):
        """High risk contract."""
        return {
            'dataset': {'name': 'sensitive'},
            'schema': [
                {'name': 'ssn', 'type': 'string', 'pii': True},
                {'name': 'health_data', 'type': 'json', 'pii': True}
            ],
            'governance': {
                'classification': 'restricted',
                'compliance_tags': ['HIPAA', 'GDPR']
            }
        }

    def test_fast_strategy_decision(self, orchestrator, low_risk_contract):
        """Test FAST strategy decision."""
        analysis = orchestrator._analyze_contract(low_risk_contract)
        decision = orchestrator._fast_strategy_decision(analysis)

        assert decision.strategy == ValidationStrategy.FAST
        assert decision.use_rule_based is True
        assert decision.use_semantic is False
        assert decision.estimated_time_seconds < 1.0

    def test_balanced_strategy_decision(self, orchestrator, high_risk_contract):
        """Test BALANCED strategy decision."""
        analysis = orchestrator._analyze_contract(high_risk_contract)
        decision = orchestrator._balanced_strategy_decision(analysis)

        assert decision.strategy == ValidationStrategy.BALANCED
        assert decision.use_rule_based is True
        assert decision.use_semantic is True
        assert decision.semantic_policies is not None
        assert len(decision.semantic_policies) > 0

    def test_thorough_strategy_decision(self, orchestrator, high_risk_contract):
        """Test THOROUGH strategy decision."""
        analysis = orchestrator._analyze_contract(high_risk_contract)
        decision = orchestrator._thorough_strategy_decision(analysis)

        assert decision.strategy == ValidationStrategy.THOROUGH
        assert decision.use_rule_based is True
        assert decision.use_semantic is True
        assert decision.semantic_policies is None  # None means all policies
        assert decision.estimated_time_seconds > 10.0

    def test_adaptive_strategy_low_risk(self, orchestrator, low_risk_contract):
        """Test ADAPTIVE strategy with low risk contract."""
        analysis = orchestrator._analyze_contract(low_risk_contract)
        decision = orchestrator._adaptive_strategy_decision(analysis)

        # Should choose FAST for low risk
        assert decision.strategy == ValidationStrategy.FAST
        assert decision.use_semantic is False

    def test_adaptive_strategy_high_risk(self, orchestrator, high_risk_contract):
        """Test ADAPTIVE strategy with high risk contract."""
        analysis = orchestrator._analyze_contract(high_risk_contract)
        decision = orchestrator._adaptive_strategy_decision(analysis)

        # Should choose THOROUGH for high/critical risk
        assert decision.strategy == ValidationStrategy.THOROUGH
        assert decision.use_semantic is True


class TestOrchestration:
    """Test orchestration execution."""

    @pytest.fixture
    def sample_contract(self):
        """Sample contract for testing."""
        return {
            'dataset': {'name': 'test_data', 'owner_name': 'Test', 'owner_email': 'test@example.com'},
            'schema': [
                {'name': 'id', 'type': 'integer', 'pii': False, 'description': 'ID'},
                {'name': 'email', 'type': 'string', 'pii': True, 'description': 'Email'}
            ],
            'governance': {
                'classification': 'confidential',
                'compliance_tags': ['GDPR'],
                'encryption_required': True
            },
            'quality_rules': {}
        }

    @patch('app.services.policy_orchestrator.SemanticPolicyEngine')
    @patch('app.services.policy_orchestrator.PolicyEngine')
    def test_orchestration_fast_strategy(self, mock_policy_engine, mock_semantic_engine, sample_contract):
        """Test orchestration with FAST strategy."""
        # Mock rule engine
        mock_rule_instance = Mock()
        mock_rule_instance.validate_contract.return_value = Mock(
            status=ValidationStatus.PASSED,
            violations=[],
            passed=10,
            warnings=0,
            failures=0
        )
        mock_policy_engine.return_value = mock_rule_instance

        # Mock semantic engine as unavailable
        mock_sem_instance = Mock()
        mock_sem_instance.is_available.return_value = False
        mock_semantic_engine.return_value = mock_sem_instance

        orchestrator = PolicyOrchestrator(enable_semantic=False)
        result = orchestrator.validate_contract(sample_contract, strategy=ValidationStrategy.FAST)

        # Should only call rule engine
        assert mock_rule_instance.validate_contract.called
        assert not mock_sem_instance.validate_contract.called
        assert result.status == ValidationStatus.PASSED

    def test_balanced_policy_selection(self):
        """Test that BALANCED strategy selects appropriate semantic policies."""
        orchestrator = PolicyOrchestrator(enable_semantic=True)

        # Contract with PII and compliance
        contract = {
            'dataset': {'name': 'data'},
            'schema': [{'name': 'ssn', 'type': 'string', 'pii': True}],
            'governance': {
                'classification': 'confidential',
                'compliance_tags': ['GDPR']
            }
        }

        analysis = orchestrator._analyze_contract(contract)
        decision = orchestrator._balanced_strategy_decision(analysis)

        # Should include SEM001 (sensitive data) and SEM004 (compliance)
        assert 'SEM001' in decision.semantic_policies
        assert 'SEM004' in decision.semantic_policies

    def test_risk_level_assessment(self):
        """Test risk level assessment logic."""
        orchestrator = PolicyOrchestrator(enable_semantic=False)

        # Test CRITICAL: restricted classification
        assert orchestrator._assess_risk_level(
            has_pii=True,
            classification='restricted',
            compliance_tags=['GDPR'],
            field_count=10,
            complexity_score=50
        ) == RiskLevel.CRITICAL

        # Test HIGH: confidential + PII
        assert orchestrator._assess_risk_level(
            has_pii=True,
            classification='confidential',
            compliance_tags=['GDPR'],
            field_count=10,
            complexity_score=50
        ) == RiskLevel.HIGH

        # Test MEDIUM: PII but internal
        assert orchestrator._assess_risk_level(
            has_pii=True,
            classification='internal',
            compliance_tags=[],
            field_count=10,
            complexity_score=30
        ) == RiskLevel.MEDIUM

        # Test LOW: simple data
        assert orchestrator._assess_risk_level(
            has_pii=False,
            classification='internal',
            compliance_tags=[],
            field_count=5,
            complexity_score=20
        ) == RiskLevel.LOW

    def test_violation_prioritization(self):
        """Test that violations are prioritized correctly."""
        orchestrator = PolicyOrchestrator(enable_semantic=False)

        violations = [
            Violation(
                type=ViolationType.WARNING,
                policy="WARN001",
                field="field1",
                message="Warning",
                remediation="Fix"
            ),
            Violation(
                type=ViolationType.CRITICAL,
                policy="CRIT001",
                field="field2",
                message="Critical issue",
                remediation="Fix now"
            ),
            Violation(
                type=ViolationType.INFO,
                policy="INFO001",
                field="field3",
                message="Info",
                remediation="Optional"
            )
        ]

        analysis = ContractAnalysis(
            risk_level=RiskLevel.HIGH,
            has_pii=True,
            has_sensitive_data=True,
            classification='confidential',
            complexity_score=60,
            requires_compliance=True,
            compliance_frameworks=['GDPR'],
            field_count=10,
            concerns=[]
        )

        prioritized = orchestrator._prioritize_violations(violations, analysis)

        # Critical should be first
        assert prioritized[0].type == ViolationType.CRITICAL
        # Info should be last
        assert prioritized[-1].type == ViolationType.INFO


class TestRecommendations:
    """Test strategy recommendation logic."""

    def test_get_recommended_strategy(self):
        """Test strategy recommendation."""
        orchestrator = PolicyOrchestrator(enable_semantic=True)

        # Low risk contract
        simple_contract = {
            'dataset': {'name': 'simple'},
            'schema': [{'name': 'count', 'type': 'integer', 'pii': False}],
            'governance': {'classification': 'internal', 'compliance_tags': []}
        }

        strategy, reasoning = orchestrator.get_recommended_strategy(simple_contract)

        assert strategy == ValidationStrategy.FAST
        assert 'low risk' in reasoning.lower() or 'fast' in reasoning.lower()

    def test_recommendation_metadata(self):
        """Test that orchestration adds metadata to results."""
        orchestrator = PolicyOrchestrator(enable_semantic=False)

        contract = {
            'dataset': {'name': 'test', 'owner_name': 'Test', 'owner_email': 'test@test.com'},
            'schema': [{'name': 'id', 'type': 'integer', 'pii': False, 'description': 'ID'}],
            'governance': {'classification': 'internal'}
        }

        result = orchestrator.validate_contract(contract, strategy=ValidationStrategy.FAST)

        # Should have metadata
        assert hasattr(result, 'metadata')
        assert result.metadata is not None
        assert 'strategy' in result.metadata
        assert 'risk_level' in result.metadata
        assert 'complexity_score' in result.metadata

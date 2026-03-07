"""
Advanced tests for PolicyOrchestrator focusing on:
- _combine_results: all branches including deduplication and stats summation
- _are_violations_similar: boundary conditions
- _prioritize_violations: sort ordering and relevance boosts
- _execute_validation: exception handling (semantic engine failure)
- _adaptive_strategy_decision: all risk-level paths
"""

import pytest
from unittest.mock import MagicMock, patch

from app.services.policy_orchestrator import (
    PolicyOrchestrator,
    ValidationStrategy,
    RiskLevel,
    ContractAnalysis,
)
from app.schemas.contract import (
    ValidationResult,
    Violation,
    ViolationType,
    ValidationStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _violation(type_: ViolationType, policy: str, field: str, message: str = "test message") -> Violation:
    return Violation(type=type_, policy=policy, field=field, message=message, remediation="fix it")


def _result(
    violations: list,
    passed: int = 5,
    warnings: int = 0,
    failures: int = 0,
    status: ValidationStatus = None,
) -> ValidationResult:
    if status is None:
        if failures > 0:
            status = ValidationStatus.FAILED
        elif warnings > 0:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASSED
    return ValidationResult(
        status=status,
        passed=passed,
        warnings=warnings,
        failures=failures,
        violations=violations,
    )


def _analysis(
    has_pii: bool = False,
    requires_compliance: bool = False,
    complexity_score: int = 20,
    risk_level: RiskLevel = RiskLevel.LOW,
    classification: str = "internal",
) -> ContractAnalysis:
    return ContractAnalysis(
        risk_level=risk_level,
        has_pii=has_pii,
        has_sensitive_data=has_pii,
        classification=classification,
        complexity_score=complexity_score,
        requires_compliance=requires_compliance,
        compliance_frameworks=["GDPR"] if requires_compliance else [],
        field_count=3,
        concerns=[],
    )


def _make_orchestrator() -> PolicyOrchestrator:
    """Return an orchestrator with semantic engine mocked away (not available)."""
    with patch("app.services.policy_orchestrator.SemanticPolicyEngine") as MockSem:
        mock_sem = MockSem.return_value
        mock_sem.is_available.return_value = False
        return PolicyOrchestrator(enable_semantic=False)


# ---------------------------------------------------------------------------
# _combine_results: return-value selection
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestCombineResultsReturnSelection:
    """When only one engine produces a result, it is returned unchanged."""

    def setup_method(self):
        self.orch = _make_orchestrator()

    def test_rule_only_returns_rule_result_directly(self):
        rule_result = _result([_violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "email")], failures=1)
        analysis = _analysis()
        result = self.orch._combine_results(rule_result, None, analysis)
        assert result is rule_result

    def test_semantic_only_returns_semantic_result_directly(self):
        sem_result = _result([_violation(ViolationType.WARNING, "SEM001: sensitive_data_context", "email")], warnings=1)
        analysis = _analysis()
        result = self.orch._combine_results(None, sem_result, analysis)
        assert result is sem_result


# ---------------------------------------------------------------------------
# _combine_results: merged stats
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestCombineResultsStats:
    """Verify that passed/warnings/failures are summed across both engines."""

    def setup_method(self):
        self.orch = _make_orchestrator()

    def test_passed_count_is_summed(self):
        rule = _result([], passed=10, warnings=0, failures=0)
        sem = _result([], passed=8, warnings=0, failures=0)
        result = self.orch._combine_results(rule, sem, _analysis())
        assert result.passed == 18

    def test_warnings_count_is_summed(self):
        rule = _result(
            [_violation(ViolationType.WARNING, "SG001: field_docs", "x")],
            passed=10, warnings=1, failures=0,
        )
        sem = _result(
            [_violation(ViolationType.WARNING, "SEM002: business_logic", "y")],
            passed=5, warnings=1, failures=0,
        )
        result = self.orch._combine_results(rule, sem, _analysis())
        assert result.warnings == 2
        assert result.failures == 0

    def test_failures_count_is_summed(self):
        rule = _result(
            [_violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "ssn")],
            passed=10, warnings=0, failures=1,
        )
        sem = _result(
            [_violation(ViolationType.CRITICAL, "SEM003: security_pattern", "card")],
            passed=5, warnings=0, failures=1,
        )
        result = self.orch._combine_results(rule, sem, _analysis())
        assert result.failures == 2

    def test_all_counts_zero_gives_passed_status(self):
        rule = _result([], passed=17, warnings=0, failures=0)
        sem = _result([], passed=8, warnings=0, failures=0)
        result = self.orch._combine_results(rule, sem, _analysis())
        assert result.status == ValidationStatus.PASSED
        assert result.failures == 0
        assert result.warnings == 0

    def test_failures_plus_warnings_gives_failed_status(self):
        rule = _result(
            [_violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "email")],
            failures=1,
        )
        sem = _result(
            [_violation(ViolationType.WARNING, "SEM002: business_logic_consistency", "amount")],
            warnings=1,
        )
        result = self.orch._combine_results(rule, sem, _analysis())
        assert result.status == ValidationStatus.FAILED  # failures take precedence

    def test_warnings_only_gives_warning_status(self):
        rule = _result(
            [_violation(ViolationType.WARNING, "SG001: field_docs", "name")],
            warnings=1,
        )
        sem = _result([], warnings=0)
        result = self.orch._combine_results(rule, sem, _analysis())
        assert result.status == ValidationStatus.WARNING


# ---------------------------------------------------------------------------
# _combine_results: violation deduplication
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestCombineResultsDeduplication:
    """Semantic violations similar to rule violations should be dropped."""

    def setup_method(self):
        self.orch = _make_orchestrator()

    def test_pii_and_sensitive_same_field_deduplicated(self):
        rule_v = _violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "email")
        sem_v = _violation(ViolationType.WARNING, "SEM001: sensitive_data_context_detection", "email")
        rule = _result([rule_v], failures=1)
        sem = _result([sem_v], warnings=1)
        result = self.orch._combine_results(rule, sem, _analysis(has_pii=True))
        assert len(result.violations) == 1
        assert result.violations[0].policy == "SD001: pii_encryption_required"

    def test_encryption_keyword_both_policies_same_field_deduplicated(self):
        rule_v = _violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "ssn")
        sem_v = _violation(ViolationType.WARNING, "SEM003: encryption_verification", "ssn")
        rule = _result([rule_v], failures=1)
        sem = _result([sem_v], warnings=1)
        result = self.orch._combine_results(rule, sem, _analysis())
        assert len(result.violations) == 1

    def test_different_fields_not_deduplicated(self):
        rule_v = _violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "email")
        sem_v = _violation(ViolationType.WARNING, "SEM001: sensitive_data_context_detection", "phone")
        rule = _result([rule_v], failures=1)
        sem = _result([sem_v], warnings=1)
        result = self.orch._combine_results(rule, sem, _analysis(has_pii=True))
        assert len(result.violations) == 2

    def test_same_field_unrelated_policies_not_deduplicated(self):
        rule_v = _violation(ViolationType.CRITICAL, "SD002: retention_policy_required", "email")
        sem_v = _violation(ViolationType.WARNING, "SEM002: business_logic_consistency", "email")
        rule = _result([rule_v], failures=1)
        sem = _result([sem_v], warnings=1)
        result = self.orch._combine_results(rule, sem, _analysis())
        assert len(result.violations) == 2

    def test_multiple_sem_violations_some_deduplicated(self):
        rule_v = _violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "email")
        sem_dup = _violation(ViolationType.WARNING, "SEM001: sensitive_data_context_detection", "email")  # duplicate
        sem_unique = _violation(ViolationType.WARNING, "SEM002: business_logic_consistency", "amount")   # unique
        rule = _result([rule_v], failures=1)
        sem = _result([sem_dup, sem_unique], warnings=2)
        result = self.orch._combine_results(rule, sem, _analysis(has_pii=True))
        policies = [v.policy for v in result.violations]
        assert "SD001: pii_encryption_required" in policies
        assert "SEM002: business_logic_consistency" in policies
        assert "SEM001: sensitive_data_context_detection" not in policies
        assert len(result.violations) == 2

    def test_no_rule_violations_all_sem_violations_kept(self):
        sem_v1 = _violation(ViolationType.WARNING, "SEM001: sensitive_data_context", "email")
        sem_v2 = _violation(ViolationType.WARNING, "SEM002: business_logic", "amount")
        rule = _result([], passed=17, warnings=0, failures=0)
        sem = _result([sem_v1, sem_v2], warnings=2)
        result = self.orch._combine_results(rule, sem, _analysis())
        assert len(result.violations) == 2


# ---------------------------------------------------------------------------
# _are_violations_similar: boundary conditions
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestAreViolationsSimilar:
    """All boundary conditions for the similarity heuristic."""

    def setup_method(self):
        self.orch = _make_orchestrator()

    def test_pii_and_sensitive_same_field_is_similar(self):
        v1 = _violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "email")
        v2 = _violation(ViolationType.WARNING, "SEM001: sensitive_data_context_detection", "email")
        assert self.orch._are_violations_similar(v1, v2) is True

    def test_encryption_both_same_field_is_similar(self):
        v1 = _violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "ssn")
        v2 = _violation(ViolationType.WARNING, "SEM003: encryption_audit_check", "ssn")
        assert self.orch._are_violations_similar(v1, v2) is True

    def test_different_fields_not_similar(self):
        v1 = _violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "email")
        v2 = _violation(ViolationType.WARNING, "SEM001: sensitive_data_context_detection", "phone")
        assert self.orch._are_violations_similar(v1, v2) is False

    def test_same_field_no_keyword_match_not_similar(self):
        """Same field but neither 'pii'/'sensitive' nor 'encryption' keyword in policies."""
        v1 = _violation(ViolationType.CRITICAL, "SD002: retention_policy_required", "email")
        v2 = _violation(ViolationType.WARNING, "SEM002: business_logic_consistency", "email")
        assert self.orch._are_violations_similar(v1, v2) is False

    def test_pii_keyword_in_first_only_same_field_without_sensitive_in_second(self):
        """'pii' in v1, but v2 policy doesn't contain 'sensitive' → not similar."""
        v1 = _violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "email")
        v2 = _violation(ViolationType.WARNING, "SEM002: business_logic_consistency", "email")
        assert self.orch._are_violations_similar(v1, v2) is False

    def test_sensitive_keyword_in_second_only_without_pii_in_first(self):
        """'sensitive' in v2 policy, but v1 doesn't contain 'pii' → not similar."""
        v1 = _violation(ViolationType.CRITICAL, "SD002: retention_policy_required", "email")
        v2 = _violation(ViolationType.WARNING, "SEM001: sensitive_data_context_detection", "email")
        assert self.orch._are_violations_similar(v1, v2) is False

    def test_reversed_order_pii_sensitive_not_similar(self):
        """Similarity is directional: 'pii' must be in v1 and 'sensitive' in v2 (not reversed)."""
        v1 = _violation(ViolationType.WARNING, "SEM001: sensitive_data_context_detection", "email")  # sensitive in v1
        v2 = _violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "email")  # pii in v2
        # The check is: 'pii' in v1.policy AND 'sensitive' in v2.policy
        # With args reversed: 'pii' not in v1.policy ('sensitive_data_context') → False
        assert self.orch._are_violations_similar(v1, v2) is False


# ---------------------------------------------------------------------------
# _prioritize_violations: sort ordering
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestPrioritizeViolations:
    """Verify sort order and relevance boosts."""

    def setup_method(self):
        self.orch = _make_orchestrator()

    def test_critical_sorted_before_warning(self):
        warning = _violation(ViolationType.WARNING, "SG001: field_documentation_required", "name", "short")
        critical = _violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "email", "a longer message here")
        result = self.orch._prioritize_violations([warning, critical], _analysis())
        assert result[0].type == ViolationType.CRITICAL

    def test_empty_list_returns_empty(self):
        result = self.orch._prioritize_violations([], _analysis())
        assert result == []

    def test_single_violation_returned_unchanged(self):
        v = _violation(ViolationType.WARNING, "SG004: string_field_constraints", "name")
        result = self.orch._prioritize_violations([v], _analysis())
        assert len(result) == 1
        assert result[0] is v

    def test_pii_violation_boosted_for_pii_contract(self):
        """PII-related violation ranks above same-severity non-PII violation when contract has PII."""
        pii_v = _violation(ViolationType.CRITICAL, "SD001: pii_encryption_required", "email", "PII message longer")
        other_v = _violation(ViolationType.CRITICAL, "SD002: retention_policy_required", "retention", "Retention message")
        result = self.orch._prioritize_violations([other_v, pii_v], _analysis(has_pii=True))
        # pii_v has relevance_boost=-1 due to 'pii' in policy; other_v does not
        # After boost: pii_v priority tuple = (0-1=−1), other_v = (0, ...)
        # Sorted ascending → pii_v should come first
        assert "pii" in result[0].policy.lower()

    def test_compliance_violation_boosted_for_compliance_contract(self):
        """Compliance-related violation ranks above same-severity non-compliance when compliance required."""
        compliance_v = _violation(ViolationType.WARNING, "SEM004: compliance_intent_verification", "tags", "Compliance message longer")
        other_v = _violation(ViolationType.WARNING, "SG001: field_documentation_required", "name", "Doc message")
        result = self.orch._prioritize_violations([other_v, compliance_v], _analysis(requires_compliance=True))
        assert "compliance" in result[0].policy.lower()

    def test_all_same_type_sorted_by_message_length_then_policy(self):
        """When severity is equal and no relevance boost, longer messages rank before shorter ones."""
        short_msg = _violation(ViolationType.WARNING, "SG001: aaa_policy", "field_a", "short")
        long_msg = _violation(ViolationType.WARNING, "SG004: bbb_policy", "field_b", "a much longer message that gives detail")
        result = self.orch._prioritize_violations([short_msg, long_msg], _analysis())
        # Longer message → -len(message) is more negative → sorts first
        assert result[0].message == "a much longer message that gives detail"


# ---------------------------------------------------------------------------
# _execute_validation: exception handling
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestExecuteValidationExceptionHandling:
    """Semantic engine failures should not propagate; rule-based result is returned."""

    def test_semantic_exception_returns_rule_based_result(self):
        with patch("app.services.policy_orchestrator.SemanticPolicyEngine"):
            orch = PolicyOrchestrator(enable_semantic=True)
            orch.semantic_engine.is_available = MagicMock(return_value=True)
            orch.semantic_engine.validate_contract = MagicMock(
                side_effect=RuntimeError("Ollama connection refused")
            )

        contract = {
            "dataset": {"owner_name": "Alice", "owner_email": "alice@example.com"},
            "schema": [{"name": "amount", "type": "float", "description": "Amount", "required": True, "nullable": False}],
            "governance": {"classification": "internal"},
            "quality_rules": {},
        }

        from app.services.policy_orchestrator import OrchestrationDecision
        decision = OrchestrationDecision(
            strategy=ValidationStrategy.BALANCED,
            use_rule_based=True,
            use_semantic=True,
            semantic_policies=["SEM001"],
            reasoning="test",
            estimated_time_seconds=3.0,
        )
        analysis = _analysis()
        # Should NOT raise; semantic error is caught internally
        result = orch._execute_validation(contract, decision, analysis)
        assert result is not None
        assert hasattr(result, "status")

    def test_semantic_unavailable_uses_rule_based(self):
        """When semantic engine is not available, _make_orchestration_decision returns FAST."""
        with patch("app.services.policy_orchestrator.SemanticPolicyEngine") as MockSem:
            mock_sem = MockSem.return_value
            mock_sem.is_available.return_value = False
            orch = PolicyOrchestrator(enable_semantic=True)

        analysis = _analysis(has_pii=True, risk_level=RiskLevel.HIGH)
        decision = orch._make_orchestration_decision(analysis, ValidationStrategy.THOROUGH)
        assert decision.use_semantic is False
        assert decision.strategy == ValidationStrategy.FAST


# ---------------------------------------------------------------------------
# _adaptive_strategy_decision: all paths
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestAdaptiveStrategyDecision:
    """All risk-level / complexity paths of _adaptive_strategy_decision."""

    def setup_method(self):
        self.orch = _make_orchestrator()

    def test_critical_risk_uses_thorough(self):
        analysis = _analysis(risk_level=RiskLevel.CRITICAL, complexity_score=80)
        decision = self.orch._adaptive_strategy_decision(analysis)
        assert decision.strategy == ValidationStrategy.THOROUGH

    def test_high_risk_uses_thorough(self):
        analysis = _analysis(risk_level=RiskLevel.HIGH, complexity_score=60)
        decision = self.orch._adaptive_strategy_decision(analysis)
        assert decision.strategy == ValidationStrategy.THOROUGH

    def test_medium_risk_uses_balanced(self):
        analysis = _analysis(risk_level=RiskLevel.MEDIUM, complexity_score=30)
        decision = self.orch._adaptive_strategy_decision(analysis)
        assert decision.strategy == ValidationStrategy.BALANCED

    def test_low_risk_low_complexity_uses_fast(self):
        """LOW risk + complexity < 30 → FAST."""
        analysis = _analysis(risk_level=RiskLevel.LOW, complexity_score=10)
        decision = self.orch._adaptive_strategy_decision(analysis)
        assert decision.strategy == ValidationStrategy.FAST

    def test_low_risk_high_complexity_uses_balanced(self):
        """LOW risk + complexity >= 30 → BALANCED (not FAST)."""
        analysis = _analysis(risk_level=RiskLevel.LOW, complexity_score=35)
        decision = self.orch._adaptive_strategy_decision(analysis)
        assert decision.strategy == ValidationStrategy.BALANCED

    def test_low_risk_exactly_30_uses_balanced(self):
        """LOW risk + complexity == 30 → BALANCED (boundary: < 30 triggers FAST, = 30 uses BALANCED)."""
        analysis = _analysis(risk_level=RiskLevel.LOW, complexity_score=30)
        decision = self.orch._adaptive_strategy_decision(analysis)
        # complexity_score < 30 is False when score == 30, so not FAST → BALANCED
        assert decision.strategy == ValidationStrategy.BALANCED


# ---------------------------------------------------------------------------
# Metadata attachment in validate_contract
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestOrchestrationMetadata:
    """validate_contract attaches orchestration metadata to result."""

    def test_metadata_attached_after_validation(self):
        with patch("app.services.policy_orchestrator.SemanticPolicyEngine") as MockSem:
            mock_sem = MockSem.return_value
            mock_sem.is_available.return_value = False
            orch = PolicyOrchestrator(enable_semantic=False)

        contract = {
            "dataset": {"owner_name": "Alice", "owner_email": "alice@example.com"},
            "schema": [{"name": "amount", "type": "float", "description": "Amount", "required": True, "nullable": False}],
            "governance": {"classification": "internal"},
            "quality_rules": {},
        }
        result = orch.validate_contract(contract, strategy=ValidationStrategy.FAST)
        assert result.metadata is not None
        assert "strategy" in result.metadata
        assert "risk_level" in result.metadata
        assert "complexity_score" in result.metadata
        assert result.metadata["strategy"] == "fast"

"""
Policy Orchestration Engine - Intelligent routing between rule-based and LLM-based validation.

This orchestrator analyzes contracts and determines the optimal validation strategy,
deciding when to use rule-based policies, semantic (LLM) policies, or both.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from app.services.policy_engine import PolicyEngine
from app.services.semantic_policy_engine import SemanticPolicyEngine
from app.schemas.contract import ValidationResult, Violation, ValidationStatus, ViolationType

logger = logging.getLogger(__name__)


class ValidationStrategy(str, Enum):
    """Validation strategies with different trade-offs."""
    FAST = "fast"  # Rule-based only (fastest, good for low-risk)
    BALANCED = "balanced"  # Rule-based + targeted semantic (recommended)
    THOROUGH = "thorough"  # Full validation with all policies (slowest, most comprehensive)
    ADAPTIVE = "adaptive"  # Analyzes contract and chooses strategy (smart default)


class RiskLevel(str, Enum):
    """Contract risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class OrchestrationDecision:
    """Decision made by orchestrator about validation approach."""
    strategy: ValidationStrategy
    use_rule_based: bool
    use_semantic: bool
    semantic_policies: Optional[List[str]]
    reasoning: str
    estimated_time_seconds: float


@dataclass
class ContractAnalysis:
    """Analysis of contract characteristics for orchestration."""
    risk_level: RiskLevel
    has_pii: bool
    has_sensitive_data: bool
    classification: str
    complexity_score: int  # 0-100
    requires_compliance: bool
    compliance_frameworks: List[str]
    field_count: int
    concerns: List[str]


class PolicyOrchestrator:
    """
    Intelligent orchestrator that decides which validation engines to use.

    Analyzes contract characteristics and routes to appropriate validation
    engines (rule-based, semantic, or both) based on risk, complexity, and strategy.
    """

    def __init__(
        self,
        enable_semantic: bool = True,
        default_strategy: ValidationStrategy = ValidationStrategy.ADAPTIVE
    ):
        """
        Initialize PolicyOrchestrator.

        Args:
            enable_semantic: Whether semantic validation is available
            default_strategy: Default validation strategy to use
        """
        self.rule_engine = PolicyEngine()
        self.semantic_engine = SemanticPolicyEngine(enabled=enable_semantic)
        self.default_strategy = default_strategy
        self.enable_semantic = enable_semantic

    def validate_contract(
        self,
        contract_data: Dict[str, Any],
        strategy: Optional[ValidationStrategy] = None
    ) -> ValidationResult:
        """
        Validate contract using orchestrated approach.

        Args:
            contract_data: Contract data to validate
            strategy: Validation strategy (uses default if None)

        Returns:
            Combined ValidationResult
        """
        # Use default strategy if not specified
        strategy = strategy or self.default_strategy

        # Analyze contract
        analysis = self._analyze_contract(contract_data)
        logger.info(f"Contract analysis: risk={analysis.risk_level.value}, "
                   f"complexity={analysis.complexity_score}, "
                   f"fields={analysis.field_count}")

        # Make orchestration decision
        decision = self._make_orchestration_decision(analysis, strategy)
        logger.info(f"Orchestration decision: strategy={decision.strategy.value}, "
                   f"rule_based={decision.use_rule_based}, "
                   f"semantic={decision.use_semantic}, "
                   f"reasoning={decision.reasoning}")

        # Execute validation based on decision
        result = self._execute_validation(contract_data, decision, analysis)

        # Add orchestration metadata
        result.metadata = {
            "strategy": decision.strategy.value,
            "risk_level": analysis.risk_level.value,
            "complexity_score": analysis.complexity_score,
            "orchestration_reasoning": decision.reasoning,
            "estimated_time": decision.estimated_time_seconds
        }

        return result

    def _analyze_contract(self, contract_data: Dict[str, Any]) -> ContractAnalysis:
        """
        Analyze contract to determine characteristics for orchestration.

        Args:
            contract_data: Contract data

        Returns:
            ContractAnalysis with risk assessment
        """
        dataset = contract_data.get('dataset', {})
        schema = contract_data.get('schema', [])
        governance = contract_data.get('governance', {})

        # Basic metrics
        field_count = len(schema)
        has_pii = any(field.get('pii', False) for field in schema)
        classification = governance.get('classification', 'internal')
        compliance_tags = governance.get('compliance_tags', [])

        # Determine if sensitive
        has_sensitive_data = (
            has_pii or
            classification in ['confidential', 'restricted'] or
            len(compliance_tags) > 0
        )

        # Calculate complexity score (0-100)
        complexity_score = self._calculate_complexity(schema, governance)

        # Assess risk level
        risk_level = self._assess_risk_level(
            has_pii, classification, compliance_tags, field_count, complexity_score
        )

        # Identify concerns
        concerns = []
        if has_pii:
            concerns.append("Contains PII")
        if classification in ['confidential', 'restricted']:
            concerns.append(f"High classification: {classification}")
        if compliance_tags:
            concerns.append(f"Compliance requirements: {', '.join(compliance_tags)}")
        if field_count > 20:
            concerns.append(f"Large schema: {field_count} fields")

        return ContractAnalysis(
            risk_level=risk_level,
            has_pii=has_pii,
            has_sensitive_data=has_sensitive_data,
            classification=classification,
            complexity_score=complexity_score,
            requires_compliance=len(compliance_tags) > 0,
            compliance_frameworks=compliance_tags,
            field_count=field_count,
            concerns=concerns
        )

    def _calculate_complexity(
        self, schema: List[Dict], governance: Dict
    ) -> int:
        """Calculate contract complexity score (0-100)."""
        score = 0

        # Field count contribution (0-30 points)
        field_count = len(schema)
        score += min(30, field_count * 1.5)

        # PII fields (0-20 points)
        pii_count = sum(1 for f in schema if f.get('pii', False))
        score += min(20, pii_count * 5)

        # Compliance requirements (0-20 points)
        compliance_count = len(governance.get('compliance_tags', []))
        score += min(20, compliance_count * 10)

        # Quality rules (0-15 points)
        quality_rules = governance.get('quality_rules', {})
        score += min(15, len(quality_rules) * 3)

        # Classification (0-15 points)
        classification = governance.get('classification', 'public')
        classification_scores = {
            'public': 0,
            'internal': 5,
            'confidential': 10,
            'restricted': 15
        }
        score += classification_scores.get(classification, 0)

        return min(100, int(score))

    def _assess_risk_level(
        self,
        has_pii: bool,
        classification: str,
        compliance_tags: List[str],
        field_count: int,
        complexity_score: int
    ) -> RiskLevel:
        """Assess contract risk level."""
        # Critical: Restricted data or multiple compliance frameworks
        if classification == 'restricted' or len(compliance_tags) >= 3:
            return RiskLevel.CRITICAL

        # High: Confidential data with PII or compliance requirements
        if classification == 'confidential' and (has_pii or compliance_tags):
            return RiskLevel.HIGH

        # High: Multiple compliance frameworks or high complexity
        if len(compliance_tags) >= 2 or complexity_score >= 70:
            return RiskLevel.HIGH

        # Medium: PII or single compliance requirement
        if has_pii or compliance_tags or classification == 'confidential':
            return RiskLevel.MEDIUM

        # Medium: Complex schema
        if field_count > 15 or complexity_score >= 40:
            return RiskLevel.MEDIUM

        # Low: Everything else
        return RiskLevel.LOW

    def _make_orchestration_decision(
        self,
        analysis: ContractAnalysis,
        strategy: ValidationStrategy
    ) -> OrchestrationDecision:
        """
        Make intelligent decision about which validation engines to use.

        Args:
            analysis: Contract analysis
            strategy: Requested validation strategy

        Returns:
            OrchestrationDecision with execution plan
        """
        # If semantic is not available, fall back to rule-based only
        if not self.semantic_engine.is_available():
            return OrchestrationDecision(
                strategy=ValidationStrategy.FAST,
                use_rule_based=True,
                use_semantic=False,
                semantic_policies=None,
                reasoning="Semantic engine not available, using rule-based only",
                estimated_time_seconds=0.1
            )

        # Handle explicit strategies
        if strategy == ValidationStrategy.FAST:
            return self._fast_strategy_decision(analysis)
        elif strategy == ValidationStrategy.BALANCED:
            return self._balanced_strategy_decision(analysis)
        elif strategy == ValidationStrategy.THOROUGH:
            return self._thorough_strategy_decision(analysis)
        elif strategy == ValidationStrategy.ADAPTIVE:
            return self._adaptive_strategy_decision(analysis)

        # Default to balanced
        return self._balanced_strategy_decision(analysis)

    def _fast_strategy_decision(self, analysis: ContractAnalysis) -> OrchestrationDecision:
        """Fast strategy: Rule-based only."""
        return OrchestrationDecision(
            strategy=ValidationStrategy.FAST,
            use_rule_based=True,
            use_semantic=False,
            semantic_policies=None,
            reasoning="Fast strategy: rule-based validation only",
            estimated_time_seconds=0.1
        )

    def _balanced_strategy_decision(self, analysis: ContractAnalysis) -> OrchestrationDecision:
        """Balanced strategy: Rule-based + targeted semantic."""
        # Select semantic policies based on analysis
        semantic_policies = []

        if analysis.has_pii or analysis.has_sensitive_data:
            semantic_policies.append("SEM001")  # Sensitive data context detection

        if analysis.requires_compliance:
            semantic_policies.append("SEM004")  # Compliance intent verification

        if analysis.complexity_score >= 50:
            semantic_policies.append("SEM002")  # Business logic consistency

        if analysis.has_sensitive_data:
            semantic_policies.append("SEM003")  # Security pattern detection

        use_semantic = len(semantic_policies) > 0

        return OrchestrationDecision(
            strategy=ValidationStrategy.BALANCED,
            use_rule_based=True,
            use_semantic=use_semantic,
            semantic_policies=semantic_policies if use_semantic else None,
            reasoning=f"Balanced strategy: rule-based + {len(semantic_policies)} semantic policies",
            estimated_time_seconds=0.1 + (len(semantic_policies) * 3.0)
        )

    def _thorough_strategy_decision(self, analysis: ContractAnalysis) -> OrchestrationDecision:
        """Thorough strategy: All validation engines and policies."""
        return OrchestrationDecision(
            strategy=ValidationStrategy.THOROUGH,
            use_rule_based=True,
            use_semantic=True,
            semantic_policies=None,  # Run all semantic policies
            reasoning="Thorough strategy: complete validation with all policies",
            estimated_time_seconds=0.1 + 24.0  # 8 policies * 3 seconds each
        )

    def _adaptive_strategy_decision(self, analysis: ContractAnalysis) -> OrchestrationDecision:
        """Adaptive strategy: Choose based on risk and complexity."""
        # Critical/High risk → Thorough validation
        if analysis.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            logger.info(f"Adaptive: High risk ({analysis.risk_level.value}) → thorough validation")
            return self._thorough_strategy_decision(analysis)

        # Low risk + low complexity → Fast validation
        if analysis.risk_level == RiskLevel.LOW and analysis.complexity_score < 30:
            logger.info(f"Adaptive: Low risk/complexity → fast validation")
            return self._fast_strategy_decision(analysis)

        # Everything else → Balanced validation
        logger.info(f"Adaptive: Medium risk/complexity → balanced validation")
        return self._balanced_strategy_decision(analysis)

    def _execute_validation(
        self,
        contract_data: Dict[str, Any],
        decision: OrchestrationDecision,
        analysis: ContractAnalysis
    ) -> ValidationResult:
        """
        Execute validation based on orchestration decision.

        Args:
            contract_data: Contract data
            decision: Orchestration decision
            analysis: Contract analysis

        Returns:
            Combined ValidationResult
        """
        rule_result = None
        semantic_result = None

        # Execute rule-based validation
        if decision.use_rule_based:
            logger.info("Executing rule-based validation...")
            rule_result = self.rule_engine.validate_contract(contract_data)
            logger.info(f"Rule-based: {rule_result.status.value}, "
                       f"violations={len(rule_result.violations)}")

        # Execute semantic validation
        if decision.use_semantic:
            logger.info(f"Executing semantic validation "
                       f"(policies: {decision.semantic_policies or 'all'})...")
            try:
                semantic_result = self.semantic_engine.validate_contract(
                    contract_data,
                    selected_policies=decision.semantic_policies
                )
                logger.info(f"Semantic: {semantic_result.status.value}, "
                           f"violations={len(semantic_result.violations)}")
            except Exception as e:
                logger.error(f"Semantic validation failed: {e}", exc_info=True)
                # Continue with rule-based results

        # Combine results
        return self._combine_results(rule_result, semantic_result, analysis)

    def _combine_results(
        self,
        rule_result: Optional[ValidationResult],
        semantic_result: Optional[ValidationResult],
        analysis: ContractAnalysis
    ) -> ValidationResult:
        """
        Combine and prioritize results from multiple engines.

        Args:
            rule_result: Result from rule-based engine
            semantic_result: Result from semantic engine
            analysis: Contract analysis

        Returns:
            Combined ValidationResult
        """
        # If only one result, return it
        if rule_result and not semantic_result:
            return rule_result
        if semantic_result and not rule_result:
            return semantic_result

        # Both results exist - combine them
        all_violations = []

        # Add rule-based violations (highest priority)
        if rule_result:
            all_violations.extend(rule_result.violations)

        # Add semantic violations (deduplicate if similar)
        if semantic_result:
            for sem_violation in semantic_result.violations:
                # Check if similar rule-based violation exists
                is_duplicate = False
                for rule_violation in rule_result.violations if rule_result else []:
                    if self._are_violations_similar(rule_violation, sem_violation):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    all_violations.append(sem_violation)

        # Prioritize violations by severity and source
        all_violations = self._prioritize_violations(all_violations, analysis)

        # Calculate combined stats
        total_passed = (rule_result.passed if rule_result else 0) + \
                      (semantic_result.passed if semantic_result else 0)
        total_warnings = (rule_result.warnings if rule_result else 0) + \
                        (semantic_result.warnings if semantic_result else 0)
        total_failures = (rule_result.failures if rule_result else 0) + \
                        (semantic_result.failures if semantic_result else 0)

        # Determine overall status
        if total_failures > 0:
            status = ValidationStatus.FAILED
        elif total_warnings > 0:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASSED

        return ValidationResult(
            status=status,
            passed=total_passed,
            warnings=total_warnings,
            failures=total_failures,
            violations=all_violations
        )

    def _are_violations_similar(self, v1: Violation, v2: Violation) -> bool:
        """Check if two violations are similar enough to be considered duplicates."""
        # Same field and similar policy ID
        if v1.field == v2.field:
            # Check if policy IDs are related (e.g., SD001 and SEM001 both about sensitive data)
            if 'pii' in v1.policy.lower() and 'sensitive' in v2.policy.lower():
                return True
            if 'encryption' in v1.policy.lower() and 'encryption' in v2.policy.lower():
                return True

        return False

    def _prioritize_violations(
        self, violations: List[Violation], analysis: ContractAnalysis
    ) -> List[Violation]:
        """
        Prioritize violations by severity and relevance.

        Args:
            violations: List of violations
            analysis: Contract analysis

        Returns:
            Sorted list of violations (most important first)
        """
        def violation_priority(v: Violation) -> Tuple[int, int, str]:
            # Priority order: CRITICAL > WARNING > INFO
            severity_priority = {
                ViolationType.CRITICAL: 0,
                ViolationType.WARNING: 1,
                ViolationType.INFO: 2
            }

            # Boost priority for risk-relevant violations
            relevance_boost = 0
            if analysis.has_pii and ('pii' in v.policy.lower() or 'sensitive' in v.policy.lower()):
                relevance_boost = -1
            if analysis.requires_compliance and 'compliance' in v.policy.lower():
                relevance_boost = -1

            return (
                severity_priority.get(v.type, 3) + relevance_boost,
                -len(v.message),  # Longer messages might be more important
                v.policy
            )

        return sorted(violations, key=violation_priority)

    def get_recommended_strategy(
        self, contract_data: Dict[str, Any]
    ) -> Tuple[ValidationStrategy, str]:
        """
        Get recommended validation strategy for a contract.

        Args:
            contract_data: Contract data

        Returns:
            Tuple of (recommended_strategy, reasoning)
        """
        analysis = self._analyze_contract(contract_data)
        decision = self._adaptive_strategy_decision(analysis)

        return decision.strategy, decision.reasoning

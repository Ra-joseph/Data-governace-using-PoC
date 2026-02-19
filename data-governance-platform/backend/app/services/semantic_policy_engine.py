"""
Semantic Policy Engine for LLM-powered policy validation.

This engine uses local LLMs (via Ollama) to perform semantic analysis
that cannot be achieved with rule-based policy engines.
"""

import yaml
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from app.schemas.contract import Violation, ValidationResult, ViolationType, ValidationStatus
from app.services.ollama_client import OllamaClient, OllamaError, get_ollama_client
from app.config import settings

logger = logging.getLogger(__name__)


class SemanticPolicyEngine:
    """Engine for validating contracts using LLM-powered semantic analysis."""

    def __init__(
        self,
        policies_path: str = None,
        ollama_client: Optional[OllamaClient] = None,
        enabled: bool = True
    ):
        """
        Initialize SemanticPolicyEngine.

        Args:
            policies_path: Path to policies directory
            ollama_client: Optional OllamaClient instance
            enabled: Whether semantic scanning is enabled
        """
        if policies_path:
            self.policies_path = Path(policies_path)
        else:
            configured_path = Path(settings.POLICIES_PATH)
            if configured_path.exists():
                self.policies_path = configured_path
            else:
                self.policies_path = Path(__file__).parent.parent.parent / "policies"
        self.enabled = enabled
        self.config = None
        self.policies = self._load_semantic_policies()

        # Initialize Ollama client if enabled
        if self.enabled:
            if ollama_client:
                self.llm_client = ollama_client
            else:
                ollama_config = self.config.get('ollama', {}) if self.config else {}
                self.llm_client = get_ollama_client(ollama_config)
        else:
            self.llm_client = None

    def _load_semantic_policies(self) -> Dict[str, Any]:
        """Load semantic policies from YAML file."""
        policy_file = self.policies_path / "semantic_policies.yaml"

        if not policy_file.exists():
            logger.warning(f"Semantic policies file not found: {policy_file}")
            return {}

        try:
            with open(policy_file, 'r') as f:
                data = yaml.safe_load(f)
                self.config = data.get('semantic_config', {})
                return data
        except Exception as e:
            logger.error(f"Failed to load semantic policies: {e}")
            return {}

    def is_available(self) -> bool:
        """
        Check if semantic scanning is available.

        Returns:
            True if Ollama is available and semantic policies are loaded
        """
        if not self.enabled:
            return False

        if not self.policies:
            return False

        if self.llm_client and not self.llm_client.is_available():
            logger.warning("Ollama is not available")
            return False

        return True

    def validate_contract(
        self,
        contract_data: Dict[str, Any],
        selected_policies: Optional[List[str]] = None
    ) -> ValidationResult:
        """
        Validate a contract using semantic policies.

        Args:
            contract_data: Contract data in JSON/dict format
            selected_policies: Optional list of policy IDs to run (runs all if None)

        Returns:
            ValidationResult with semantic violations
        """
        if not self.is_available():
            logger.info("Semantic scanning not available, skipping")
            return ValidationResult(
                status=ValidationStatus.PASSED,
                passed=0,
                warnings=0,
                failures=0,
                violations=[]
            )

        violations = []
        policies_list = self.policies.get('policies', [])

        # Filter policies if specific ones are selected
        if selected_policies:
            policies_list = [p for p in policies_list if p['id'] in selected_policies]

        logger.info(f"Running {len(policies_list)} semantic policies")

        # Run each semantic policy
        for policy in policies_list:
            policy_violations = self._evaluate_policy(policy, contract_data)
            violations.extend(policy_violations)

        # Calculate result status
        critical_count = sum(1 for v in violations if v.type == ViolationType.CRITICAL)
        warning_count = sum(1 for v in violations if v.type == ViolationType.WARNING)
        passed_count = len(policies_list) - len(violations)

        if critical_count > 0:
            status = ValidationStatus.FAILED
        elif warning_count > 0:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASSED

        logger.info(f"Semantic validation complete: {status.value}, "
                   f"passed={passed_count}, warnings={warning_count}, failures={critical_count}")

        return ValidationResult(
            status=status,
            passed=passed_count,
            warnings=warning_count,
            failures=critical_count,
            violations=violations
        )

    def _evaluate_policy(
        self,
        policy: Dict[str, Any],
        contract_data: Dict[str, Any]
    ) -> List[Violation]:
        """
        Evaluate a single semantic policy using LLM.

        Args:
            policy: Policy definition
            contract_data: Contract data

        Returns:
            List of violations found
        """
        policy_id = policy['id']
        policy_name = policy['name']
        logger.info(f"Evaluating semantic policy: {policy_id} - {policy_name}")

        violations = []

        try:
            # Prepare prompt based on policy type
            prompt = self._prepare_prompt(policy, contract_data)

            # Get LLM analysis
            response = self.llm_client.analyze_with_retry(
                prompt=prompt,
                system="You are a data governance expert analyzing database schemas for policy compliance. "
                       "Respond only with valid JSON.",
                max_retries=self.config.get('execution', {}).get('max_retries', 3)
            )

            # Parse and convert to violations
            policy_violations = self._parse_llm_response(
                policy_id=policy_id,
                policy_name=policy_name,
                severity=policy['severity'],
                response=response
            )

            violations.extend(policy_violations)

        except OllamaError as e:
            logger.error(f"Failed to evaluate policy {policy_id}: {e}")
            # Add error violation
            violations.append(Violation(
                type=ViolationType.WARNING,
                policy=f"{policy_id}: {policy_name}",
                field="semantic_analysis",
                message=f"Failed to perform semantic analysis: {str(e)}",
                remediation="Ensure Ollama is running and the model is available. "
                           "Run: ollama pull mistral:7b"
            ))
        except Exception as e:
            logger.error(f"Unexpected error evaluating policy {policy_id}: {e}", exc_info=True)

        return violations

    def _prepare_prompt(
        self,
        policy: Dict[str, Any],
        contract_data: Dict[str, Any]
    ) -> str:
        """
        Prepare prompt for LLM based on policy template.

        Args:
            policy: Policy definition with prompt_template
            contract_data: Contract data

        Returns:
            Formatted prompt string
        """
        template = policy.get('prompt_template', '')
        policy_id = policy['id']

        # Extract contract components
        dataset = contract_data.get('dataset', {})
        schema = contract_data.get('schema', [])
        governance = contract_data.get('governance', {})
        quality_rules = contract_data.get('quality_rules', {})

        # Prepare context based on policy type
        context = {
            'dataset_name': dataset.get('name', 'Unknown'),
            'classification': governance.get('classification', 'internal'),
            'field_names': [f['name'] for f in schema],
            'fields_list': self._format_fields_list(schema),
            'fields_summary': self._format_fields_summary(schema),
            'quality_rules': self._format_quality_rules(quality_rules),
            'retention_days': governance.get('retention_days', 'not specified'),
            'compliance_tags': governance.get('compliance_tags', []),
            'data_residency': governance.get('data_residency', 'not specified'),
            'approved_use_cases': governance.get('approved_use_cases', []),
            'data_types': list(set(f['type'] for f in schema)),
            'purpose': dataset.get('description', 'not specified'),
            'freshness_sla': quality_rules.get('freshness_sla', 'not specified'),
            'access_pattern': 'not specified',  # Could be enhanced
            'use_cases': governance.get('approved_use_cases', ['not specified'])
        }

        # Format template with context
        try:
            prompt = template.format(**context)
        except KeyError as e:
            logger.warning(f"Missing template variable {e} for policy {policy_id}")
            prompt = template

        return prompt

    def _format_fields_list(self, schema: List[Dict]) -> str:
        """Format schema fields as a readable list."""
        lines = []
        for field in schema:
            pii_marker = " [PII]" if field.get('pii') else ""
            lines.append(
                f"- {field['name']} ({field['type']}){pii_marker}: "
                f"{field.get('description', 'no description')}"
            )
        return "\n".join(lines) if lines else "No fields"

    def _format_fields_summary(self, schema: List[Dict]) -> str:
        """Format schema fields as a compact summary."""
        summaries = []
        for field in schema:
            pii = "PII" if field.get('pii') else ""
            required = "REQUIRED" if field.get('required') else ""
            tags = ", ".join(filter(None, [pii, required]))
            tags_str = f" [{tags}]" if tags else ""
            summaries.append(f"{field['name']}:{field['type']}{tags_str}")
        return ", ".join(summaries) if summaries else "No fields"

    def _format_quality_rules(self, quality_rules: Dict) -> str:
        """Format quality rules as readable text."""
        if not quality_rules:
            return "No quality rules defined"

        lines = []
        for key, value in quality_rules.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _parse_llm_response(
        self,
        policy_id: str,
        policy_name: str,
        severity: str,
        response: Dict[str, Any]
    ) -> List[Violation]:
        """
        Parse LLM response and convert to violations.

        Args:
            policy_id: Policy ID
            policy_name: Policy name
            severity: Policy severity
            response: LLM response dict

        Returns:
            List of Violation objects
        """
        violations = []
        llm_data = response.get('response', {})

        # Handle error responses
        if isinstance(llm_data, dict) and 'error' in llm_data:
            logger.warning(f"LLM returned error for policy {policy_id}: {llm_data['error']}")
            return violations

        confidence_threshold = self.config.get('execution', {}).get('confidence_threshold', 70)

        # Parse based on policy type
        if policy_id == 'SEM001':  # Sensitive data context detection
            violations.extend(self._parse_sem001(
                policy_id, policy_name, severity, llm_data, confidence_threshold
            ))
        elif policy_id == 'SEM002':  # Business logic consistency
            violations.extend(self._parse_sem002(policy_id, policy_name, severity, llm_data))
        elif policy_id == 'SEM003':  # Security pattern detection
            violations.extend(self._parse_sem003(policy_id, policy_name, llm_data))
        elif policy_id == 'SEM004':  # Compliance intent verification
            violations.extend(self._parse_sem004(policy_id, policy_name, llm_data))
        elif policy_id in ['SEM005', 'SEM006', 'SEM007', 'SEM008']:
            # Generic parser for other policies
            violations.extend(self._parse_generic(policy_id, policy_name, severity, llm_data))

        return violations

    def _parse_sem001(
        self, policy_id: str, policy_name: str, severity: str,
        data: Dict, confidence_threshold: int
    ) -> List[Violation]:
        """Parse SEM001: Sensitive data context detection."""
        violations = []

        is_sensitive = data.get('is_sensitive', False)
        confidence = data.get('confidence', 0)
        reasoning = data.get('reasoning', 'No reasoning provided')
        recommended_actions = data.get('recommended_actions', [])

        if is_sensitive and confidence >= confidence_threshold:
            violations.append(Violation(
                type=ViolationType.CRITICAL if severity == 'critical' else ViolationType.WARNING,
                policy=f"{policy_id}: {policy_name}",
                field="semantic_analysis",
                message=f"Potentially sensitive data detected (confidence: {confidence}%). {reasoning}",
                remediation="\n".join(recommended_actions) if recommended_actions else
                           "Review and classify this data appropriately"
            ))

        return violations

    def _parse_sem002(
        self, policy_id: str, policy_name: str, severity: str, data: Dict
    ) -> List[Violation]:
        """Parse SEM002: Business logic consistency."""
        violations = []

        is_consistent = data.get('is_consistent', True)
        issues = data.get('issues', [])

        if not is_consistent and issues:
            for issue in issues:
                violations.append(Violation(
                    type=self._severity_to_type(issue.get('severity', severity)),
                    policy=f"{policy_id}: {policy_name}",
                    field=issue.get('field', 'governance'),
                    message=issue.get('issue', 'Logical inconsistency detected'),
                    remediation=issue.get('suggestion', 'Review and correct the inconsistency')
                ))

        return violations

    def _parse_sem003(
        self, policy_id: str, policy_name: str, data: Dict
    ) -> List[Violation]:
        """Parse SEM003: Security pattern detection."""
        violations = []

        security_concerns = data.get('security_concerns', [])

        for concern in security_concerns:
            severity = concern.get('severity', 'medium')
            violations.append(Violation(
                type=self._severity_to_type(severity),
                policy=f"{policy_id}: {policy_name}",
                field=", ".join(concern.get('affected_fields', [])),
                message=f"{concern.get('concern_type', 'Security concern')}: "
                        f"{concern.get('description', 'Security issue detected')}",
                remediation=concern.get('remediation', 'Review and address the security concern')
            ))

        return violations

    def _parse_sem004(
        self, policy_id: str, policy_name: str, data: Dict
    ) -> List[Violation]:
        """Parse SEM004: Compliance intent verification."""
        violations = []

        compliance_analysis = data.get('compliance_analysis', [])

        for framework in compliance_analysis:
            if not framework.get('requirements_met', True):
                missing = framework.get('missing_requirements', [])
                violations.append(Violation(
                    type=ViolationType.CRITICAL,
                    policy=f"{policy_id}: {policy_name}",
                    field=f"compliance.{framework.get('framework', 'unknown')}",
                    message=f"{framework.get('framework')} requirements not met. "
                            f"Missing: {', '.join(missing)}",
                    remediation="\n".join(framework.get('recommendations', []))
                ))

        return violations

    def _parse_generic(
        self, policy_id: str, policy_name: str, severity: str, data: Dict
    ) -> List[Violation]:
        """Generic parser for structured LLM responses."""
        violations = []

        # Try common response structures
        if 'issues' in data and data['issues']:
            for issue in data['issues']:
                violations.append(Violation(
                    type=self._severity_to_type(severity),
                    policy=f"{policy_id}: {policy_name}",
                    field=issue.get('field', 'semantic_analysis'),
                    message=issue.get('message', 'Issue detected'),
                    remediation=issue.get('remediation', 'Review and address the issue')
                ))

        return violations

    def _severity_to_type(self, severity: str) -> ViolationType:
        """Convert severity string to ViolationType."""
        severity_lower = severity.lower()
        if severity_lower in ['critical', 'high']:
            return ViolationType.CRITICAL
        elif severity_lower in ['warning', 'medium', 'low']:
            return ViolationType.WARNING
        else:
            return ViolationType.INFO

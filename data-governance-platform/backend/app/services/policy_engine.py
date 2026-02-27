"""
Policy engine for governance policy validation.

This module provides the PolicyEngine class which validates data contracts
against YAML-defined governance policies. Includes three policy categories:
Sensitive Data (SD), Data Quality (DQ), and Schema Governance (SG) policies.
Validation results include detailed violation messages with remediation guidance.
"""

import yaml
from typing import Dict, List, Any
from pathlib import Path
from app.schemas.contract import Violation, ValidationResult, ViolationType, ValidationStatus
from app.config import settings


class PolicyEngine:
    """
    Engine for validating contracts against governance policies.

    Loads YAML policy definitions and validates data contracts against
    17 governance policies across three categories:
    - Sensitive Data (SD001-SD005): PII, encryption, retention, compliance
    - Data Quality (DQ001-DQ003): Completeness, freshness, uniqueness
    - Schema Governance (SG001-SG004): Documentation, ownership, constraints

    Attributes:
        policies_path: Path to directory containing YAML policy files.
        policies: Dictionary of loaded policy definitions.

    Example:
        >>> engine = PolicyEngine()
        >>> result = engine.validate_contract(contract_data)
        >>> print(f"Status: {result.status}, Failures: {result.failures}")
    """

    def __init__(self, policies_path: str = None):
        """
        Initialize PolicyEngine with policy files.

        Args:
            policies_path: Optional custom path to policies directory.
                          Defaults to settings.POLICIES_PATH.
        """
        if policies_path:
            self.policies_path = Path(policies_path).resolve()
        else:
            # Try configured path first (now an absolute path set in config.py).
            # Fall back to a path anchored relative to this file so the engine
            # works even if the config is not yet initialised.
            configured_path = Path(settings.POLICIES_PATH)
            if configured_path.exists():
                self.policies_path = configured_path
            else:
                # backend/app/services/policy_engine.py → three levels up → backend/policies
                self.policies_path = Path(__file__).resolve().parent.parent.parent / "policies"
        self.policies = self._load_policies()
    
    def _load_policies(self) -> Dict[str, Any]:
        """
        Load all policy files from the policies directory.

        Reads YAML policy definition files and constructs a dictionary
        of policy configurations indexed by policy category name.

        Returns:
            Dict[str, Any]: Dictionary mapping policy names to their
                           definitions loaded from YAML files.
        """
        policies = {}
        
        policy_files = [
            "sensitive_data_policies.yaml",
            "data_quality_policies.yaml",
            "schema_governance_policies.yaml"
        ]
        
        for filename in policy_files:
            file_path = self.policies_path / filename
            if file_path.exists():
                with open(file_path, 'r') as f:
                    policy_data = yaml.safe_load(f)
                    policy_name = policy_data.get('name')
                    policies[policy_name] = policy_data
        
        return policies
    
    def validate_contract(self, contract_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate a contract against all policies.
        
        Args:
            contract_data: Contract data in JSON/dict format
            
        Returns:
            ValidationResult with violations and status
        """
        violations = []
        
        # Extract contract components
        dataset = contract_data.get('dataset', {})
        schema = contract_data.get('schema', [])
        governance = contract_data.get('governance', {})
        quality_rules = contract_data.get('quality_rules', {})
        
        # Validate Sensitive Data Policies
        violations.extend(self._validate_sensitive_data(schema, governance))
        
        # Validate Data Quality Policies
        violations.extend(self._validate_data_quality(schema, governance, quality_rules))
        
        # Validate Schema Governance Policies
        violations.extend(self._validate_schema_governance(dataset, schema))
        
        # Calculate result status
        critical_count = sum(1 for v in violations if v.type == ViolationType.CRITICAL)
        warning_count = sum(1 for v in violations if v.type == ViolationType.WARNING)
        passed_count = len(self._get_all_policy_ids()) - len(violations)
        
        if critical_count > 0:
            status = ValidationStatus.FAILED
        elif warning_count > 0:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.PASSED
        
        return ValidationResult(
            status=status,
            passed=passed_count,
            warnings=warning_count,
            failures=critical_count,
            violations=violations
        )
    
    def _validate_sensitive_data(self, schema: List[Dict], governance: Dict) -> List[Violation]:
        """
        Validate sensitive data policies (SD001-SD005).

        Checks PII encryption requirements, retention policies, compliance tags,
        restricted data use cases, and cross-border data transfer requirements.

        Args:
            schema: List of field definitions with PII flags and types.
            governance: Governance metadata with classification and policies.

        Returns:
            List[Violation]: List of policy violations found.
        """
        violations = []
        
        # Check if schema contains PII
        has_pii = any(field.get('pii', False) for field in schema)
        classification = governance.get('classification', 'internal')
        
        # SD001: PII fields must have encryption enabled
        if has_pii and not governance.get('encryption_required', False):
            pii_fields = [f['name'] for f in schema if f.get('pii', False)]
            violations.append(Violation(
                type=ViolationType.CRITICAL,
                policy="SD001: pii_encryption_required",
                field=", ".join(pii_fields),
                message=f"PII fields {pii_fields} require encryption but encryption_required is False",
                remediation="Set 'encryption_required: true' in governance metadata\nExample:\n  governance:\n    encryption_required: true"
            ))
        
        # SD002: Confidential/Restricted data must specify retention period
        if classification in ['confidential', 'restricted'] and not governance.get('retention_days'):
            violations.append(Violation(
                type=ViolationType.CRITICAL,
                policy="SD002: retention_policy_required",
                field="governance.retention_days",
                message=f"Classification '{classification}' requires retention_days to be specified",
                remediation="Add retention_days to governance section\nExample:\n  governance:\n    retention_days: 2555  # 7 years"
            ))
        
        # SD003: PII datasets should have compliance tags
        if has_pii and not governance.get('compliance_tags'):
            violations.append(Violation(
                type=ViolationType.WARNING,
                policy="SD003: pii_compliance_tags",
                field="governance.compliance_tags",
                message="Datasets with PII should specify applicable compliance frameworks (GDPR, CCPA, HIPAA)",
                remediation="Add compliance tags\nExample:\n  governance:\n    compliance_tags:\n      - GDPR\n      - CCPA"
            ))
        
        # SD004: Restricted data must specify approved use cases
        if classification == 'restricted' and not governance.get('approved_use_cases'):
            violations.append(Violation(
                type=ViolationType.CRITICAL,
                policy="SD004: restricted_use_cases",
                field="governance.approved_use_cases",
                message="Restricted data must specify approved use cases",
                remediation="Add approved use cases\nExample:\n  governance:\n    approved_use_cases:\n      - fraud_detection\n      - compliance_reporting"
            ))
        
        return violations
    
    def _validate_data_quality(self, schema: List[Dict], governance: Dict, quality_rules: Dict) -> List[Violation]:
        """
        Validate data quality policies (DQ001-DQ003).

        Checks completeness thresholds for critical data, freshness SLA
        requirements for temporal datasets, and uniqueness specifications
        for key fields.

        Args:
            schema: List of field definitions with types and constraints.
            governance: Governance metadata with classification level.
            quality_rules: Quality thresholds and SLA requirements.

        Returns:
            List[Violation]: List of policy violations found.
        """
        violations = []
        
        classification = governance.get('classification', 'internal')
        
        # DQ001: Critical data requires high completeness
        if classification in ['confidential', 'restricted']:
            completeness = quality_rules.get('completeness_threshold', 0)
            if completeness < 95:
                violations.append(Violation(
                    type=ViolationType.CRITICAL,
                    policy="DQ001: critical_data_completeness",
                    field="quality_rules.completeness_threshold",
                    message=f"Classification '{classification}' requires completeness_threshold >= 95%, current: {completeness}%",
                    remediation="Increase completeness threshold\nExample:\n  quality_rules:\n    completeness_threshold: 99"
                ))
        
        # DQ002: Temporal datasets should specify freshness SLA
        has_temporal_fields = any(
            field.get('type') in ['date', 'timestamp', 'datetime'] 
            for field in schema
        )
        if has_temporal_fields and not quality_rules.get('freshness_sla'):
            violations.append(Violation(
                type=ViolationType.WARNING,
                policy="DQ002: freshness_sla_required",
                field="quality_rules.freshness_sla",
                message="Temporal datasets should specify freshness SLA",
                remediation="Define freshness requirement\nExample:\n  quality_rules:\n    freshness_sla: \"24h\""
            ))
        
        # DQ003: Key fields should have uniqueness specification
        # (This is a heuristic check - look for fields with "id" in name)
        has_id_fields = any('id' in field.get('name', '').lower() for field in schema)
        if has_id_fields and not quality_rules.get('uniqueness_fields'):
            violations.append(Violation(
                type=ViolationType.WARNING,
                policy="DQ003: uniqueness_specification",
                field="quality_rules.uniqueness_fields",
                message="Key fields should have uniqueness constraints specified",
                remediation="Specify fields that must be unique\nExample:\n  quality_rules:\n    uniqueness_fields:\n      - account_id"
            ))
        
        return violations
    
    def _validate_schema_governance(self, dataset: Dict, schema: List[Dict]) -> List[Violation]:
        """
        Validate schema governance policies (SG001-SG004).

        Checks field documentation, required field consistency, dataset
        ownership requirements, and string field constraints.

        Args:
            dataset: Dataset metadata with owner information.
            schema: List of field definitions with documentation.

        Returns:
            List[Violation]: List of policy violations found.
        """
        violations = []
        
        # SG001: Field documentation
        undocumented_fields = [
            field['name'] for field in schema 
            if not field.get('description')
        ]
        if undocumented_fields:
            violations.append(Violation(
                type=ViolationType.WARNING,
                policy="SG001: field_documentation_required",
                field=", ".join(undocumented_fields),
                message=f"Fields missing descriptions: {undocumented_fields}",
                remediation="Add descriptions to all fields\nExample:\n  - name: customer_email\n    description: \"Customer email address for communication\""
            ))
        
        # SG002: Required fields cannot be nullable
        inconsistent_fields = [
            field['name'] for field in schema
            if field.get('required', False) and field.get('nullable', True)
        ]
        if inconsistent_fields:
            violations.append(Violation(
                type=ViolationType.CRITICAL,
                policy="SG002: required_field_consistency",
                field=", ".join(inconsistent_fields),
                message=f"Required fields cannot be nullable: {inconsistent_fields}",
                remediation="Set nullable: false for required fields\nExample:\n  - name: account_id\n    required: true\n    nullable: false"
            ))
        
        # SG003: Dataset ownership required
        if not dataset.get('owner_name') or not dataset.get('owner_email'):
            violations.append(Violation(
                type=ViolationType.CRITICAL,
                policy="SG003: dataset_ownership_required",
                field="dataset.owner_name, dataset.owner_email",
                message="All datasets must have owner_name and owner_email specified",
                remediation="Specify dataset owner\nExample:\n  dataset:\n    owner_name: \"John Doe\"\n    owner_email: \"john.doe@company.com\""
            ))
        
        # SG004: String fields should have max_length
        string_fields_without_length = [
            field['name'] for field in schema
            if field.get('type') == 'string' and not field.get('max_length')
        ]
        if string_fields_without_length:
            violations.append(Violation(
                type=ViolationType.WARNING,
                policy="SG004: string_field_constraints",
                field=", ".join(string_fields_without_length),
                message=f"String fields should have max_length: {string_fields_without_length}",
                remediation="Add max_length constraint\nExample:\n  - name: customer_name\n    type: string\n    max_length: 255"
            ))
        
        return violations
    
    def _get_all_policy_ids(self) -> List[str]:
        """
        Get list of all policy IDs for counting.

        Extracts policy IDs from all loaded policy definitions to
        calculate total policy count for validation results.

        Returns:
            List[str]: List of all policy IDs (e.g., ["SD001", "SD002", ...]).
        """
        policy_ids = []
        for policy_doc in self.policies.values():
            for policy in policy_doc.get('policies', []):
                policy_ids.append(policy['id'])
        return policy_ids

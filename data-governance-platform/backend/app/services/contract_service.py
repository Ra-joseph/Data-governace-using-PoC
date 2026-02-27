"""
Contract service for data contract lifecycle management.

This module provides the ContractService class which handles the complete
lifecycle of data contracts including creation, validation, versioning,
Git-based version control, and approval workflows. It integrates with the
PolicyEngine for rule-based validation and optionally with SemanticPolicyEngine
for LLM-powered semantic validation.
"""

import copy
import json
import yaml
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.contract import Contract
from app.models.dataset import Dataset
from app.services.policy_engine import PolicyEngine
from app.services.semantic_policy_engine import SemanticPolicyEngine
from app.services.policy_orchestrator import PolicyOrchestrator, ValidationStrategy
from app.services.git_service import GitService
from app.schemas.contract import ValidationResult, Violation, ValidationStatus

logger = logging.getLogger(__name__)


class ContractService:
    """
    Service for managing data contract lifecycle.

    Handles creation of data contracts from datasets, validation against
    governance policies, semantic versioning, Git-based version control,
    and contract approval workflows. Integrates both rule-based and
    optional semantic (LLM-based) policy validation.

    Attributes:
        policy_engine: PolicyEngine for rule-based validation.
        semantic_engine: SemanticPolicyEngine for LLM-based validation.
        git_service: GitService for version control operations.
        db: Database session for persistence.
        enable_semantic: Whether semantic validation is enabled.

    Example:
        >>> service = ContractService(db, enable_semantic=True)
        >>> contract = service.create_contract_from_dataset(db, dataset_id=1)
        >>> result = service.validate_contract(contract.machine_readable)
    """

    def __init__(
        self,
        db: Session = None,
        enable_semantic: bool = False,
        validation_strategy: ValidationStrategy = ValidationStrategy.ADAPTIVE
    ):
        """
        Initialize contract service.

        Args:
            db: Optional database session for contract persistence.
            enable_semantic: Enable semantic validation with local LLM via Ollama.
                           Defaults to False for faster validation.
            validation_strategy: Default validation strategy for orchestrator.
                               Defaults to ADAPTIVE (auto-selects based on risk).
        """
        # Legacy engines (for backward compatibility)
        self.policy_engine = PolicyEngine()
        self.semantic_engine = SemanticPolicyEngine(enabled=enable_semantic)

        # New orchestrator (recommended)
        self.orchestrator = PolicyOrchestrator(
            enable_semantic=enable_semantic,
            default_strategy=validation_strategy
        )

        self.git_service = GitService()
        self.db = db
        self.enable_semantic = enable_semantic
        self.validation_strategy = validation_strategy
    
    def create_contract_from_dataset(self, db: Session, dataset_id: int, 
                                    version: str = "1.0.0") -> Contract:
        """
        Create a data contract from a dataset.
        
        Args:
            db: Database session
            dataset_id: Dataset ID
            version: Contract version (semantic versioning)
            
        Returns:
            Created Contract object
        """
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not dataset:
            raise ValueError(f"Dataset with ID {dataset_id} not found")
        
        # Build contract data structure
        contract_data = {
            'dataset': {
                'name': dataset.name,
                'description': dataset.description,
                'owner_name': dataset.owner_name,
                'owner_email': dataset.owner_email,
                'version': version
            },
            'schema': dataset.schema_definition,
            'governance': {
                'classification': dataset.classification,
                'encryption_required': False,  # Will be set based on PII
                'compliance_tags': dataset.compliance_tags or []
            },
            'quality_rules': {},
            'metadata': {
                'source_type': dataset.source_type,
                'physical_location': dataset.physical_location,
                'created_at': datetime.now().isoformat()
            }
        }
        
        # Check for PII and set encryption requirement
        has_pii = any(field.get('pii', False) for field in dataset.schema_definition)
        if has_pii:
            contract_data['governance']['encryption_required'] = True
        
        # Generate YAML (human-readable)
        human_readable = self._generate_yaml(contract_data, dataset.name, version)
        
        # Machine-readable is just the dict as JSON
        machine_readable = contract_data
        
        # Calculate schema hash
        schema_hash = self._calculate_schema_hash(dataset.schema_definition)
        
        # Validate contract (rule-based + optional semantic)
        validation_result = self.validate_contract_combined(contract_data)
        
        # Commit to Git
        git_info = self.git_service.commit_contract(
            human_readable,
            dataset.name,
            version,
            f"Initial contract for {dataset.name} v{version}"
        )
        
        # Create Contract record
        contract = Contract(
            dataset_id=dataset_id,
            version=version,
            human_readable=human_readable,
            machine_readable=machine_readable,
            schema_hash=schema_hash,
            governance_rules=contract_data['governance'],
            quality_rules=contract_data.get('quality_rules'),
            validation_status=validation_result.status.value,
            validation_results=json.loads(validation_result.model_dump_json()),
            last_validated_at=datetime.now(),
            git_commit_hash=git_info['commit_hash'],
            git_file_path=git_info['file_path']
        )
        
        db.add(contract)
        db.commit()
        db.refresh(contract)
        
        return contract
    
    def enrich_contract_with_slas(self, db: Session, contract_id: int, 
                                  sla_data: Dict[str, Any]) -> Contract:
        """
        Enrich a contract with SLA requirements from a subscription.
        
        Args:
            db: Database session
            contract_id: Contract ID
            sla_data: SLA requirements dictionary
            
        Returns:
            New Contract version with SLAs
        """
        # Get existing contract
        old_contract = db.query(Contract).filter(Contract.id == contract_id).first()
        if not old_contract:
            raise ValueError(f"Contract with ID {contract_id} not found")
        
        # Get dataset
        dataset = db.query(Dataset).filter(Dataset.id == old_contract.dataset_id).first()
        
        # Load existing contract data (deepcopy to avoid mutating the stored record)
        contract_data = copy.deepcopy(old_contract.machine_readable)

        # Add SLA requirements
        contract_data['sla_requirements'] = sla_data
        
        # Increment version (minor bump: 1.0.0 -> 1.1.0)
        old_version_parts = old_contract.version.split('.')
        new_version = f"{old_version_parts[0]}.{int(old_version_parts[1]) + 1}.{old_version_parts[2]}"
        contract_data['dataset']['version'] = new_version
        
        # Regenerate YAML
        human_readable = self._generate_yaml(contract_data, dataset.name, new_version)
        
        # Validate enriched contract (rule-based + optional semantic)
        validation_result = self.validate_contract_combined(contract_data)
        
        # Commit to Git
        git_info = self.git_service.commit_contract(
            human_readable,
            dataset.name,
            new_version,
            f"Add SLA requirements to {dataset.name} v{new_version}"
        )
        
        # Create new contract version
        new_contract = Contract(
            dataset_id=old_contract.dataset_id,
            version=new_version,
            human_readable=human_readable,
            machine_readable=contract_data,
            schema_hash=old_contract.schema_hash,
            governance_rules=contract_data['governance'],
            quality_rules=contract_data.get('quality_rules'),
            sla_requirements=sla_data,
            validation_status=validation_result.status.value,
            validation_results=json.loads(validation_result.model_dump_json()),
            last_validated_at=datetime.now(),
            git_commit_hash=git_info['commit_hash'],
            git_file_path=git_info['file_path']
        )
        
        db.add(new_contract)
        db.commit()
        db.refresh(new_contract)
        
        return new_contract
    
    def validate_contract(self, contract_yaml: str = None, 
                         contract_json: Dict = None) -> ValidationResult:
        """
        Validate a contract (from YAML or JSON).
        
        Args:
            contract_yaml: Contract in YAML format
            contract_json: Contract in JSON/dict format
            
        Returns:
            ValidationResult
        """
        if contract_yaml:
            contract_data = yaml.safe_load(contract_yaml)
        elif contract_json:
            contract_data = contract_json
        else:
            raise ValueError("Either contract_yaml or contract_json must be provided")

        return self.validate_contract_combined(contract_data)
    
    def get_contract_diff(self, db: Session, old_version_id: int, 
                         new_version_id: int) -> Dict[str, Any]:
        """
        Compare two contract versions.
        
        Args:
            db: Database session
            old_version_id: Old contract ID
            new_version_id: New contract ID
            
        Returns:
            Dictionary with differences
        """
        old_contract = db.query(Contract).filter(Contract.id == old_version_id).first()
        new_contract = db.query(Contract).filter(Contract.id == new_version_id).first()
        
        if not old_contract or not new_contract:
            raise ValueError("One or both contracts not found")
        
        differences = {
            'version_change': f"{old_contract.version} -> {new_contract.version}",
            'schema_changed': old_contract.schema_hash != new_contract.schema_hash,
            'sla_added': new_contract.sla_requirements is not None and old_contract.sla_requirements is None,
            'yaml_diff': self._get_yaml_diff(old_contract.human_readable, new_contract.human_readable)
        }
        
        return differences
    
    def _generate_yaml(self, contract_data: Dict, dataset_name: str, version: str) -> str:
        """Generate human-readable YAML with header."""
        header = f"""# Data Contract
# Dataset: {dataset_name}
# Version: {version}
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# 
# This contract defines the schema, governance rules, and quality requirements
# for the {dataset_name} dataset.

"""
        yaml_content = yaml.dump(contract_data, default_flow_style=False, sort_keys=False)
        return header + yaml_content
    
    def _calculate_schema_hash(self, schema: list) -> str:
        """Calculate SHA-256 hash of schema for version tracking."""
        schema_str = json.dumps(schema, sort_keys=True)
        return hashlib.sha256(schema_str.encode()).hexdigest()

    def validate_contract_combined(
        self,
        contract_data: Dict[str, Any],
        strategy: Optional[ValidationStrategy] = None
    ) -> ValidationResult:
        """
        Validate contract using intelligent orchestration.

        This method uses the PolicyOrchestrator to automatically decide
        which validation engines to use based on contract characteristics.

        Args:
            contract_data: Contract data in JSON/dict format
            strategy: Validation strategy (FAST, BALANCED, THOROUGH, ADAPTIVE)
                     If None, uses the default strategy from initialization

        Returns:
            Orchestrated ValidationResult
        """
        logger.info(f"Starting orchestrated validation with strategy: "
                   f"{strategy.value if strategy else 'default'}")

        # Use orchestrator for intelligent validation
        result = self.orchestrator.validate_contract(
            contract_data,
            strategy=strategy
        )

        logger.info(f"Orchestrated validation complete: {result.status.value}, "
                   f"violations={len(result.violations)}")

        return result

    def _combine_validation_results(
        self,
        rule_result: ValidationResult,
        semantic_result: ValidationResult
    ) -> ValidationResult:
        """
        Combine validation results from rule-based and semantic engines.

        Args:
            rule_result: Result from rule-based policy engine
            semantic_result: Result from semantic policy engine

        Returns:
            Combined ValidationResult
        """
        # Merge violations
        all_violations = rule_result.violations + semantic_result.violations

        # Calculate combined counts
        total_passed = rule_result.passed + semantic_result.passed
        total_warnings = rule_result.warnings + semantic_result.warnings
        total_failures = rule_result.failures + semantic_result.failures

        # Determine overall status (most severe wins)
        if total_failures > 0:
            combined_status = ValidationStatus.FAILED
        elif total_warnings > 0:
            combined_status = ValidationStatus.WARNING
        else:
            combined_status = ValidationStatus.PASSED

        return ValidationResult(
            status=combined_status,
            passed=total_passed,
            warnings=total_warnings,
            failures=total_failures,
            violations=all_violations
        )

    def _get_yaml_diff(self, old_yaml: str, new_yaml: str) -> list:
        """Get line-by-line diff of YAML files."""
        old_lines = old_yaml.split('\n')
        new_lines = new_yaml.split('\n')
        
        diff = []
        max_len = max(len(old_lines), len(new_lines))
        
        for i in range(max_len):
            old_line = old_lines[i] if i < len(old_lines) else ''
            new_line = new_lines[i] if i < len(new_lines) else ''
            
            if old_line != new_line:
                diff.append({
                    'line': i + 1,
                    'old': old_line,
                    'new': new_line
                })
        
        return diff[:20]  # Limit to first 20 differences

    def add_subscription_to_contract(self, contract_id: int, subscription_id: int,
                                    subscription_data: Dict[str, Any]) -> Contract:
        """
        Add subscription details to contract and create new version.

        Args:
            contract_id: Contract ID
            subscription_id: Subscription ID
            subscription_data: Subscription details (consumer, SLA, fields)

        Returns:
            New Contract version with subscription
        """
        if not self.db:
            raise ValueError("Database session required")

        # Get existing contract
        old_contract = self.db.query(Contract).filter(Contract.id == contract_id).first()
        if not old_contract:
            raise ValueError(f"Contract with ID {contract_id} not found")

        # Get dataset
        dataset = self.db.query(Dataset).filter(Dataset.id == old_contract.dataset_id).first()

        # Load existing contract data (deepcopy to avoid mutating the stored record)
        contract_data = copy.deepcopy(old_contract.machine_readable)

        # Add subscription information
        if 'subscriptions' not in contract_data:
            contract_data['subscriptions'] = []

        contract_data['subscriptions'].append({
            'subscription_id': subscription_id,
            'consumer': subscription_data.get('consumer'),
            'sla_requirements': subscription_data.get('sla_requirements', {}),
            'approved_fields': subscription_data.get('approved_fields', []),
            'approved_at': datetime.now().isoformat()
        })

        # Increment version (minor bump: 1.0.0 -> 1.1.0)
        old_version_parts = old_contract.version.split('.')
        new_version = f"{old_version_parts[0]}.{int(old_version_parts[1]) + 1}.{old_version_parts[2]}"
        contract_data['dataset']['version'] = new_version

        # Regenerate YAML
        human_readable = self._generate_yaml(contract_data, dataset.name, new_version)

        # Validate enriched contract (rule-based + optional semantic)
        validation_result = self.validate_contract_combined(contract_data)

        # Commit to Git
        git_info = self.git_service.commit_contract(
            human_readable,
            dataset.name,
            new_version,
            f"Add subscription for {subscription_data.get('consumer')} to {dataset.name} v{new_version}"
        )

        # Create new contract version
        new_contract = Contract(
            dataset_id=old_contract.dataset_id,
            version=new_version,
            human_readable=human_readable,
            machine_readable=contract_data,
            schema_hash=old_contract.schema_hash,
            governance_rules=contract_data['governance'],
            quality_rules=contract_data.get('quality_rules'),
            sla_requirements=subscription_data.get('sla_requirements'),
            validation_status=validation_result.status.value,
            validation_results=json.loads(validation_result.model_dump_json()),
            last_validated_at=datetime.now(),
            git_commit_hash=git_info['commit_hash'],
            git_file_path=git_info['file_path']
        )

        self.db.add(new_contract)
        self.db.commit()
        self.db.refresh(new_contract)

        return new_contract

"""
Pydantic schemas for data contract validation and management.

This module defines request and response schemas for contract operations including
validation results, violation details, and contract lifecycle management. It provides
structured data models for API communication and validation status tracking.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class ValidationStatus(str, Enum):
    """
    Contract validation status enumeration.

    Represents the overall result of contract validation against governance
    policies.

    Attributes:
        PENDING: Validation not yet performed
        PASSED: All validations passed without violations
        WARNING: Passed with non-critical warnings
        FAILED: Critical validation failures detected
    """
    PENDING = "pending"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class ViolationType(str, Enum):
    """
    Violation severity type enumeration.

    Classifies policy violations by their severity level for prioritization.

    Attributes:
        CRITICAL: Must be fixed before approval (e.g., PII without encryption)
        WARNING: Should be addressed but not blocking (e.g., missing description)
        INFO: Informational suggestions for improvement
    """
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class Violation(BaseModel):
    """
    Policy violation details schema.

    Represents a single policy violation detected during contract validation,
    including context, severity, and remediation guidance.

    Attributes:
        type: Severity level (critical, warning, info)
        policy: Policy ID that was violated (e.g., "SD001", "SEM003")
        field: Optional field name where violation occurred
        message: Human-readable violation description
        remediation: Suggested fix or action to resolve violation
        line_number: Optional line number in contract (for YAML validation)

    Example:
        {
            "type": "critical",
            "policy": "SD001",
            "field": "email",
            "message": "PII field 'email' requires encryption",
            "remediation": "Add 'encryption: AES-256' to field governance"
        }
    """
    type: ViolationType
    policy: str
    field: Optional[str] = None
    message: str
    remediation: str
    line_number: Optional[int] = None


class ValidationResult(BaseModel):
    """
    Contract validation result schema.

    Aggregates all validation results including overall status, counts by
    severity, and detailed violation information.

    Attributes:
        status: Overall validation status (passed, warning, failed)
        passed: Number of policies that passed validation
        warnings: Number of warning-level violations
        failures: Number of critical failures
        violations: List of detailed violation objects
        timestamp: Timestamp when validation was performed

    Example:
        {
            "status": "failed",
            "passed": 8,
            "warnings": 2,
            "failures": 1,
            "violations": [...],
            "timestamp": "2024-01-15T10:30:00Z"
        }
    """
    status: ValidationStatus
    passed: int = 0
    warnings: int = 0
    failures: int = 0
    violations: List[Violation] = []
    timestamp: datetime = datetime.now()
    metadata: Optional[Dict[str, Any]] = None


class ContractCreate(BaseModel):
    """
    Schema for creating a new contract.

    Request model for contract creation with optional SLA requirements.

    Attributes:
        dataset_id: ID of the dataset to create contract for
        version: Semantic version string (e.g., "1.0.0")
        sla_requirements: Optional SLA specifications for the contract
    """
    dataset_id: int
    version: str
    sla_requirements: Optional[Dict[str, Any]] = None


class ContractResponse(BaseModel):
    """
    Schema for contract response.

    Response model containing complete contract information including
    both human and machine-readable formats, validation results, and Git metadata.

    Attributes:
        id: Unique contract identifier
        dataset_id: ID of associated dataset
        version: Semantic version string
        human_readable: YAML formatted contract for human consumption
        machine_readable: Parsed contract as dictionary
        schema_hash: SHA-256 hash of schema for change detection
        validation_status: Current validation status (passed, warning, failed)
        validation_results: Detailed validation results dictionary
        git_commit_hash: Git commit hash where contract was stored
        git_file_path: Path to contract file in Git repository
        created_at: Contract creation timestamp
    """
    id: int
    dataset_id: int
    version: str
    human_readable: str
    machine_readable: Dict[str, Any]
    schema_hash: str
    validation_status: str
    validation_results: Optional[Dict[str, Any]]
    git_commit_hash: Optional[str]
    git_file_path: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ContractValidateRequest(BaseModel):
    """
    Request to validate a contract.

    Allows validation of contract in either YAML or JSON format before creation.

    Attributes:
        contract_yaml: Optional YAML string representation
        contract_json: Optional dictionary representation
    """
    contract_yaml: Optional[str] = None
    contract_json: Optional[Dict[str, Any]] = None


class ContractApprovalRequest(BaseModel):
    """
    Request to approve or reject a contract.

    Used by data stewards to formally approve contracts.

    Attributes:
        approved: Boolean approval decision
        comments: Optional comments explaining decision
    """
    approved: bool
    comments: Optional[str] = None

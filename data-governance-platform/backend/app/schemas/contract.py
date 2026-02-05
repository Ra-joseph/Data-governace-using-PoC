from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from enum import Enum


class ValidationStatus(str, Enum):
    """Contract validation status."""
    PENDING = "pending"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"


class ViolationType(str, Enum):
    """Violation severity types."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class Violation(BaseModel):
    """Policy violation details."""
    type: ViolationType
    policy: str
    field: Optional[str] = None
    message: str
    remediation: str
    line_number: Optional[int] = None


class ValidationResult(BaseModel):
    """Contract validation result."""
    status: ValidationStatus
    passed: int = 0
    warnings: int = 0
    failures: int = 0
    violations: List[Violation] = []
    timestamp: datetime = datetime.now()


class ContractCreate(BaseModel):
    """Schema for creating a contract."""
    dataset_id: int
    version: str
    sla_requirements: Optional[Dict[str, Any]] = None


class ContractResponse(BaseModel):
    """Schema for contract response."""
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
    """Request to validate a contract."""
    contract_yaml: Optional[str] = None
    contract_json: Optional[Dict[str, Any]] = None


class ContractApprovalRequest(BaseModel):
    """Request to approve a contract."""
    approved: bool
    comments: Optional[str] = None

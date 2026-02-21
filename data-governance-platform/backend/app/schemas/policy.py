"""
Pydantic schemas for policy authoring and approval workflow.
"""

from typing import Optional, List, Any
from datetime import datetime, date
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PolicyCategory(str, Enum):
    DATA_QUALITY = "data_quality"
    SECURITY = "security"
    PRIVACY = "privacy"
    COMPLIANCE = "compliance"
    LINEAGE = "lineage"
    SLA = "sla"


class PolicySeverity(str, Enum):
    CRITICAL = "CRITICAL"
    WARNING = "WARNING"
    INFO = "INFO"


class ScannerHint(str, Enum):
    RULE_BASED = "rule_based"
    AI_SEMANTIC = "ai_semantic"
    AUTO = "auto"


class PolicyStatus(str, Enum):
    DRAFT = "draft"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEPRECATED = "deprecated"


# --- Request Schemas ---

class PolicyCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    policy_category: PolicyCategory
    affected_domains: List[str] = Field(default=["ALL"])
    severity: PolicySeverity = PolicySeverity.WARNING
    scanner_hint: ScannerHint = ScannerHint.AUTO
    remediation_guide: Optional[str] = None
    effective_date: Optional[date] = None
    authored_by: str = Field(default="Data Governance Expert")


class PolicyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    policy_category: Optional[PolicyCategory] = None
    affected_domains: Optional[List[str]] = None
    severity: Optional[PolicySeverity] = None
    scanner_hint: Optional[ScannerHint] = None
    remediation_guide: Optional[str] = None
    effective_date: Optional[date] = None
    authored_by: Optional[str] = None


class PolicySubmit(BaseModel):
    """No extra fields needed — triggers status change to pending_approval."""
    pass


class PolicyApprove(BaseModel):
    approver_name: str = Field(default="Data Governance Approver", min_length=1)


class PolicyReject(BaseModel):
    approver_name: str = Field(default="Data Governance Approver", min_length=1)
    comment: str = Field(..., min_length=10)


# --- Response Schemas ---

class PolicyVersionResponse(BaseModel):
    id: int
    version: int
    title: str
    status: str
    authored_by: str
    approved_by: Optional[str]
    created_at: Optional[datetime]

    class Config:
        from_attributes = True


class PolicyArtifactResponse(BaseModel):
    id: int
    version: int
    yaml_content: str
    json_content: str
    scanner_type: str
    git_commit_hash: Optional[str]
    git_file_path: Optional[str]
    generated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PolicyApprovalLogResponse(BaseModel):
    id: int
    action: str
    actor_name: str
    comment: Optional[str]
    timestamp: Optional[datetime]

    class Config:
        from_attributes = True


class PolicyResponse(BaseModel):
    id: int
    policy_uid: str
    title: str
    description: str
    policy_category: str
    affected_domains: Any
    severity: str
    scanner_hint: str
    remediation_guide: Optional[str]
    effective_date: Optional[date]
    authored_by: str
    status: str
    version: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class PolicyDetailResponse(PolicyResponse):
    versions: List[PolicyVersionResponse] = []
    artifacts: List[PolicyArtifactResponse] = []
    approval_logs: List[PolicyApprovalLogResponse] = []

    class Config:
        from_attributes = True


class PolicyListResponse(BaseModel):
    policies: List[PolicyResponse]
    total: int

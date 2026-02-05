from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class FieldType(str, Enum):
    """Field data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    JSON = "json"


class Classification(str, Enum):
    """Data classification levels."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class SourceType(str, Enum):
    """Data source types."""
    POSTGRES = "postgres"
    FILE = "file"
    AZURE_BLOB = "azure_blob"
    AZURE_ADLS = "azure_adls"


class DatasetStatus(str, Enum):
    """Dataset lifecycle status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class FieldSchema(BaseModel):
    """Schema definition for a single field."""
    name: str
    type: FieldType
    required: bool = False
    nullable: bool = True
    pii: bool = False
    description: Optional[str] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    enum_values: Optional[List[str]] = None
    pattern: Optional[str] = None
    foreign_key: Optional[str] = None  # Format: "table.column"


class GovernanceMetadata(BaseModel):
    """Governance rules for a dataset."""
    classification: Classification = Classification.INTERNAL
    encryption_required: bool = False
    retention_days: Optional[int] = None
    compliance_tags: Optional[List[str]] = None
    segment_filters: Optional[Dict[str, Any]] = None
    approved_use_cases: Optional[List[str]] = None
    data_residency: Optional[str] = None


class QualityRules(BaseModel):
    """Data quality rules and thresholds."""
    completeness_threshold: Optional[float] = Field(None, ge=0, le=100)
    accuracy_threshold: Optional[float] = Field(None, ge=0, le=100)
    freshness_sla: Optional[str] = None  # e.g., "1h", "24h"
    uniqueness_fields: Optional[List[str]] = None
    custom_rules: Optional[Dict[str, Any]] = None


class DatasetCreate(BaseModel):
    """Schema for creating a dataset."""
    name: str
    description: Optional[str] = None
    owner_name: str
    owner_email: EmailStr
    source_type: SourceType
    source_connection: Optional[str] = None
    physical_location: str
    schema_definition: List[FieldSchema]
    governance: GovernanceMetadata
    quality_rules: Optional[QualityRules] = None


class DatasetUpdate(BaseModel):
    """Schema for updating a dataset."""
    description: Optional[str] = None
    owner_name: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    schema_definition: Optional[List[FieldSchema]] = None
    governance: Optional[GovernanceMetadata] = None
    quality_rules: Optional[QualityRules] = None
    status: Optional[DatasetStatus] = None


class DatasetResponse(BaseModel):
    """Schema for dataset response."""
    id: int
    name: str
    description: Optional[str]
    owner_name: str
    owner_email: str
    source_type: str
    physical_location: str
    schema_definition: List[Dict[str, Any]]
    classification: str
    contains_pii: bool
    compliance_tags: Optional[List[str]]
    status: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    published_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class SchemaImportRequest(BaseModel):
    """Schema for importing schema from external sources."""
    source_type: SourceType
    table_name: Optional[str] = None  # For database sources
    schema_name: str = "public"  # For database sources
    file_path: Optional[str] = None  # For file sources
    connection_string: Optional[str] = None  # Optional override


class SchemaImportResponse(BaseModel):
    """Response from schema import."""
    table_name: str
    schema_name: str
    description: Optional[str]
    schema_definition: List[FieldSchema]
    metadata: Dict[str, Any]  # contains_pii, suggested_classification, keys, etc.


class TableInfo(BaseModel):
    """Information about a database table."""
    table_name: str
    schema_name: str
    table_type: str
    row_count: Optional[int] = None

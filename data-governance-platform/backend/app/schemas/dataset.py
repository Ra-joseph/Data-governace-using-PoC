"""
Pydantic schemas for dataset management and schema definitions.

This module defines request and response schemas for dataset operations including
field schemas, governance metadata, quality rules, and schema import functionality.
It provides comprehensive data models for dataset lifecycle management and
schema discovery from external sources.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from enum import Enum


class FieldType(str, Enum):
    """
    Field data type enumeration.

    Standardized data types used across all datasets for consistency.

    Attributes:
        STRING: Text/character data (maps to varchar, text, char)
        INTEGER: Whole number data (maps to int, bigint, smallint)
        FLOAT: Decimal number data (maps to decimal, numeric, real, double)
        BOOLEAN: True/false values
        DATE: Date without time (maps to date)
        TIMESTAMP: Date and time (maps to timestamp, datetime)
        JSON: Structured JSON/JSONB data
    """
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    JSON = "json"


class Classification(str, Enum):
    """
    Data classification level enumeration.

    Standard classification levels for data sensitivity and access control.

    Attributes:
        PUBLIC: Publicly accessible data with no restrictions
        INTERNAL: Internal use only, not for external sharing
        CONFIDENTIAL: Sensitive data requiring authorization
        RESTRICTED: Highly sensitive data with strict access controls
    """
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class SourceType(str, Enum):
    """
    Data source type enumeration.

    Supported data source systems for schema import and dataset management.

    Attributes:
        POSTGRES: PostgreSQL database
        FILE: File-based sources (CSV, Parquet, etc.)
        AZURE_BLOB: Azure Blob Storage
        AZURE_ADLS: Azure Data Lake Storage
    """
    POSTGRES = "postgres"
    FILE = "file"
    AZURE_BLOB = "azure_blob"
    AZURE_ADLS = "azure_adls"


class DatasetStatus(str, Enum):
    """
    Dataset lifecycle status enumeration.

    Tracks dataset progression through its lifecycle.

    Attributes:
        DRAFT: Initial state, not yet validated or published
        PUBLISHED: Validated and available for subscription
        DEPRECATED: No longer active, scheduled for retirement
    """
    DRAFT = "draft"
    PUBLISHED = "published"
    DEPRECATED = "deprecated"


class FieldSchema(BaseModel):
    """
    Schema definition for a single dataset field.

    Comprehensive field metadata including type, constraints, governance,
    and validation rules.

    Attributes:
        name: Field name (column name)
        type: Data type from FieldType enum
        required: Whether field must have a value (NOT NULL)
        nullable: Whether field allows null values
        pii: Whether field contains personally identifiable information
        description: Human-readable field description
        max_length: Maximum length for string types
        min_value: Minimum value for numeric types
        max_value: Maximum value for numeric types
        enum_values: List of allowed values for enum fields
        pattern: Regular expression pattern for validation
        foreign_key: Foreign key reference in format "table.column"

    Example:
        {
            "name": "email",
            "type": "string",
            "required": true,
            "pii": true,
            "description": "Customer email address",
            "max_length": 255,
            "pattern": "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        }
    """
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
    """
    Governance metadata and rules for a dataset.

    Defines data governance policies, compliance requirements, access controls,
    and retention policies.

    Attributes:
        classification: Data sensitivity classification level
        encryption_required: Whether data must be encrypted at rest/transit
        retention_days: Data retention period in days (None = indefinite)
        compliance_tags: List of compliance frameworks (GDPR, HIPAA, SOC2, etc.)
        segment_filters: Optional filters for data segmentation by region/team
        approved_use_cases: List of approved business use cases
        data_residency: Geographic data residency requirement (e.g., "EU", "US")

    Example:
        {
            "classification": "confidential",
            "encryption_required": true,
            "retention_days": 2555,
            "compliance_tags": ["GDPR", "SOC2"],
            "data_residency": "EU"
        }
    """
    classification: Classification = Classification.INTERNAL
    encryption_required: bool = False
    retention_days: Optional[int] = None
    compliance_tags: Optional[List[str]] = None
    segment_filters: Optional[Dict[str, Any]] = None
    approved_use_cases: Optional[List[str]] = None
    data_residency: Optional[str] = None


class QualityRules(BaseModel):
    """
    Data quality rules and thresholds.

    Defines expected data quality metrics and SLA requirements for freshness
    and accuracy.

    Attributes:
        completeness_threshold: Minimum acceptable completeness percentage (0-100)
        accuracy_threshold: Minimum acceptable accuracy percentage (0-100)
        freshness_sla: Maximum acceptable data age (e.g., "1h", "24h", "weekly")
        uniqueness_fields: Fields that should have unique values
        custom_rules: Additional custom quality rules as key-value pairs

    Example:
        {
            "completeness_threshold": 95.0,
            "accuracy_threshold": 99.0,
            "freshness_sla": "1h",
            "uniqueness_fields": ["customer_id", "email"]
        }
    """
    completeness_threshold: Optional[float] = Field(None, ge=0, le=100)
    accuracy_threshold: Optional[float] = Field(None, ge=0, le=100)
    freshness_sla: Optional[str] = None  # e.g., "1h", "24h"
    uniqueness_fields: Optional[List[str]] = None
    custom_rules: Optional[Dict[str, Any]] = None


class DatasetCreate(BaseModel):
    """
    Schema for creating a new dataset.

    Request model for dataset creation with complete metadata, schema
    definition, and governance rules.

    Attributes:
        name: Unique dataset name
        description: Human-readable dataset description
        owner_name: Full name of dataset owner
        owner_email: Email address of dataset owner
        source_type: Type of data source (postgres, file, etc.)
        source_connection: Connection string or path to source
        physical_location: Physical location identifier (e.g., "schema.table")
        schema_definition: List of field schemas
        governance: Governance metadata and rules
        quality_rules: Optional data quality requirements
    """
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
    """
    Schema for updating an existing dataset.

    Request model for dataset updates. All fields are optional - only provided
    fields will be updated. Schema changes trigger new contract version creation.

    Attributes:
        description: Updated dataset description
        owner_name: Updated owner name
        owner_email: Updated owner email
        schema_definition: Updated field schemas (triggers new contract version)
        governance: Updated governance metadata
        quality_rules: Updated quality requirements
        status: Updated lifecycle status
    """
    description: Optional[str] = None
    owner_name: Optional[str] = None
    owner_email: Optional[EmailStr] = None
    schema_definition: Optional[List[FieldSchema]] = None
    governance: Optional[GovernanceMetadata] = None
    quality_rules: Optional[QualityRules] = None
    status: Optional[DatasetStatus] = None


class DatasetResponse(BaseModel):
    """
    Schema for dataset response.

    Response model containing complete dataset information including metadata,
    schema, governance rules, and lifecycle status.

    Attributes:
        id: Unique dataset identifier
        name: Dataset name
        description: Dataset description
        owner_name: Owner's full name
        owner_email: Owner's email address
        source_type: Data source type
        physical_location: Physical location identifier
        schema_definition: List of field schemas as dictionaries
        classification: Data classification level
        contains_pii: Whether dataset contains PII fields
        compliance_tags: List of compliance frameworks
        status: Current lifecycle status
        is_active: Whether dataset is active (not soft-deleted)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        published_at: Publication timestamp
    """
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
    """
    Schema for importing schema from external sources.

    Request model for automated schema discovery and import from databases,
    files, or cloud storage.

    Attributes:
        source_type: Type of data source to import from
        table_name: Table name (for database sources)
        schema_name: Database schema name (for database sources, default: "public")
        file_path: File path (for file sources)
        connection_string: Optional connection string override
    """
    source_type: SourceType
    table_name: Optional[str] = None  # For database sources
    schema_name: str = "public"  # For database sources
    file_path: Optional[str] = None  # For file sources
    connection_string: Optional[str] = None  # Optional override


class SchemaImportResponse(BaseModel):
    """
    Response from schema import operation.

    Contains discovered schema information with PII detection and suggested
    governance settings.

    Attributes:
        table_name: Name of the imported table
        schema_name: Database schema name
        description: Table description (from metadata or generated)
        schema_definition: List of discovered field schemas
        metadata: Additional metadata including:
            - contains_pii: Boolean PII detection result
            - suggested_classification: Recommended classification level
            - primary_keys: List of primary key columns
            - foreign_keys: Dictionary of foreign key relationships
            - indexes: List of index names
            - row_count: Approximate row count
            - total_size: Human-readable table size
    """
    table_name: str
    schema_name: str
    description: Optional[str]
    schema_definition: List[FieldSchema]
    metadata: Dict[str, Any]  # contains_pii, suggested_classification, keys, etc.


class TableInfo(BaseModel):
    """
    Information about a database table.

    Metadata about tables available for import.

    Attributes:
        table_name: Name of the table
        schema_name: Database schema containing the table
        table_type: Type of object (BASE TABLE, VIEW, etc.)
        row_count: Optional approximate row count
    """
    table_name: str
    schema_name: str
    table_type: str
    row_count: Optional[int] = None

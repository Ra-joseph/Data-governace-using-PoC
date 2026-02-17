"""
Dataset model for data asset catalog.

This module defines the Dataset SQLAlchemy model which represents data assets
in the governance platform. Datasets include metadata about source, schema,
ownership, governance classification, and lifecycle status. Each dataset can
have multiple contract versions and subscriptions.
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Dataset(Base):
    """
    Dataset model representing a data asset in the catalog.

    Stores comprehensive metadata about data assets including source information,
    schema definition, governance classification, ownership, and lifecycle status.
    Datasets are the primary entities in the governance platform and can have
    multiple contract versions and consumer subscriptions.

    Attributes:
        id: Primary key.
        name: Unique dataset name/identifier.
        description: Human-readable description of the dataset.
        owner_id: Foreign key to owning user.
        owner_name: Dataset owner's full name.
        owner_email: Dataset owner's contact email.
        source_type: Type of data source (postgres/file/azure_blob/azure_adls).
        source_connection: Connection details for the data source.
        physical_location: Physical location (table name, file path, blob URL).
        schema_definition: JSON schema with field definitions and metadata.
        classification: Data classification level (public/internal/confidential/restricted).
        contains_pii: Whether the dataset contains personally identifiable information.
        compliance_tags: List of applicable compliance frameworks (GDPR, CCPA, HIPAA).
        status: Lifecycle status (draft/published/deprecated).
        is_active: Whether the dataset is currently active.
        created_at: Dataset registration timestamp.
        updated_at: Last update timestamp.
        published_at: Publication timestamp (when status changed to published).

    Relationships:
        owner: User who owns this dataset.
        contracts: List of contract versions for this dataset.
        subscriptions: List of consumer subscriptions to this dataset.
    """
    
    __tablename__ = "datasets"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic Information
    name = Column(String(255), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Ownership
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner_name = Column(String(255), nullable=False)
    owner_email = Column(String(255), nullable=False)
    
    # Source Information
    source_type = Column(String(50), nullable=False)  # postgres, file, azure_blob, azure_adls
    source_connection = Column(Text, nullable=True)  # Connection details (encrypted in production)
    physical_location = Column(Text, nullable=False)  # Table name, file path, blob URL
    
    # Schema Definition
    schema_definition = Column(JSON, nullable=False)  # List of field definitions
    
    # Governance Metadata
    classification = Column(String(50), nullable=False, default="internal")  # public, internal, confidential, restricted
    contains_pii = Column(Boolean, default=False)
    compliance_tags = Column(JSON, nullable=True)  # List of compliance frameworks [GDPR, CCPA, HIPAA]
    
    # Status
    status = Column(String(50), nullable=False, default="draft")  # draft, published, deprecated
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="datasets")
    contracts = relationship("Contract", back_populates="dataset", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="dataset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dataset(name='{self.name}', classification='{self.classification}', status='{self.status}')>"

"""
Contract model for data contract versioning.

This module defines the Contract SQLAlchemy model which represents versioned
data contracts. Each contract is associated with a dataset and includes both
human-readable (YAML) and machine-readable (JSON) formats, validation results,
Git integration for version control, and approval workflow tracking.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Contract(Base):
    """
    Contract model representing a data contract version.

    Stores versioned data contracts with dual formats (YAML and JSON),
    validation results, Git integration, and approval tracking. Each
    contract is linked to a dataset and follows semantic versioning.

    Attributes:
        id: Primary key.
        dataset_id: Foreign key to associated dataset.
        version: Semantic version string (e.g., "1.0.0").
        human_readable: Contract in YAML format for readability.
        machine_readable: Contract in JSON format for automation.
        schema_hash: SHA-256 hash of the schema for change detection.
        governance_rules: Governance metadata (classification, retention, etc.).
        quality_rules: Data quality thresholds and requirements.
        sla_requirements: Service level agreements for data access.
        validation_status: Current validation state (pending/passed/failed).
        validation_results: Detailed validation report with violations.
        last_validated_at: Timestamp of last validation run.
        git_commit_hash: Git commit SHA for version control.
        git_file_path: Path to contract file in Git repository.
        approved_by: User ID who approved the contract.
        approved_at: Timestamp of approval.
        approval_comments: Reviewer comments.
        created_at: Contract creation timestamp.

    Relationships:
        dataset: Associated Dataset object.
        approver: User who approved the contract.
        subscriptions: List of subscriptions using this contract version.
    """
    
    __tablename__ = "contracts"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Dataset Reference
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    
    # Version
    version = Column(String(50), nullable=False)  # Semantic versioning: 1.0.0
    
    # Contract Content
    human_readable = Column(Text, nullable=False)  # YAML format
    machine_readable = Column(JSON, nullable=False)  # JSON format
    
    # Components
    schema_hash = Column(String(64), nullable=False)  # SHA-256 hash of schema
    governance_rules = Column(JSON, nullable=True)
    quality_rules = Column(JSON, nullable=True)
    sla_requirements = Column(JSON, nullable=True)
    
    # Validation
    validation_status = Column(String(50), nullable=False, default="pending")  # pending, passed, failed
    validation_results = Column(JSON, nullable=True)  # Validation report
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Git Integration
    git_commit_hash = Column(String(40), nullable=True)
    git_file_path = Column(String(500), nullable=True)
    
    # Approval
    approved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approval_comments = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    dataset = relationship("Dataset", back_populates="contracts")
    approver = relationship("User", foreign_keys=[approved_by])
    subscriptions = relationship("Subscription", back_populates="contract")
    
    def __repr__(self):
        return f"<Contract(dataset_id={self.dataset_id}, version='{self.version}', status='{self.validation_status}')>"

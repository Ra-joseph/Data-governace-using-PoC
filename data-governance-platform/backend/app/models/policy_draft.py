"""
Policy draft model for policy-as-code authoring.

This module defines the PolicyDraft SQLAlchemy model which represents governance
policies authored in plain English. Policies go through a draft/approval workflow
before being converted to YAML/JSON artifacts and committed to Git.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PolicyDraft(Base):
    """
    PolicyDraft model representing an authored governance policy.

    Attributes:
        id: Primary key (auto-increment integer, consistent with existing models).
        policy_uid: UUID string for external references and YAML artifacts.
        title: Short policy title.
        description: Full plain-English policy statement.
        policy_category: Category enum (data_quality, security, privacy, compliance, lineage, sla).
        affected_domains: JSON list of domain names, or ["ALL"].
        severity: Severity enum (CRITICAL, WARNING, INFO).
        scanner_hint: Scanner routing hint (rule_based, ai_semantic, auto).
        remediation_guide: Mandatory remediation instructions.
        effective_date: Date the policy takes effect.
        authored_by: Free-text author identity (defaults to "Data Governance Expert").
        status: Workflow status (draft, pending_approval, approved, rejected, deprecated).
        version: Integer version, incremented on each approval cycle.
        created_at: Auto-set creation timestamp.
        updated_at: Auto-set update timestamp.
    """

    __tablename__ = "policy_drafts"

    id = Column(Integer, primary_key=True, index=True)
    policy_uid = Column(String(36), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    policy_category = Column(String(50), nullable=False)
    affected_domains = Column(JSON, nullable=False, default=["ALL"])
    severity = Column(String(20), nullable=False, default="WARNING")
    scanner_hint = Column(String(20), nullable=False, default="auto")
    remediation_guide = Column(Text, nullable=True)
    effective_date = Column(Date, nullable=True)
    authored_by = Column(String(255), nullable=False, default="Data Governance Expert")
    status = Column(String(30), nullable=False, default="draft")
    version = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    versions = relationship("PolicyVersion", back_populates="policy", cascade="all, delete-orphan")
    artifacts = relationship("PolicyArtifact", back_populates="policy", cascade="all, delete-orphan")
    approval_logs = relationship("PolicyApprovalLog", back_populates="policy", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<PolicyDraft(title='{self.title}', status='{self.status}', version={self.version})>"

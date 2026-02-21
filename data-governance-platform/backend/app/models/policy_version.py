"""
Policy version model for immutable version history.

Each time a policy is approved or revised, a snapshot is stored
as a PolicyVersion record for full audit trail.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PolicyVersion(Base):
    """
    Immutable snapshot of a policy at a specific version.

    Attributes:
        id: Primary key.
        policy_id: FK to PolicyDraft.
        version: Version number at time of snapshot.
        title: Policy title at this version.
        description: Full description at this version.
        policy_category: Category at this version.
        affected_domains: Domains at this version.
        severity: Severity at this version.
        scanner_hint: Scanner hint at this version.
        remediation_guide: Remediation text at this version.
        effective_date: Effective date at this version.
        authored_by: Author at this version.
        approved_by: Approver name (set on approval).
        status: Status that triggered the snapshot (approved, rejected).
        created_at: Timestamp of the snapshot.
    """

    __tablename__ = "policy_versions"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policy_drafts.id"), nullable=False)
    version = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    policy_category = Column(String(50), nullable=False)
    affected_domains = Column(JSON, nullable=False)
    severity = Column(String(20), nullable=False)
    scanner_hint = Column(String(20), nullable=False)
    remediation_guide = Column(Text, nullable=True)
    effective_date = Column(Date, nullable=True)
    authored_by = Column(String(255), nullable=False)
    approved_by = Column(String(255), nullable=True)
    status = Column(String(30), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    policy = relationship("PolicyDraft", back_populates="versions")

    def __repr__(self):
        return f"<PolicyVersion(policy_id={self.policy_id}, version={self.version}, status='{self.status}')>"

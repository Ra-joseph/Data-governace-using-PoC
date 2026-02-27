"""
Policy approval log model for audit trail.

Every status transition (submitted, approved, rejected, deprecated)
is recorded as an immutable log entry for compliance auditing.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PolicyApprovalLog(Base):
    """
    Immutable audit log entry for policy workflow actions.

    Attributes:
        id: Primary key.
        policy_id: FK to PolicyDraft.
        action: Action performed (submitted, approved, rejected, deprecated).
        actor_name: Free-text identity of who performed the action.
        comment: Optional comment (mandatory on rejection).
        timestamp: Auto-set, never updated.
    """

    __tablename__ = "policy_approval_logs"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policy_drafts.id"), nullable=False)
    action = Column(String(30), nullable=False)
    actor_name = Column(String(255), nullable=False)
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    policy = relationship("PolicyDraft", back_populates="approval_logs")

    def __repr__(self):
        return f"<PolicyApprovalLog(policy_id={self.policy_id}, action='{self.action}', actor='{self.actor_name}')>"

"""
Policy artifact model for generated YAML and JSON outputs.

When a policy is approved, the conversion engine generates YAML and JSON
representations. These are stored here and also committed to Git.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class PolicyArtifact(Base):
    """
    Generated YAML/JSON artifact for an approved policy.

    Attributes:
        id: Primary key.
        policy_id: FK to PolicyDraft.
        version: Version of the policy this artifact represents.
        yaml_content: Generated YAML text.
        json_content: Generated JSON text.
        scanner_type: Resolved scanner type (rule_based or ai_semantic).
        git_commit_hash: Git commit SHA after committing the YAML.
        git_file_path: Path to the YAML file in the Git repo.
        generated_at: Timestamp of artifact generation.
    """

    __tablename__ = "policy_artifacts"

    id = Column(Integer, primary_key=True, index=True)
    policy_id = Column(Integer, ForeignKey("policy_drafts.id"), nullable=False)
    version = Column(Integer, nullable=False)
    yaml_content = Column(Text, nullable=False)
    json_content = Column(Text, nullable=False)
    scanner_type = Column(String(20), nullable=False)
    git_commit_hash = Column(String(40), nullable=True)
    git_file_path = Column(String(500), nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    policy = relationship("PolicyDraft", back_populates="artifacts")

    def __repr__(self):
        return f"<PolicyArtifact(policy_id={self.policy_id}, version={self.version}, scanner='{self.scanner_type}')>"

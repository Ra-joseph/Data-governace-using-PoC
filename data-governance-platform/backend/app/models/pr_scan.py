"""
PR Scan model for tracking governance agent PR scan results.

This module defines the PRScan SQLAlchemy model which represents the results
of automated governance policy scans on GitHub pull requests. Each scan record
tracks the PR metadata, validation results, and GitHub feedback status.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.database import Base


class PRScan(Base):
    """
    PR Scan model representing a governance scan of a GitHub pull request.

    Stores scan results including validation outcomes, violation summaries,
    and GitHub integration metadata (check runs, review comments).

    Attributes:
        id: Primary key.
        github_repo: Repository full name (owner/repo).
        pr_number: Pull request number.
        pr_title: Pull request title.
        pr_author: PR author's GitHub username.
        head_sha: Commit SHA that triggered the scan.
        base_branch: Target branch of the PR.
        head_branch: Source branch of the PR.
        scan_status: Current scan status (pending/running/passed/warning/failed/error).
        total_files_scanned: Number of governance-relevant files scanned.
        contracts_found: Number of contract/schema files found.
        validation_results: Full validation results per file (JSON).
        violations_summary: Summary counts {critical, warning, info} (JSON).
        strategy_used: Orchestration strategy used (FAST/BALANCED/THOROUGH/ADAPTIVE).
        scan_duration_ms: Duration of the scan in milliseconds.
        check_run_id: GitHub Check Run ID for status updates.
        review_comment_ids: List of GitHub review comment IDs (JSON).
        triggered_at: Timestamp when scan was triggered.
        completed_at: Timestamp when scan completed.
    """

    __tablename__ = "pr_scans"

    id = Column(Integer, primary_key=True, index=True)

    # GitHub PR metadata
    github_repo = Column(String(255), nullable=False)
    pr_number = Column(Integer, nullable=False)
    pr_title = Column(String(500), nullable=True)
    pr_author = Column(String(255), nullable=True)
    head_sha = Column(String(40), nullable=False)
    base_branch = Column(String(255), nullable=True)
    head_branch = Column(String(255), nullable=True)

    # Scan results
    scan_status = Column(String(50), nullable=False, default="pending")
    total_files_scanned = Column(Integer, default=0)
    contracts_found = Column(Integer, default=0)
    validation_results = Column(JSON, nullable=True)
    violations_summary = Column(JSON, nullable=True)

    # Orchestration metadata
    strategy_used = Column(String(50), nullable=True)
    scan_duration_ms = Column(Integer, nullable=True)

    # GitHub feedback
    check_run_id = Column(String(100), nullable=True)
    review_comment_ids = Column(JSON, nullable=True)

    # Timestamps
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index('ix_pr_scans_repo_pr', 'github_repo', 'pr_number'),
    )

    def __repr__(self):
        return f"<PRScan(repo='{self.github_repo}', pr={self.pr_number}, status='{self.scan_status}')>"

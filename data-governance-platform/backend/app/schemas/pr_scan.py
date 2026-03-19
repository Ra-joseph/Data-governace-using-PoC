"""
Pydantic schemas for PR governance scanning.

This module defines request and response schemas for the PR governance agent,
including webhook payloads, scan results, and dashboard statistics.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class PRScanStatus(str, Enum):
    """PR scan status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    WARNING = "warning"
    FAILED = "failed"
    ERROR = "error"


class GitHubFileChange(BaseModel):
    """Represents a changed file from a GitHub PR."""
    filename: str
    status: str  # added, modified, removed, renamed
    additions: int = 0
    deletions: int = 0
    patch: Optional[str] = None
    content: Optional[str] = None
    is_governance_relevant: bool = False


class FileValidationResult(BaseModel):
    """Validation result for a single file in a PR."""
    filename: str
    status: str  # passed, warning, failed, skipped
    violations_count: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    violations: List[Dict[str, Any]] = []
    error: Optional[str] = None


class PRScanCreate(BaseModel):
    """Internal schema for creating a PR scan record."""
    github_repo: str
    pr_number: int
    pr_title: Optional[str] = None
    pr_author: Optional[str] = None
    head_sha: str
    base_branch: Optional[str] = None
    head_branch: Optional[str] = None


class PRScanResponse(BaseModel):
    """Response schema for a PR scan."""
    id: int
    github_repo: str
    pr_number: int
    pr_title: Optional[str] = None
    pr_author: Optional[str] = None
    head_sha: str
    base_branch: Optional[str] = None
    head_branch: Optional[str] = None
    scan_status: str
    total_files_scanned: int = 0
    contracts_found: int = 0
    validation_results: Optional[Dict[str, Any]] = None
    violations_summary: Optional[Dict[str, Any]] = None
    strategy_used: Optional[str] = None
    scan_duration_ms: Optional[int] = None
    check_run_id: Optional[str] = None
    triggered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PRScanListResponse(BaseModel):
    """Paginated list of PR scans."""
    scans: List[PRScanResponse]
    total: int


class PRScanSummary(BaseModel):
    """Lightweight summary for dashboard cards."""
    total_scans: int = 0
    passed: int = 0
    warnings: int = 0
    failed: int = 0
    error: int = 0
    pass_rate: float = 0.0
    avg_violations: float = 0.0
    avg_duration_ms: float = 0.0
    blocked_prs: int = 0


class ManualScanRequest(BaseModel):
    """Request to manually trigger a PR scan."""
    repo: str = Field(..., description="Repository full name (owner/repo)")
    pr_number: int = Field(..., description="Pull request number")
    strategy: Optional[str] = Field(None, description="Validation strategy override")

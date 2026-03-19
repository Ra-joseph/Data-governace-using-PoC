"""
PR Governance API endpoints.

This module provides endpoints for the PR Governance Agent, including
GitHub webhook receiver, scan history queries, manual scan triggers,
and dashboard statistics.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.github_client import GitHubClient
from app.services.pr_scan_service import PRScanService
from app.schemas.pr_scan import (
    PRScanResponse,
    PRScanListResponse,
    PRScanSummary,
    ManualScanRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pr-governance", tags=["pr-governance"])


def _get_scan_service(db: Session = Depends(get_db)) -> PRScanService:
    """Create PRScanService with database session."""
    return PRScanService(db=db)


@router.post("/webhook", status_code=202)
async def github_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Receive GitHub webhook events for PR scanning.

    Verifies the webhook signature, checks for pull_request events,
    and triggers a governance scan. Returns 202 Accepted.

    Headers:
        X-Hub-Signature-256: HMAC-SHA256 signature.
        X-GitHub-Event: Event type (must be pull_request).
    """
    # Read raw body for signature verification
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    event_type = request.headers.get("X-GitHub-Event", "")

    # Verify signature
    github_client = GitHubClient()
    if not github_client.verify_webhook_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Only process pull_request events
    if event_type != "pull_request":
        return {"status": "ignored", "reason": f"Event type '{event_type}' not handled"}

    # Parse payload
    import json
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Handle the event
    service = PRScanService(db=db, github_client=github_client)
    scan = service.handle_pr_event(payload)

    if scan is None:
        return {"status": "ignored", "reason": "PR action not relevant"}

    return {
        "status": "accepted",
        "scan_id": scan.id,
        "scan_status": scan.scan_status,
    }


@router.get("/scans", response_model=PRScanListResponse)
def list_scans(
    repo: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    service: PRScanService = Depends(_get_scan_service),
):
    """
    List PR scan history with optional filters.

    Args:
        repo: Filter by repository name.
        status: Filter by scan status.
        limit: Max results (default 50).
        offset: Pagination offset.
    """
    scans, total = service.get_scan_history(
        repo=repo, status=status, limit=limit, offset=offset
    )
    return PRScanListResponse(
        scans=[PRScanResponse.model_validate(s) for s in scans],
        total=total,
    )


@router.get("/scans/{scan_id}", response_model=PRScanResponse)
def get_scan(
    scan_id: int,
    service: PRScanService = Depends(_get_scan_service),
):
    """Get detailed results for a specific scan."""
    scan = service.get_scan_detail(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return PRScanResponse.model_validate(scan)


@router.post("/scans/{scan_id}/rescan")
def rescan_pr(
    scan_id: int,
    service: PRScanService = Depends(_get_scan_service),
):
    """Re-trigger a scan for a previously scanned PR."""
    original = service.get_scan_detail(scan_id)
    if not original:
        raise HTTPException(status_code=404, detail="Original scan not found")

    new_scan = service.scan_pr(
        repo=original.github_repo,
        pr_number=original.pr_number,
        head_sha=original.head_sha,
        pr_title=original.pr_title,
        pr_author=original.pr_author,
        base_branch=original.base_branch,
        head_branch=original.head_branch,
    )

    return {
        "status": "completed",
        "original_scan_id": scan_id,
        "new_scan_id": new_scan.id,
        "scan_status": new_scan.scan_status,
    }


@router.get("/stats", response_model=PRScanSummary)
def get_stats(service: PRScanService = Depends(_get_scan_service)):
    """Get dashboard statistics for PR governance scans."""
    stats = service.get_stats()
    return PRScanSummary(**stats)


@router.post("/scan-manual")
def manual_scan(
    request: ManualScanRequest,
    service: PRScanService = Depends(_get_scan_service),
):
    """
    Manually trigger a governance scan on a PR.

    Useful for testing or re-scanning without a webhook event.
    Requires GITHUB_TOKEN to be configured.
    """
    if not service.github_client.is_configured():
        raise HTTPException(
            status_code=400,
            detail="GitHub token not configured. Set GITHUB_TOKEN environment variable.",
        )

    # Fetch PR details to get head_sha
    pr_details = service.github_client.get_pr_details(
        request.repo, request.pr_number
    )
    if not pr_details:
        raise HTTPException(
            status_code=404,
            detail=f"PR #{request.pr_number} not found in {request.repo}",
        )

    head_sha = pr_details.get("head", {}).get("sha", "")
    if not head_sha:
        raise HTTPException(status_code=400, detail="Could not determine head SHA")

    scan = service.scan_pr(
        repo=request.repo,
        pr_number=request.pr_number,
        head_sha=head_sha,
        pr_title=pr_details.get("title"),
        pr_author=pr_details.get("user", {}).get("login"),
        base_branch=pr_details.get("base", {}).get("ref"),
        head_branch=pr_details.get("head", {}).get("ref"),
        strategy_override=request.strategy,
    )

    return {
        "status": "completed",
        "scan_id": scan.id,
        "scan_status": scan.scan_status,
        "violations_summary": scan.violations_summary,
    }

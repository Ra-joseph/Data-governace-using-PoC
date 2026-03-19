"""
PR Scan Service - orchestrates the PR governance scanning lifecycle.

This service handles the complete PR scan workflow: receiving PR events,
fetching changed files, parsing governance-relevant content, validating
against policies via the PolicyOrchestrator, posting results to GitHub,
and storing scan records for audit trail.
"""

import time
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.orm import Session

from app.config import settings
from app.models.pr_scan import PRScan
from app.services.github_client import GitHubClient
from app.services.diff_parser import (
    filter_governance_files,
    parse_pr_files,
)
from app.services.policy_orchestrator import PolicyOrchestrator, ValidationStrategy

logger = logging.getLogger(__name__)

# Map string strategy names to enum values
STRATEGY_MAP = {
    "FAST": ValidationStrategy.FAST,
    "BALANCED": ValidationStrategy.BALANCED,
    "THOROUGH": ValidationStrategy.THOROUGH,
    "ADAPTIVE": ValidationStrategy.ADAPTIVE,
}


class PRScanService:
    """
    Service for orchestrating PR governance scans.

    Manages the full scan lifecycle from PR event handling through
    validation and GitHub feedback posting.
    """

    def __init__(
        self,
        db: Session,
        github_client: Optional[GitHubClient] = None,
    ):
        self.db = db
        self.github_client = github_client or GitHubClient()
        strategy_name = settings.PR_SCAN_STRATEGY.upper()
        self.default_strategy = STRATEGY_MAP.get(
            strategy_name, ValidationStrategy.BALANCED
        )
        self.orchestrator = PolicyOrchestrator(
            enable_semantic=settings.ENABLE_LLM_VALIDATION,
            default_strategy=self.default_strategy,
        )

    def handle_pr_event(self, payload: Dict[str, Any]) -> Optional[PRScan]:
        """
        Handle a GitHub pull_request webhook event.

        Extracts PR metadata from the payload and triggers a scan
        for relevant actions (opened, synchronize, reopened).

        Args:
            payload: GitHub webhook payload dictionary.

        Returns:
            PRScan record if scan was triggered, None otherwise.
        """
        action = payload.get("action", "")
        if action not in ("opened", "synchronize", "reopened"):
            logger.info(f"Ignoring PR event with action: {action}")
            return None

        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {}).get("full_name", "")
        pr_number = pr.get("number", 0)
        head_sha = pr.get("head", {}).get("sha", "")

        if not repo or not pr_number or not head_sha:
            logger.error("Missing required fields in webhook payload")
            return None

        return self.scan_pr(
            repo=repo,
            pr_number=pr_number,
            head_sha=head_sha,
            pr_title=pr.get("title"),
            pr_author=pr.get("user", {}).get("login"),
            base_branch=pr.get("base", {}).get("ref"),
            head_branch=pr.get("head", {}).get("ref"),
        )

    def scan_pr(
        self,
        repo: str,
        pr_number: int,
        head_sha: str,
        pr_title: Optional[str] = None,
        pr_author: Optional[str] = None,
        base_branch: Optional[str] = None,
        head_branch: Optional[str] = None,
        strategy_override: Optional[str] = None,
    ) -> PRScan:
        """
        Execute a full governance scan on a pull request.

        Lifecycle:
        1. Create scan record (status: running)
        2. Fetch PR files from GitHub
        3. Filter to governance-relevant files
        4. Fetch full content for each relevant file
        5. Parse and validate each file against policies
        6. Aggregate results
        7. Post check run and review to GitHub
        8. Update scan record with results

        Args:
            repo: Repository full name (owner/repo).
            pr_number: Pull request number.
            head_sha: Commit SHA that triggered the scan.
            pr_title: PR title for display.
            pr_author: PR author username.
            base_branch: Target branch.
            head_branch: Source branch.
            strategy_override: Optional strategy override.

        Returns:
            Completed PRScan record.
        """
        start_time = time.time()

        # Create scan record
        scan = PRScan(
            github_repo=repo,
            pr_number=pr_number,
            pr_title=pr_title,
            pr_author=pr_author,
            head_sha=head_sha,
            base_branch=base_branch,
            head_branch=head_branch,
            scan_status="running",
            strategy_used=strategy_override or settings.PR_SCAN_STRATEGY,
        )
        self.db.add(scan)
        self.db.commit()
        self.db.refresh(scan)

        try:
            # Post initial check run (in_progress)
            check_run = None
            if self.github_client.is_configured():
                check_run = self.github_client.create_check_run(
                    repo=repo,
                    head_sha=head_sha,
                    name="Governance Policy Scan",
                    status="in_progress",
                    title="Scanning for governance violations...",
                    summary="The governance agent is validating data contracts and schemas.",
                )
                if check_run:
                    scan.check_run_id = str(check_run.get("id", ""))

            # Fetch PR files
            pr_files = self.github_client.get_pr_files(repo, pr_number)
            relevant_files = filter_governance_files(pr_files)

            scan.total_files_scanned = len(relevant_files)
            scan.contracts_found = len(relevant_files)

            if not relevant_files:
                # No governance-relevant files changed
                scan.scan_status = "passed"
                scan.validation_results = {
                    "message": "No governance-relevant files changed in this PR",
                    "files_checked": 0,
                    "file_results": [],
                }
                scan.violations_summary = {
                    "critical": 0,
                    "warning": 0,
                    "info": 0,
                }
                self._post_check_result(
                    scan, repo, head_sha, "success",
                    "No governance-relevant files found",
                    "This PR does not modify any data contracts, schemas, or policy files.",
                )
                self._finalize_scan(scan, start_time)
                return scan

            # Fetch content for each relevant file
            file_contents = {}
            for f in relevant_files:
                filename = f.get("filename", "")
                content = self.github_client.get_file_content(
                    repo, filename, head_sha
                )
                if content:
                    file_contents[filename] = content

            # Parse and validate
            contracts = parse_pr_files(relevant_files, file_contents)
            file_results = []
            total_critical = 0
            total_warning = 0
            total_info = 0

            strategy = self.default_strategy
            if strategy_override:
                strategy = STRATEGY_MAP.get(
                    strategy_override.upper(), self.default_strategy
                )

            for filename, contract_data in contracts:
                try:
                    result = self.orchestrator.validate_contract(
                        contract_data, strategy=strategy
                    )
                    critical = sum(
                        1 for v in result.violations if v.type.value == "critical"
                    )
                    warning = sum(
                        1 for v in result.violations if v.type.value == "warning"
                    )
                    info = sum(
                        1 for v in result.violations if v.type.value == "info"
                    )

                    file_results.append({
                        "filename": filename,
                        "status": result.status.value,
                        "violations_count": len(result.violations),
                        "critical_count": critical,
                        "warning_count": warning,
                        "info_count": info,
                        "violations": [
                            {
                                "type": v.type.value,
                                "policy": v.policy,
                                "field": v.field,
                                "message": v.message,
                                "remediation": v.remediation,
                            }
                            for v in result.violations
                        ],
                    })

                    total_critical += critical
                    total_warning += warning
                    total_info += info

                except Exception as e:
                    logger.error(f"Validation failed for {filename}: {e}")
                    file_results.append({
                        "filename": filename,
                        "status": "error",
                        "violations_count": 0,
                        "critical_count": 0,
                        "warning_count": 0,
                        "info_count": 0,
                        "violations": [],
                        "error": str(e),
                    })

            # Determine overall status
            if total_critical > 0:
                scan.scan_status = "failed"
            elif total_warning > 0:
                scan.scan_status = "warning"
            else:
                scan.scan_status = "passed"

            scan.validation_results = {
                "files_checked": len(contracts),
                "file_results": file_results,
            }
            scan.violations_summary = {
                "critical": total_critical,
                "warning": total_warning,
                "info": total_info,
            }

            # Post results to GitHub
            self._post_scan_results(scan, repo, pr_number, head_sha, file_results)

            self._finalize_scan(scan, start_time)
            return scan

        except Exception as e:
            logger.error(f"PR scan failed: {e}", exc_info=True)
            scan.scan_status = "error"
            scan.validation_results = {"error": str(e)}
            scan.violations_summary = {"critical": 0, "warning": 0, "info": 0}
            self._finalize_scan(scan, start_time)
            return scan

    def _post_scan_results(
        self,
        scan: PRScan,
        repo: str,
        pr_number: int,
        head_sha: str,
        file_results: List[Dict],
    ) -> None:
        """Post scan results to GitHub as check run and PR review."""
        if not self.github_client.is_configured():
            return

        # Determine check conclusion
        if scan.scan_status == "failed" and settings.PR_SCAN_BLOCK_ON_CRITICAL:
            conclusion = "failure"
        elif scan.scan_status == "warning":
            conclusion = "neutral"
        else:
            conclusion = "success"

        # Build summary
        summary = scan.violations_summary or {}
        total_violations = (
            summary.get("critical", 0)
            + summary.get("warning", 0)
            + summary.get("info", 0)
        )

        summary_text = (
            f"## Governance Scan Results\n\n"
            f"**Status**: {scan.scan_status.upper()}\n"
            f"**Files Scanned**: {scan.total_files_scanned}\n"
            f"**Total Violations**: {total_violations}\n"
            f"- Critical: {summary.get('critical', 0)}\n"
            f"- Warning: {summary.get('warning', 0)}\n"
            f"- Info: {summary.get('info', 0)}\n"
        )

        # Add per-file details
        detail_text = ""
        for fr in file_results:
            status_icon = {
                "passed": "✅", "warning": "⚠️", "failed": "❌", "error": "💥"
            }.get(fr["status"], "❓")
            detail_text += (
                f"\n### {status_icon} {fr['filename']}\n"
                f"Violations: {fr['violations_count']}\n"
            )
            for v in fr.get("violations", []):
                severity_icon = {
                    "critical": "🔴", "warning": "🟡", "info": "🔵"
                }.get(v["type"], "⚪")
                detail_text += (
                    f"- {severity_icon} **{v['policy']}**"
                    f"{(' (field: ' + v['field'] + ')') if v.get('field') else ''}: "
                    f"{v['message']}\n"
                    f"  - Remediation: {v['remediation']}\n"
                )

        # Post check run
        self._post_check_result(
            scan, repo, head_sha, conclusion,
            f"Governance Scan: {total_violations} violation(s) found",
            summary_text + detail_text,
        )

        # Post PR review if there are violations
        if total_violations > 0:
            review_body = (
                f"## 🛡️ Governance Policy Scan\n\n"
                f"{summary_text}\n"
                f"{'**This PR is blocked from merging** due to critical governance violations.' if conclusion == 'failure' else ''}\n"
                f"{detail_text}"
            )

            event = "REQUEST_CHANGES" if conclusion == "failure" else "COMMENT"
            self.github_client.create_pr_review(
                repo=repo,
                pr_number=pr_number,
                body=review_body,
                event=event,
            )

    def _post_check_result(
        self,
        scan: PRScan,
        repo: str,
        head_sha: str,
        conclusion: str,
        title: str,
        summary: str,
    ) -> None:
        """Post or update a GitHub check run with final results."""
        if not self.github_client.is_configured():
            return

        self.github_client.create_check_run(
            repo=repo,
            head_sha=head_sha,
            name="Governance Policy Scan",
            status="completed",
            conclusion=conclusion,
            title=title,
            summary=summary,
        )

    def _finalize_scan(self, scan: PRScan, start_time: float) -> None:
        """Finalize scan record with timing and persist."""
        scan.scan_duration_ms = int((time.time() - start_time) * 1000)
        scan.completed_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(scan)

    def get_scan_history(
        self,
        repo: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple:
        """
        Query scan history with optional filters.

        Args:
            repo: Filter by repository name.
            status: Filter by scan status.
            limit: Max results to return.
            offset: Pagination offset.

        Returns:
            Tuple of (scans list, total count).
        """
        query = self.db.query(PRScan)

        if repo:
            query = query.filter(PRScan.github_repo == repo)
        if status:
            query = query.filter(PRScan.scan_status == status)

        total = query.count()
        scans = (
            query.order_by(PRScan.triggered_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

        return scans, total

    def get_scan_detail(self, scan_id: int) -> Optional[PRScan]:
        """Get a single scan by ID."""
        return self.db.query(PRScan).filter(PRScan.id == scan_id).first()

    def get_scans_by_pr(
        self, repo: str, pr_number: int
    ) -> List[PRScan]:
        """Get all scans for a specific PR."""
        return (
            self.db.query(PRScan)
            .filter(
                PRScan.github_repo == repo,
                PRScan.pr_number == pr_number,
            )
            .order_by(PRScan.triggered_at.desc())
            .all()
        )

    def get_stats(self) -> Dict[str, Any]:
        """
        Calculate dashboard statistics from scan history.

        Returns:
            Dict with total scans, pass rate, avg violations, etc.
        """
        all_scans = self.db.query(PRScan).all()
        total = len(all_scans)

        if total == 0:
            return {
                "total_scans": 0,
                "passed": 0,
                "warnings": 0,
                "failed": 0,
                "error": 0,
                "pass_rate": 0.0,
                "avg_violations": 0.0,
                "avg_duration_ms": 0.0,
                "blocked_prs": 0,
            }

        passed = sum(1 for s in all_scans if s.scan_status == "passed")
        warnings = sum(1 for s in all_scans if s.scan_status == "warning")
        failed = sum(1 for s in all_scans if s.scan_status == "failed")
        errors = sum(1 for s in all_scans if s.scan_status == "error")

        total_violations = 0
        for s in all_scans:
            if s.violations_summary:
                total_violations += sum(s.violations_summary.values())

        durations = [
            s.scan_duration_ms for s in all_scans if s.scan_duration_ms
        ]
        avg_duration = sum(durations) / len(durations) if durations else 0

        return {
            "total_scans": total,
            "passed": passed,
            "warnings": warnings,
            "failed": failed,
            "error": errors,
            "pass_rate": round((passed / total) * 100, 1) if total > 0 else 0.0,
            "avg_violations": round(total_violations / total, 1) if total > 0 else 0.0,
            "avg_duration_ms": round(avg_duration, 0),
            "blocked_prs": failed,
        }

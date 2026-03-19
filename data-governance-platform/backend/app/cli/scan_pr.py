"""
CLI entrypoint for PR governance scanning.

This script allows running governance policy scans on pull requests
from the command line or as part of a CI/CD pipeline (e.g., GitHub Actions).

Usage:
    python -m app.cli.scan_pr --repo owner/repo --pr 123 --sha abc123
"""

import argparse
import json
import sys

from app.database import SessionLocal, init_db
from app.services.github_client import GitHubClient
from app.services.pr_scan_service import PRScanService


def main():
    """Run a governance scan on a pull request."""
    parser = argparse.ArgumentParser(
        description="Scan a GitHub pull request for governance policy violations"
    )
    parser.add_argument(
        "--repo", required=True, help="Repository full name (owner/repo)"
    )
    parser.add_argument(
        "--pr", required=True, type=int, help="Pull request number"
    )
    parser.add_argument(
        "--sha", required=True, help="Head commit SHA"
    )
    parser.add_argument(
        "--strategy",
        default=None,
        choices=["FAST", "BALANCED", "THOROUGH", "ADAPTIVE"],
        help="Validation strategy (default: from config)",
    )
    parser.add_argument(
        "--output",
        default="text",
        choices=["text", "json"],
        help="Output format (default: text)",
    )

    args = parser.parse_args()

    # Initialize database
    init_db()
    db = SessionLocal()

    try:
        github_client = GitHubClient()
        service = PRScanService(db=db, github_client=github_client)

        print(f"Scanning PR #{args.pr} in {args.repo} (SHA: {args.sha[:8]})...")

        scan = service.scan_pr(
            repo=args.repo,
            pr_number=args.pr,
            head_sha=args.sha,
            strategy_override=args.strategy,
        )

        if args.output == "json":
            result = {
                "scan_id": scan.id,
                "status": scan.scan_status,
                "files_scanned": scan.total_files_scanned,
                "violations_summary": scan.violations_summary,
                "validation_results": scan.validation_results,
                "duration_ms": scan.scan_duration_ms,
            }
            print(json.dumps(result, indent=2, default=str))
        else:
            summary = scan.violations_summary or {}
            print(f"\nScan complete: {scan.scan_status.upper()}")
            print(f"Files scanned: {scan.total_files_scanned}")
            print(f"Duration: {scan.scan_duration_ms}ms")
            print(f"Violations: "
                  f"{summary.get('critical', 0)} critical, "
                  f"{summary.get('warning', 0)} warning, "
                  f"{summary.get('info', 0)} info")

            if scan.validation_results and scan.validation_results.get("file_results"):
                for fr in scan.validation_results["file_results"]:
                    status_icon = {
                        "passed": "[PASS]",
                        "warning": "[WARN]",
                        "failed": "[FAIL]",
                        "error": "[ERR]",
                    }.get(fr["status"], "[?]")
                    print(f"\n  {status_icon} {fr['filename']}")
                    for v in fr.get("violations", []):
                        print(f"    - [{v['type'].upper()}] {v['policy']}: {v['message']}")
                        if v.get("remediation"):
                            print(f"      Fix: {v['remediation']}")

        # Exit with non-zero code if scan failed (for CI/CD gating)
        if scan.scan_status == "failed":
            sys.exit(1)
        elif scan.scan_status == "error":
            sys.exit(2)

    finally:
        db.close()


if __name__ == "__main__":
    main()

"""
Tests for the PR scan service.

Tests the full scan lifecycle including PR event handling,
validation orchestration, result aggregation, and scan history queries.
"""

import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from app.models.pr_scan import PRScan
from app.services.pr_scan_service import PRScanService
from app.services.github_client import GitHubClient


@pytest.fixture
def mock_github_client():
    """Create a mock GitHub client."""
    client = MagicMock(spec=GitHubClient)
    client.is_configured.return_value = False
    client.get_pr_files.return_value = []
    client.get_file_content.return_value = None
    return client


@pytest.fixture
def scan_service(db, mock_github_client):
    """Create a PRScanService with test database and mock client."""
    return PRScanService(db=db, github_client=mock_github_client)


@pytest.mark.service
class TestHandlePrEvent:
    """Test PR webhook event handling."""

    def test_handle_opened_event(self, scan_service, mock_github_client):
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 42,
                "title": "Add customer schema",
                "head": {"sha": "abc123def456", "ref": "feature/schema"},
                "base": {"ref": "main"},
                "user": {"login": "testuser"},
            },
            "repository": {"full_name": "owner/repo"},
        }

        scan = scan_service.handle_pr_event(payload)

        assert scan is not None
        assert scan.pr_number == 42
        assert scan.github_repo == "owner/repo"
        assert scan.head_sha == "abc123def456"
        assert scan.scan_status in ("passed", "warning", "failed", "error")

    def test_ignore_closed_event(self, scan_service):
        payload = {
            "action": "closed",
            "pull_request": {"number": 42},
            "repository": {"full_name": "owner/repo"},
        }
        result = scan_service.handle_pr_event(payload)
        assert result is None

    def test_ignore_labeled_event(self, scan_service):
        payload = {
            "action": "labeled",
            "pull_request": {"number": 42},
            "repository": {"full_name": "owner/repo"},
        }
        result = scan_service.handle_pr_event(payload)
        assert result is None

    def test_handle_synchronize_event(self, scan_service):
        payload = {
            "action": "synchronize",
            "pull_request": {
                "number": 42,
                "title": "Update schema",
                "head": {"sha": "def456", "ref": "feature/update"},
                "base": {"ref": "main"},
                "user": {"login": "testuser"},
            },
            "repository": {"full_name": "owner/repo"},
        }
        scan = scan_service.handle_pr_event(payload)
        assert scan is not None
        assert scan.head_sha == "def456"

    def test_missing_repo_returns_none(self, scan_service):
        payload = {
            "action": "opened",
            "pull_request": {
                "number": 42,
                "head": {"sha": "abc123"},
            },
            "repository": {},
        }
        result = scan_service.handle_pr_event(payload)
        assert result is None


@pytest.mark.service
class TestScanPr:
    """Test PR scanning lifecycle."""

    def test_scan_no_relevant_files(self, scan_service, mock_github_client):
        mock_github_client.get_pr_files.return_value = [
            {"filename": "app/main.py", "status": "modified"},
            {"filename": "README.md", "status": "modified"},
        ]

        scan = scan_service.scan_pr(
            repo="owner/repo",
            pr_number=1,
            head_sha="abc123",
        )

        assert scan.scan_status == "passed"
        assert scan.total_files_scanned == 0
        assert scan.violations_summary["critical"] == 0

    def test_scan_with_valid_contract(self, scan_service, mock_github_client):
        import yaml
        contract = {
            "dataset": {
                "name": "test_customers",
                "description": "Customer data",
                "owner_name": "John",
                "owner_email": "john@test.com",
            },
            "schema": [
                {
                    "name": "id",
                    "type": "integer",
                    "description": "Customer ID",
                    "required": True,
                    "nullable": False,
                    "pii": False,
                }
            ],
            "governance": {
                "classification": "public",
            },
            "quality_rules": {},
        }

        mock_github_client.get_pr_files.return_value = [
            {"filename": "contracts/customers.yaml", "status": "modified"},
        ]
        mock_github_client.get_file_content.return_value = yaml.dump(contract)

        scan = scan_service.scan_pr(
            repo="owner/repo",
            pr_number=2,
            head_sha="def456",
        )

        assert scan.scan_status in ("passed", "warning", "failed")
        assert scan.total_files_scanned == 1
        assert scan.validation_results is not None
        assert scan.scan_duration_ms is not None

    def test_scan_with_violations(self, scan_service, mock_github_client):
        import yaml
        contract = {
            "dataset": {
                "name": "test",
                # Missing owner_name, owner_email (SG003)
            },
            "schema": [
                {
                    "name": "ssn",
                    "type": "string",
                    # Missing description (SG001)
                    "required": True,
                    "nullable": False,
                    "pii": True,
                    # Missing max_length (SG004)
                }
            ],
            "governance": {
                "classification": "confidential",
                # Missing encryption_required (SD001)
                # Missing retention_days (SD002)
            },
            "quality_rules": {},
        }

        mock_github_client.get_pr_files.return_value = [
            {"filename": "contracts/sensitive.yaml", "status": "added"},
        ]
        mock_github_client.get_file_content.return_value = yaml.dump(contract)

        scan = scan_service.scan_pr(
            repo="owner/repo",
            pr_number=3,
            head_sha="ghi789",
        )

        assert scan.scan_status == "failed"
        summary = scan.violations_summary
        assert summary["critical"] > 0

    def test_scan_stores_in_db(self, scan_service, db, mock_github_client):
        mock_github_client.get_pr_files.return_value = []

        scan = scan_service.scan_pr(
            repo="owner/repo",
            pr_number=10,
            head_sha="xyz999",
        )

        stored = db.query(PRScan).filter(PRScan.id == scan.id).first()
        assert stored is not None
        assert stored.github_repo == "owner/repo"
        assert stored.pr_number == 10


@pytest.mark.service
class TestScanHistory:
    """Test scan history queries."""

    def test_get_empty_history(self, scan_service):
        scans, total = scan_service.get_scan_history()
        assert total == 0
        assert scans == []

    def test_get_history_after_scans(self, scan_service, mock_github_client):
        mock_github_client.get_pr_files.return_value = []

        scan_service.scan_pr(repo="owner/repo", pr_number=1, head_sha="sha1")
        scan_service.scan_pr(repo="owner/repo", pr_number=2, head_sha="sha2")

        scans, total = scan_service.get_scan_history()
        assert total == 2
        assert len(scans) == 2

    def test_filter_by_repo(self, scan_service, mock_github_client):
        mock_github_client.get_pr_files.return_value = []

        scan_service.scan_pr(repo="owner/repo1", pr_number=1, head_sha="sha1")
        scan_service.scan_pr(repo="owner/repo2", pr_number=1, head_sha="sha2")

        scans, total = scan_service.get_scan_history(repo="owner/repo1")
        assert total == 1

    def test_get_scan_detail(self, scan_service, mock_github_client):
        mock_github_client.get_pr_files.return_value = []
        scan = scan_service.scan_pr(repo="owner/repo", pr_number=1, head_sha="sha1")

        detail = scan_service.get_scan_detail(scan.id)
        assert detail is not None
        assert detail.id == scan.id

    def test_get_scan_detail_not_found(self, scan_service):
        assert scan_service.get_scan_detail(9999) is None

    def test_get_scans_by_pr(self, scan_service, mock_github_client):
        mock_github_client.get_pr_files.return_value = []

        scan_service.scan_pr(repo="owner/repo", pr_number=42, head_sha="sha1")
        scan_service.scan_pr(repo="owner/repo", pr_number=42, head_sha="sha2")
        scan_service.scan_pr(repo="owner/repo", pr_number=43, head_sha="sha3")

        scans = scan_service.get_scans_by_pr("owner/repo", 42)
        assert len(scans) == 2


@pytest.mark.service
class TestStats:
    """Test dashboard statistics calculation."""

    def test_empty_stats(self, scan_service):
        stats = scan_service.get_stats()
        assert stats["total_scans"] == 0
        assert stats["pass_rate"] == 0.0

    def test_stats_after_scans(self, scan_service, mock_github_client):
        mock_github_client.get_pr_files.return_value = []

        # Create multiple scans (all should pass since no files)
        for i in range(5):
            scan_service.scan_pr(
                repo="owner/repo", pr_number=i, head_sha=f"sha{i}"
            )

        stats = scan_service.get_stats()
        assert stats["total_scans"] == 5
        assert stats["passed"] == 5
        assert stats["pass_rate"] == 100.0

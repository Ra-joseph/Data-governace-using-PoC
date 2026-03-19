"""
Tests for PR governance API endpoints.

Tests the webhook endpoint, scan listing, scan detail,
rescan, stats, and manual scan endpoints.
"""

import json
import hmac
import hashlib
import pytest
from unittest.mock import patch, MagicMock

from app.models.pr_scan import PRScan


@pytest.mark.api
class TestWebhookEndpoint:
    """Test the GitHub webhook receiver."""

    def test_webhook_ignored_event(self, client):
        response = client.post(
            "/api/v1/pr-governance/webhook",
            content=json.dumps({"action": "labeled"}).encode(),
            headers={
                "X-GitHub-Event": "issues",
                "X-Hub-Signature-256": "",
            },
        )
        assert response.status_code == 202
        assert response.json()["status"] == "ignored"

    def test_webhook_invalid_json(self, client):
        response = client.post(
            "/api/v1/pr-governance/webhook",
            content=b"not json",
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "",
            },
        )
        assert response.status_code == 400

    def test_webhook_pull_request_ignored_action(self, client):
        payload = json.dumps({"action": "closed"}).encode()
        response = client.post(
            "/api/v1/pr-governance/webhook",
            content=payload,
            headers={
                "X-GitHub-Event": "pull_request",
                "X-Hub-Signature-256": "",
            },
        )
        assert response.status_code == 202
        assert response.json()["status"] == "ignored"


@pytest.mark.api
class TestScanEndpoints:
    """Test scan listing and detail endpoints."""

    def test_list_scans_empty(self, client):
        response = client.get("/api/v1/pr-governance/scans")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["scans"] == []

    def test_list_scans_with_data(self, client, db):
        scan = PRScan(
            github_repo="owner/repo",
            pr_number=42,
            pr_title="Test PR",
            head_sha="abc123",
            scan_status="passed",
            total_files_scanned=2,
            violations_summary={"critical": 0, "warning": 0, "info": 0},
        )
        db.add(scan)
        db.commit()

        response = client.get("/api/v1/pr-governance/scans")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert data["scans"][0]["pr_number"] == 42

    def test_get_scan_detail(self, client, db):
        scan = PRScan(
            github_repo="owner/repo",
            pr_number=42,
            head_sha="abc123",
            scan_status="failed",
            validation_results={"files_checked": 1, "file_results": []},
            violations_summary={"critical": 2, "warning": 1, "info": 0},
        )
        db.add(scan)
        db.commit()

        response = client.get(f"/api/v1/pr-governance/scans/{scan.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["scan_status"] == "failed"

    def test_get_scan_not_found(self, client):
        response = client.get("/api/v1/pr-governance/scans/9999")
        assert response.status_code == 404

    def test_filter_by_status(self, client, db):
        for status in ["passed", "passed", "failed"]:
            scan = PRScan(
                github_repo="owner/repo",
                pr_number=1,
                head_sha="abc",
                scan_status=status,
            )
            db.add(scan)
        db.commit()

        response = client.get("/api/v1/pr-governance/scans?status=failed")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1


@pytest.mark.api
class TestStatsEndpoint:
    """Test dashboard statistics endpoint."""

    def test_empty_stats(self, client):
        response = client.get("/api/v1/pr-governance/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] == 0
        assert data["pass_rate"] == 0.0

    def test_stats_with_data(self, client, db):
        for status in ["passed", "passed", "failed", "warning"]:
            scan = PRScan(
                github_repo="owner/repo",
                pr_number=1,
                head_sha="abc",
                scan_status=status,
                violations_summary={"critical": 1 if status == "failed" else 0, "warning": 0, "info": 0},
                scan_duration_ms=100,
            )
            db.add(scan)
        db.commit()

        response = client.get("/api/v1/pr-governance/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["total_scans"] == 4
        assert data["passed"] == 2
        assert data["failed"] == 1


@pytest.mark.api
class TestRescanEndpoint:
    """Test PR rescan endpoint."""

    def test_rescan_not_found(self, client):
        response = client.post("/api/v1/pr-governance/scans/9999/rescan")
        assert response.status_code == 404

    @patch("app.services.pr_scan_service.PRScanService.scan_pr")
    def test_rescan_success(self, mock_scan_pr, client, db):
        original = PRScan(
            github_repo="owner/repo",
            pr_number=42,
            head_sha="abc123",
            scan_status="failed",
        )
        db.add(original)
        db.commit()

        new_scan = MagicMock()
        new_scan.id = 999
        new_scan.scan_status = "passed"
        mock_scan_pr.return_value = new_scan

        response = client.post(f"/api/v1/pr-governance/scans/{original.id}/rescan")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"


@pytest.mark.api
class TestManualScanEndpoint:
    """Test manual scan trigger."""

    def test_manual_scan_no_token(self, client):
        response = client.post(
            "/api/v1/pr-governance/scan-manual",
            json={"repo": "owner/repo", "pr_number": 42},
        )
        assert response.status_code == 400
        assert "token" in response.json()["detail"].lower()

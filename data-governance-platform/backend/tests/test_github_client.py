"""
Tests for the GitHub API client.

Tests webhook signature verification, API response parsing,
and error handling. All HTTP calls are mocked.
"""

import hmac
import hashlib
import pytest
from unittest.mock import patch, MagicMock

from app.services.github_client import GitHubClient


@pytest.mark.unit
class TestWebhookSignatureVerification:
    """Test HMAC-SHA256 webhook signature verification."""

    def test_valid_signature(self):
        client = GitHubClient(
            token="test-token", webhook_secret="test-secret"
        )
        payload = b'{"action": "opened"}'
        expected = "sha256=" + hmac.new(
            b"test-secret", payload, hashlib.sha256
        ).hexdigest()

        assert client.verify_webhook_signature(payload, expected) is True

    def test_invalid_signature(self):
        client = GitHubClient(
            token="test-token", webhook_secret="test-secret"
        )
        payload = b'{"action": "opened"}'
        assert client.verify_webhook_signature(payload, "sha256=invalid") is False

    def test_empty_signature(self):
        client = GitHubClient(
            token="test-token", webhook_secret="test-secret"
        )
        assert client.verify_webhook_signature(b"payload", "") is False

    def test_no_secret_configured(self):
        client = GitHubClient(token="test-token", webhook_secret="")
        assert client.verify_webhook_signature(b"payload", "any") is True


@pytest.mark.unit
class TestGetPrFiles:
    """Test PR file retrieval."""

    @patch("app.services.github_client.httpx.get")
    def test_get_pr_files_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"filename": "contracts/test.yaml", "status": "modified"},
            {"filename": "app/main.py", "status": "modified"},
        ]
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = GitHubClient(token="test-token")
        files = client.get_pr_files("owner/repo", 42)

        assert len(files) == 2
        assert files[0]["filename"] == "contracts/test.yaml"

    @patch("app.services.github_client.httpx.get")
    def test_get_pr_files_error(self, mock_get):
        import httpx
        mock_get.side_effect = httpx.HTTPError("Connection error")

        client = GitHubClient(token="test-token")
        files = client.get_pr_files("owner/repo", 42)

        assert files == []


@pytest.mark.unit
class TestGetFileContent:
    """Test file content retrieval."""

    @patch("app.services.github_client.httpx.get")
    def test_get_file_content_base64(self, mock_get):
        import base64
        content = "name: test\nversion: '1.0'"
        encoded = base64.b64encode(content.encode()).decode()

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "content": encoded,
            "encoding": "base64",
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        client = GitHubClient(token="test-token")
        result = client.get_file_content("owner/repo", "test.yaml", "abc123")

        assert result == content

    @patch("app.services.github_client.httpx.get")
    def test_get_file_content_error(self, mock_get):
        import httpx
        mock_get.side_effect = httpx.HTTPError("Not found")

        client = GitHubClient(token="test-token")
        result = client.get_file_content("owner/repo", "test.yaml", "abc123")

        assert result is None


@pytest.mark.unit
class TestCreateCheckRun:
    """Test GitHub Check Run creation."""

    @patch("app.services.github_client.httpx.post")
    def test_create_check_run_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 12345}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        client = GitHubClient(token="test-token")
        result = client.create_check_run(
            repo="owner/repo",
            head_sha="abc123",
            name="Governance Scan",
            status="completed",
            conclusion="success",
            title="All checks passed",
            summary="No violations found",
        )

        assert result == {"id": 12345}

    @patch("app.services.github_client.httpx.post")
    def test_create_check_run_error(self, mock_post):
        import httpx
        mock_post.side_effect = httpx.HTTPError("Forbidden")

        client = GitHubClient(token="test-token")
        result = client.create_check_run(
            repo="owner/repo",
            head_sha="abc123",
            name="Governance Scan",
            status="completed",
        )

        assert result is None


@pytest.mark.unit
class TestIsConfigured:
    """Test configuration check."""

    def test_configured_with_token(self):
        client = GitHubClient(token="test-token")
        assert client.is_configured() is True

    def test_not_configured_without_token(self):
        client = GitHubClient(token="")
        assert client.is_configured() is False


@pytest.mark.unit
class TestCreatePrReview:
    """Test PR review creation."""

    @patch("app.services.github_client.httpx.post")
    def test_create_review_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": 99}
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response

        client = GitHubClient(token="test-token")
        result = client.create_pr_review(
            repo="owner/repo",
            pr_number=42,
            body="Scan complete",
            event="COMMENT",
        )

        assert result == {"id": 99}

    @patch("app.services.github_client.httpx.post")
    def test_create_review_error(self, mock_post):
        import httpx
        mock_post.side_effect = httpx.HTTPError("Error")

        client = GitHubClient(token="test-token")
        result = client.create_pr_review(
            repo="owner/repo",
            pr_number=42,
            body="Scan complete",
        )

        assert result is None

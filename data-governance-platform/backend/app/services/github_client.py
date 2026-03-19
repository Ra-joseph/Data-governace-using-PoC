"""
GitHub API client for PR governance scanning.

This module provides a client for interacting with the GitHub REST API
to fetch PR details, file contents, and post check runs and review
comments. Used by the PR Governance Agent to scan pull requests for
governance policy violations.
"""

import hmac
import hashlib
import base64
import logging
from typing import Optional, List, Dict, Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class GitHubClient:
    """
    HTTP client for GitHub REST API interactions.

    Handles authentication, webhook signature verification, PR file
    retrieval, and posting scan results back to GitHub as check runs
    and review comments.

    Attributes:
        token: GitHub Personal Access Token or App token.
        webhook_secret: Shared secret for HMAC webhook verification.
        base_url: GitHub API base URL.
        timeout: Request timeout in seconds.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        base_url: str = "https://api.github.com",
        timeout: int = 30,
    ):
        self.token = token or settings.GITHUB_TOKEN
        self.webhook_secret = webhook_secret or settings.GITHUB_WEBHOOK_SECRET
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers with authentication."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DataGovernancePlatform/1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify GitHub webhook HMAC-SHA256 signature.

        Uses constant-time comparison to prevent timing attacks.

        Args:
            payload: Raw request body bytes.
            signature: X-Hub-Signature-256 header value.

        Returns:
            True if signature is valid, False otherwise.
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured; skipping verification")
            return True

        if not signature:
            return False

        expected = "sha256=" + hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected, signature)

    def get_pr_details(self, repo: str, pr_number: int) -> Dict[str, Any]:
        """
        Fetch pull request details.

        Args:
            repo: Repository full name (owner/repo).
            pr_number: Pull request number.

        Returns:
            PR details including title, author, branches, and SHA.
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}"
        try:
            response = httpx.get(
                url, headers=self._get_headers(), timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch PR details: {e}")
            return {}

    def get_pr_files(self, repo: str, pr_number: int) -> List[Dict[str, Any]]:
        """
        Fetch the list of files changed in a pull request.

        Args:
            repo: Repository full name (owner/repo).
            pr_number: Pull request number.

        Returns:
            List of file change objects with filename, status, and patch.
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/files"
        all_files = []
        page = 1

        try:
            while True:
                response = httpx.get(
                    url,
                    headers=self._get_headers(),
                    params={"per_page": 100, "page": page},
                    timeout=self.timeout,
                )
                response.raise_for_status()
                files = response.json()
                if not files:
                    break
                all_files.extend(files)
                if len(files) < 100:
                    break
                page += 1

            return all_files
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch PR files: {e}")
            return []

    def get_file_content(
        self, repo: str, path: str, ref: str
    ) -> Optional[str]:
        """
        Fetch file content at a specific commit SHA.

        Args:
            repo: Repository full name (owner/repo).
            path: File path within the repository.
            ref: Git reference (commit SHA, branch, tag).

        Returns:
            Decoded file content as string, or None on failure.
        """
        url = f"{self.base_url}/repos/{repo}/contents/{path}"
        try:
            response = httpx.get(
                url,
                headers=self._get_headers(),
                params={"ref": ref},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            if data.get("encoding") == "base64" and data.get("content"):
                return base64.b64decode(data["content"]).decode("utf-8")

            return data.get("content", "")
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch file content for {path}: {e}")
            return None

    def create_check_run(
        self,
        repo: str,
        head_sha: str,
        name: str,
        status: str,
        conclusion: Optional[str] = None,
        title: Optional[str] = None,
        summary: Optional[str] = None,
        text: Optional[str] = None,
        annotations: Optional[List[Dict]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create or complete a GitHub Check Run.

        Args:
            repo: Repository full name (owner/repo).
            head_sha: Commit SHA to attach check to.
            name: Check run name displayed in GitHub UI.
            status: Check status (queued, in_progress, completed).
            conclusion: Final conclusion (success, failure, neutral, action_required).
            title: Output title for the check details.
            summary: Output summary (markdown).
            text: Detailed output text (markdown).
            annotations: List of file annotations with messages.

        Returns:
            Created check run object, or None on failure.
        """
        url = f"{self.base_url}/repos/{repo}/check-runs"
        payload: Dict[str, Any] = {
            "name": name,
            "head_sha": head_sha,
            "status": status,
        }

        if conclusion:
            payload["conclusion"] = conclusion

        output: Dict[str, Any] = {}
        if title:
            output["title"] = title
        if summary:
            output["summary"] = summary
        if text:
            output["text"] = text
        if annotations:
            output["annotations"] = annotations[:50]  # GitHub limit

        if output:
            payload["output"] = output

        try:
            response = httpx.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to create check run: {e}")
            return None

    def create_pr_review(
        self,
        repo: str,
        pr_number: int,
        body: str,
        event: str = "COMMENT",
        comments: Optional[List[Dict]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Create a pull request review with optional inline comments.

        Args:
            repo: Repository full name (owner/repo).
            pr_number: Pull request number.
            body: Review body text.
            event: Review event (APPROVE, REQUEST_CHANGES, COMMENT).
            comments: List of inline review comments.

        Returns:
            Created review object, or None on failure.
        """
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/reviews"
        payload: Dict[str, Any] = {
            "body": body,
            "event": event,
        }

        if comments:
            payload["comments"] = comments

        try:
            response = httpx.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Failed to create PR review: {e}")
            return None

    def is_configured(self) -> bool:
        """Check if the GitHub client has a token configured."""
        return bool(self.token)

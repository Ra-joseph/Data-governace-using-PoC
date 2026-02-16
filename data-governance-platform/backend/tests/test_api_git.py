"""
Unit tests for git API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.api
@pytest.mark.unit
class TestGitAPI:
    """Test cases for git API endpoints."""

    @patch('app.api.git.git_service.get_commit_history')
    def test_get_commit_history(self, mock_get_history, client):
        """Test getting commit history."""
        mock_get_history.return_value = [
            {
                "commit": "abc123",
                "author": "John Doe",
                "date": "2024-01-01T00:00:00",
                "message": "Initial commit"
            }
        ]

        response = client.get("/api/v1/git/history")
        assert response.status_code == 200
        data = response.json()
        assert "history" in data
        assert "count" in data
        assert len(data["history"]) == 1
        assert data["count"] == 1

    @patch('app.api.git.git_service.get_commit_history')
    def test_get_commit_history_with_filename(self, mock_get_history, client):
        """Test getting commit history for a specific file."""
        mock_get_history.return_value = [
            {
                "commit": "xyz789",
                "author": "Jane Doe",
                "date": "2024-01-02T00:00:00",
                "message": "Update contract"
            }
        ]

        response = client.get("/api/v1/git/history?filename=test_contract.yaml")
        assert response.status_code == 200
        data = response.json()
        assert len(data["history"]) == 1
        mock_get_history.assert_called_once_with("test_contract.yaml")

    @patch('app.api.git.git_service.list_contracts')
    def test_list_git_contracts(self, mock_list_contracts, client):
        """Test listing all contracts in Git."""
        mock_list_contracts.return_value = [
            "customer_accounts_v1.0.0.yaml",
            "transactions_v1.0.0.yaml"
        ]

        response = client.get("/api/v1/git/contracts")
        assert response.status_code == 200
        data = response.json()
        assert "contracts" in data
        assert "count" in data
        assert len(data["contracts"]) == 2
        assert data["count"] == 2

    @patch('app.api.git.git_service.get_diff')
    def test_get_commit_diff(self, mock_get_diff, client):
        """Test getting diff between two commits."""
        mock_get_diff.return_value = "--- a/file\n+++ b/file\n@@ -1 +1 @@"

        response = client.get("/api/v1/git/diff?commit1=abc123&commit2=xyz789")
        assert response.status_code == 200
        data = response.json()
        assert data["commit1"] == "abc123"
        assert data["commit2"] == "xyz789"
        assert "diff" in data

    @patch('app.api.git.git_service.get_contract')
    def test_get_contract_content(self, mock_get_contract, client):
        """Test getting contract content from Git."""
        mock_get_contract.return_value = "# Contract content\nversion: 1.0.0"

        response = client.get("/api/v1/git/contract/customer_accounts/1.0.0")
        assert response.status_code == 200
        data = response.json()
        assert data["dataset_name"] == "customer_accounts"
        assert data["version"] == "1.0.0"
        assert "content" in data

    @patch('app.api.git.git_service.get_contract')
    def test_get_contract_not_found(self, mock_get_contract, client):
        """Test getting non-existent contract."""
        mock_get_contract.return_value = None

        response = client.get("/api/v1/git/contract/nonexistent/1.0.0")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.git.git_service.create_tag')
    def test_create_git_tag(self, mock_create_tag, client):
        """Test creating a Git tag."""
        mock_create_tag.return_value = "v1.0.0"

        response = client.post("/api/v1/git/tags?tag_name=v1.0.0&message=Release%201.0.0")
        assert response.status_code == 200
        data = response.json()
        assert data["tag"] == "v1.0.0"

    @patch('app.api.git.git_service')
    def test_get_repository_status(self, mock_git_service, client):
        """Test getting repository status."""
        # Mock the git service
        mock_git_service.list_contracts.return_value = ["contract1.yaml", "contract2.yaml"]
        mock_git_service.get_commit_history.return_value = [
            {"commit": "abc", "message": "Test"}
        ]

        mock_repo = MagicMock()
        mock_repo.refs = [MagicMock(name="main"), MagicMock(name="develop")]
        mock_repo.tags = [MagicMock(name="v1.0"), MagicMock(name="v2.0")]
        mock_repo.active_branch.name = "main"

        mock_git_service.repo = mock_repo
        mock_git_service.repo_path = "/path/to/repo"

        response = client.get("/api/v1/git/status")
        assert response.status_code == 200
        data = response.json()
        assert "repository_path" in data
        assert "total_contracts" in data
        assert "total_commits" in data
        assert "branches" in data
        assert "tags" in data
        assert "active_branch" in data

    @patch('app.api.git.git_service.get_commit_history')
    def test_get_file_history(self, mock_get_history, client):
        """Test getting detailed file history."""
        mock_get_history.return_value = [
            {
                "commit": "abc123",
                "author": "John Doe",
                "date": "2024-01-01",
                "message": "Initial version"
            },
            {
                "commit": "def456",
                "author": "Jane Doe",
                "date": "2024-01-02",
                "message": "Update schema"
            }
        ]

        response = client.get("/api/v1/git/file-history/contract.yaml")
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "contract.yaml"
        assert data["total_commits"] == 2
        assert len(data["commits"]) == 2

    @patch('app.api.git.git_service.get_commit_history')
    def test_get_file_history_not_found(self, mock_get_history, client):
        """Test getting history for non-existent file."""
        mock_get_history.return_value = []

        response = client.get("/api/v1/git/file-history/nonexistent.yaml")
        assert response.status_code == 404

    @patch('app.api.git.git_service')
    def test_get_file_blame(self, mock_git_service, client):
        """Test getting Git blame for a file."""
        # Mock repo and blame
        mock_commit = MagicMock()
        mock_commit.hexsha = "abc123456789"
        mock_commit.author = "John Doe"
        mock_commit.committed_datetime.isoformat.return_value = "2024-01-01T00:00:00"
        mock_commit.message = "Initial commit"

        mock_repo = MagicMock()
        mock_repo.blame.return_value = [(mock_commit, ["line1", "line2"])]

        mock_git_service.repo = mock_repo
        mock_git_service.repo_path = MagicMock()
        mock_git_service.repo_path.__truediv__ = lambda self, other: MagicMock(exists=lambda: True)

        response = client.get("/api/v1/git/blame/contract.yaml")
        assert response.status_code == 200
        data = response.json()
        assert data["filename"] == "contract.yaml"
        assert "blame" in data

    @patch('app.api.git.git_service.get_commit_history')
    def test_git_history_error_handling(self, mock_get_history, client):
        """Test error handling in Git history endpoint."""
        mock_get_history.side_effect = Exception("Git error")

        response = client.get("/api/v1/git/history")
        assert response.status_code == 500
        assert "Failed to get history" in response.json()["detail"]

    @patch('app.api.git.git_service.list_contracts')
    def test_list_contracts_error_handling(self, mock_list_contracts, client):
        """Test error handling in list contracts endpoint."""
        mock_list_contracts.side_effect = Exception("Git error")

        response = client.get("/api/v1/git/contracts")
        assert response.status_code == 500
        assert "Failed to list contracts" in response.json()["detail"]

    @patch('app.api.git.git_service.get_diff')
    def test_diff_error_handling(self, mock_get_diff, client):
        """Test error handling in diff endpoint."""
        mock_get_diff.side_effect = Exception("Git error")

        response = client.get("/api/v1/git/diff?commit1=abc&commit2=xyz")
        assert response.status_code == 500
        assert "Failed to get diff" in response.json()["detail"]

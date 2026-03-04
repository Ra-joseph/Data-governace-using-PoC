"""
Unit tests for GitService.
"""
import pytest
from unittest.mock import patch, Mock, MagicMock, PropertyMock
from pathlib import Path

from app.services.git_service import GitService


@pytest.mark.unit
@pytest.mark.service
class TestGitServiceInit:
    """Test GitService initialization."""

    @patch("app.services.git_service.settings")
    def test_init_creates_directory(self, mock_settings, tmp_path):
        """Test that init creates the repo directory if it doesn't exist."""
        repo_path = tmp_path / "new_contracts"
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(repo_path)
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(repo_path))
        assert repo_path.exists()
        assert service.repo is not None

    @patch("app.services.git_service.settings")
    def test_init_opens_existing_repo(self, mock_settings, tmp_path):
        """Test that init opens an existing Git repo."""
        import git
        repo_path = tmp_path / "existing_repo"
        repo_path.mkdir()
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        # Initialize a real git repo first
        repo = git.Repo.init(repo_path)
        readme = repo_path / "README.md"
        readme.write_text("# Test")
        repo.index.add(["README.md"])
        repo.index.commit("Initial", author=git.Actor("Test", "test@test.com"))

        service = GitService(repo_path=str(repo_path))
        assert service.repo is not None

    @patch("app.services.git_service.settings")
    def test_init_creates_new_repo_with_initial_commit(self, mock_settings, tmp_path):
        """Test that a new repo is created with .gitignore and README."""
        repo_path = tmp_path / "fresh_repo"
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(repo_path)
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(repo_path))

        # Check initial files
        assert (repo_path / ".gitignore").exists()
        assert (repo_path / "README.md").exists()

        # Check initial commit
        commits = list(service.repo.iter_commits())
        assert len(commits) == 1
        assert "Initial commit" in commits[0].message


@pytest.mark.unit
@pytest.mark.service
class TestGitServiceCommit:
    """Test GitService commit operations."""

    @patch("app.services.git_service.settings")
    def test_commit_contract_basic(self, mock_settings, tmp_path):
        """Test basic contract commit."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        result = service.commit_contract(
            contract_yaml="dataset:\n  name: test",
            dataset_name="test_dataset",
            version="1.0.0"
        )

        assert "commit_hash" in result
        assert "commit_message" in result
        assert "file_path" in result
        assert "timestamp" in result
        assert result["file_path"] == "test_dataset_v1.0.0.yaml"

    @patch("app.services.git_service.settings")
    def test_commit_contract_sanitizes_name(self, mock_settings, tmp_path):
        """Test that dataset names with spaces and hyphens are sanitized."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        result = service.commit_contract(
            contract_yaml="test: true",
            dataset_name="My Data-Set Name",
            version="1.0.0"
        )

        assert result["file_path"] == "my_data_set_name_v1.0.0.yaml"

    @patch("app.services.git_service.settings")
    def test_commit_contract_special_characters(self, mock_settings, tmp_path):
        """Test commit with special characters in dataset name."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        result = service.commit_contract(
            contract_yaml="test: true",
            dataset_name="UPPER-Case Dataset",
            version="2.0.0"
        )

        assert result["file_path"] == "upper_case_dataset_v2.0.0.yaml"

    @patch("app.services.git_service.settings")
    def test_commit_contract_custom_message(self, mock_settings, tmp_path):
        """Test commit with custom message."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        result = service.commit_contract(
            contract_yaml="test: true",
            dataset_name="test",
            version="1.0.0",
            commit_message="Custom commit message"
        )

        assert result["commit_message"] == "Custom commit message"

    @patch("app.services.git_service.settings")
    def test_commit_contract_default_message(self, mock_settings, tmp_path):
        """Test commit generates default message when none provided."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        result = service.commit_contract(
            contract_yaml="test: true",
            dataset_name="my_data",
            version="1.0.0"
        )

        assert "my_data" in result["commit_message"]
        assert "1.0.0" in result["commit_message"]


@pytest.mark.unit
@pytest.mark.service
class TestGitServiceGetContract:
    """Test GitService contract retrieval."""

    @patch("app.services.git_service.settings")
    def test_get_contract_found(self, mock_settings, tmp_path):
        """Test retrieving an existing contract."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        service.commit_contract("dataset:\n  name: test", "test_data", "1.0.0")

        content = service.get_contract("test_data", "1.0.0")
        assert content is not None
        assert "dataset:" in content

    @patch("app.services.git_service.settings")
    def test_get_contract_not_found(self, mock_settings, tmp_path):
        """Test retrieving a non-existent contract returns None."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        content = service.get_contract("nonexistent", "9.9.9")
        assert content is None

    @patch("app.services.git_service.settings")
    def test_get_contract_sanitizes_name(self, mock_settings, tmp_path):
        """Test name sanitization consistency between commit and get."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        service.commit_contract("data: value", "My-Dataset", "1.0.0")

        # Should find it with same un-sanitized name
        content = service.get_contract("My-Dataset", "1.0.0")
        assert content is not None


@pytest.mark.unit
@pytest.mark.service
class TestGitServiceListContracts:
    """Test GitService contract listing."""

    @patch("app.services.git_service.settings")
    def test_list_contracts_empty_repo(self, mock_settings, tmp_path):
        """Test listing contracts in a repo with no YAML files."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        contracts = service.list_contracts()
        assert contracts == []

    @patch("app.services.git_service.settings")
    def test_list_contracts_multiple_files(self, mock_settings, tmp_path):
        """Test listing multiple contract files."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        service.commit_contract("data: 1", "dataset_a", "1.0.0")
        service.commit_contract("data: 2", "dataset_b", "1.0.0")

        contracts = service.list_contracts()
        assert len(contracts) == 2
        filenames = [c["filename"] for c in contracts]
        assert "dataset_a_v1.0.0.yaml" in filenames
        assert "dataset_b_v1.0.0.yaml" in filenames

    @patch("app.services.git_service.settings")
    def test_list_contracts_has_metadata(self, mock_settings, tmp_path):
        """Test that listed contracts include metadata."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        service.commit_contract("dataset:\n  name: test", "test", "1.0.0")

        contracts = service.list_contracts()
        assert len(contracts) == 1
        assert "filename" in contracts[0]
        assert "path" in contracts[0]
        assert "size" in contracts[0]
        assert contracts[0]["size"] > 0


@pytest.mark.unit
@pytest.mark.service
class TestGitServiceHistory:
    """Test GitService commit history."""

    @patch("app.services.git_service.settings")
    def test_get_commit_history_all(self, mock_settings, tmp_path):
        """Test getting full commit history."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        service.commit_contract("data: 1", "ds1", "1.0.0")
        service.commit_contract("data: 2", "ds2", "1.0.0")

        history = service.get_commit_history()
        # Initial commit + 2 contract commits
        assert len(history) >= 3

        # Check history entry structure
        for entry in history:
            assert "commit_hash" in entry
            assert "author" in entry
            assert "date" in entry
            assert "message" in entry

    @patch("app.services.git_service.settings")
    def test_get_commit_history_specific_file(self, mock_settings, tmp_path):
        """Test getting history for a specific file."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        service.commit_contract("data: 1", "ds1", "1.0.0")
        service.commit_contract("data: 2", "ds2", "1.0.0")

        # Only ds1 commits
        history = service.get_commit_history("ds1_v1.0.0.yaml")
        assert len(history) == 1


@pytest.mark.unit
@pytest.mark.service
class TestGitServiceTags:
    """Test GitService tagging."""

    @patch("app.services.git_service.settings")
    def test_create_tag_with_message(self, mock_settings, tmp_path):
        """Test creating a tag with custom message."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        tag_name = service.create_tag("v1.0.0", "First release")
        assert tag_name == "v1.0.0"

    @patch("app.services.git_service.settings")
    def test_create_tag_default_message(self, mock_settings, tmp_path):
        """Test creating a tag with default message."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        tag_name = service.create_tag("v2.0.0")
        assert tag_name == "v2.0.0"


@pytest.mark.unit
@pytest.mark.service
class TestGitServiceDiff:
    """Test GitService diff operations."""

    @patch("app.services.git_service.settings")
    def test_get_diff_between_commits(self, mock_settings, tmp_path):
        """Test getting diff between two commits."""
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))
        result1 = service.commit_contract("version: 1.0.0", "ds", "1.0.0")
        result2 = service.commit_contract("version: 2.0.0", "ds", "2.0.0")

        diff = service.get_diff(result1["commit_hash"], result2["commit_hash"])
        assert isinstance(diff, str)

    @patch("app.services.git_service.settings")
    def test_get_diff_invalid_commit(self, mock_settings, tmp_path):
        """Test diff with invalid commit hash raises error."""
        import git
        mock_settings.GIT_CONTRACTS_REPO_PATH = str(tmp_path / "repo")
        mock_settings.GIT_USER_NAME = "Test User"
        mock_settings.GIT_USER_EMAIL = "test@example.com"

        service = GitService(repo_path=str(tmp_path / "repo"))

        with pytest.raises(git.BadName):
            service.get_diff("invalid_hash_1", "invalid_hash_2")

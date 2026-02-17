"""
Git service for data contract version control.

This module provides the GitService class which manages data contracts in a Git
repository for complete version control and audit trails. It handles repository
initialization, contract commits, version history, tagging, and diff operations
to ensure all contract changes are tracked and auditable.
"""

import git
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from app.config import settings


class GitService:
    """
    Service for Git-based version control of data contracts.

    This service manages a Git repository that stores all data contracts as YAML
    files with full version history. It provides operations for committing new
    contract versions, retrieving historical versions, comparing changes, and
    maintaining audit trails through Git's native versioning capabilities.

    Attributes:
        repo_path: Path to the Git repository directory
        repo: GitPython Repo object for repository operations

    Example:
        >>> git_service = GitService()
        >>> commit_info = git_service.commit_contract(
        ...     contract_yaml="dataset:\n  name: customers",
        ...     dataset_name="customers",
        ...     version="1.0.0"
        ... )
        >>> print(f"Committed: {commit_info['commit_hash']}")
    """
    
    def __init__(self, repo_path: str = None):
        """
        Initialize Git service with repository path.

        Creates the repository directory if it doesn't exist and initializes
        or opens the Git repository.

        Args:
            repo_path: Optional custom path to Git repository.
                      Defaults to settings.GIT_CONTRACTS_REPO_PATH.
        """
        self.repo_path = Path(repo_path or settings.GIT_CONTRACTS_REPO_PATH)
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.repo = self._init_or_open_repo()
    
    def _init_or_open_repo(self) -> git.Repo:
        """
        Initialize or open existing Git repository.

        If the repository doesn't exist, creates a new one with initial
        .gitignore and README.md files. If it exists, simply opens it.

        Returns:
            GitPython Repo object for the repository.

        Raises:
            git.GitError: If repository initialization or opening fails.
        """
        try:
            # Try to open existing repo
            repo = git.Repo(self.repo_path)
        except git.InvalidGitRepositoryError:
            # Initialize new repo
            repo = git.Repo.init(self.repo_path)
            
            # Create .gitignore
            gitignore_path = self.repo_path / '.gitignore'
            gitignore_path.write_text('__pycache__/\n*.pyc\n.DS_Store\n')
            
            # Create README
            readme_path = self.repo_path / 'README.md'
            readme_path.write_text(
                '# Data Contracts Repository\n\n'
                'This repository contains all data contracts for the Data Governance Platform.\n\n'
                '## Structure\n'
                '- Each contract is stored as `{dataset_name}_v{version}.yaml`\n'
                '- Contracts are versioned using semantic versioning\n'
                '- All changes are tracked in Git history\n'
            )
            
            # Initial commit
            repo.index.add(['.gitignore', 'README.md'])
            repo.index.commit(
                'Initial commit - Data Contracts Repository',
                author=git.Actor(settings.GIT_USER_NAME, settings.GIT_USER_EMAIL)
            )
        
        return repo
    
    def commit_contract(self, contract_yaml: str, dataset_name: str,
                       version: str, commit_message: str = None) -> Dict[str, str]:
        """
        Commit a data contract to the Git repository.

        Writes the contract as a YAML file with standardized naming
        ({dataset_name}_v{version}.yaml), stages it, and creates a Git commit
        with full author information.

        Args:
            contract_yaml: Contract content in YAML format string.
            dataset_name: Name of the dataset (will be sanitized for filename).
            version: Semantic version string (e.g., "1.0.0").
            commit_message: Optional custom commit message. Defaults to
                          "Add/Update contract for {dataset_name} v{version}".

        Returns:
            Dictionary containing:
                - commit_hash: SHA hash of the commit
                - commit_message: The commit message used
                - file_path: Relative path to the contract file
                - timestamp: ISO formatted commit timestamp

        Example:
            >>> result = git_service.commit_contract(
            ...     contract_yaml="dataset:\\n  name: users",
            ...     dataset_name="customer_users",
            ...     version="2.1.0",
            ...     commit_message="Update schema with new email field"
            ... )
            >>> print(result['commit_hash'])
        """
        # Sanitize dataset name for filename
        safe_name = dataset_name.lower().replace(' ', '_').replace('-', '_')
        filename = f"{safe_name}_v{version}.yaml"
        file_path = self.repo_path / filename
        
        # Write contract file
        file_path.write_text(contract_yaml)
        
        # Stage the file
        self.repo.index.add([filename])
        
        # Create commit message
        if not commit_message:
            commit_message = f"Add/Update contract for {dataset_name} v{version}"
        
        # Commit
        commit = self.repo.index.commit(
            commit_message,
            author=git.Actor(settings.GIT_USER_NAME, settings.GIT_USER_EMAIL)
        )
        
        return {
            'commit_hash': commit.hexsha,
            'commit_message': commit_message,
            'file_path': str(file_path.relative_to(self.repo_path)),
            'timestamp': datetime.fromtimestamp(commit.committed_date).isoformat()
        }
    
    def get_contract(self, dataset_name: str, version: str) -> Optional[str]:
        """
        Retrieve a specific contract version from the repository.

        Reads the contract file for the specified dataset and version from
        the repository's working directory.

        Args:
            dataset_name: Name of the dataset (will be sanitized).
            version: Semantic version string to retrieve.

        Returns:
            Contract YAML content as string, or None if not found.

        Example:
            >>> contract = git_service.get_contract("customers", "1.0.0")
            >>> if contract:
            ...     print(f"Found contract: {len(contract)} bytes")
        """
        safe_name = dataset_name.lower().replace(' ', '_').replace('-', '_')
        filename = f"{safe_name}_v{version}.yaml"
        file_path = self.repo_path / filename
        
        if file_path.exists():
            return file_path.read_text()
        return None
    
    def list_contracts(self) -> List[Dict[str, str]]:
        """
        List all contract files in the repository.

        Scans the repository for all YAML files (excluding infrastructure
        files like .gitignore and README.md) and returns their metadata.

        Returns:
            List of dictionaries, each containing:
                - filename: Name of the contract file
                - path: Relative path from repository root
                - size: File size in bytes

        Example:
            >>> contracts = git_service.list_contracts()
            >>> for contract in contracts:
            ...     print(f"{contract['filename']} - {contract['size']} bytes")
        """
        contracts = []
        
        for file_path in self.repo_path.glob('*.yaml'):
            if file_path.name in ['.gitignore', 'README.md']:
                continue
            
            contracts.append({
                'filename': file_path.name,
                'path': str(file_path.relative_to(self.repo_path)),
                'size': file_path.stat().st_size
            })
        
        return contracts
    
    def get_commit_history(self, filename: str = None) -> List[Dict[str, str]]:
        """
        Get Git commit history for contracts.

        Retrieves commit history either for a specific file or for the entire
        repository, providing full audit trail information.

        Args:
            filename: Optional filename to filter commits. If None, returns
                     all commits in the repository.

        Returns:
            List of dictionaries, each containing:
                - commit_hash: Full SHA hash of the commit
                - author: Author name and email
                - date: ISO formatted commit date
                - message: Commit message

        Example:
            >>> history = git_service.get_commit_history("customers_v1.0.0.yaml")
            >>> for commit in history:
            ...     print(f"{commit['date']}: {commit['message']}")
        """
        commits = []
        
        if filename:
            commit_iter = self.repo.iter_commits(paths=filename)
        else:
            commit_iter = self.repo.iter_commits()
        
        for commit in commit_iter:
            commits.append({
                'commit_hash': commit.hexsha,
                'author': f"{commit.author.name} <{commit.author.email}>",
                'date': datetime.fromtimestamp(commit.committed_date).isoformat(),
                'message': commit.message.strip()
            })
        
        return commits
    
    def create_tag(self, tag_name: str, message: str = None) -> str:
        """
        Create a Git tag for marking important versions.

        Creates an annotated or lightweight tag at the current HEAD, useful
        for marking release versions or important milestones.

        Args:
            tag_name: Name for the tag (e.g., "v1.0.0", "production-release").
            message: Optional annotation message. If None, defaults to "Tag: {tag_name}".

        Returns:
            The created tag name.

        Example:
            >>> tag = git_service.create_tag(
            ...     "v1.0.0",
            ...     "First production release"
            ... )
            >>> print(f"Created tag: {tag}")
        """
        tag = self.repo.create_tag(
            tag_name,
            message=message or f"Tag: {tag_name}"
        )
        return tag.name
    
    def get_diff(self, commit1: str, commit2: str) -> str:
        """
        Get unified diff between two commits.

        Compares two commits and returns a unified diff showing all changes,
        useful for understanding what changed between contract versions.

        Args:
            commit1: SHA hash of the first commit (or short hash).
            commit2: SHA hash of the second commit (or short hash).

        Returns:
            Unified diff string showing line-by-line changes.

        Raises:
            git.BadName: If either commit hash is invalid.

        Example:
            >>> diff = git_service.get_diff("abc123", "def456")
            >>> print(diff)
            >>> # Shows additions (+) and deletions (-)
        """
        commit_a = self.repo.commit(commit1)
        commit_b = self.repo.commit(commit2)
        
        diff = commit_a.diff(commit_b, create_patch=True)
        
        diff_text = []
        for item in diff:
            if item.diff:
                diff_text.append(item.diff.decode('utf-8'))
        
        return '\n'.join(diff_text)

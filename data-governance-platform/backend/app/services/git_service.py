import git
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from app.config import settings


class GitService:
    """Service for managing contracts in Git repository."""
    
    def __init__(self, repo_path: str = None):
        """Initialize Git service."""
        self.repo_path = Path(repo_path or settings.GIT_CONTRACTS_REPO_PATH)
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.repo = self._init_or_open_repo()
    
    def _init_or_open_repo(self) -> git.Repo:
        """Initialize or open existing Git repository."""
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
        Commit a contract to Git repository.
        
        Args:
            contract_yaml: Contract content in YAML format
            dataset_name: Name of the dataset
            version: Contract version
            commit_message: Optional commit message
            
        Returns:
            Dictionary with commit information
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
        Retrieve a contract from the repository.
        
        Args:
            dataset_name: Name of the dataset
            version: Contract version
            
        Returns:
            Contract YAML content or None
        """
        safe_name = dataset_name.lower().replace(' ', '_').replace('-', '_')
        filename = f"{safe_name}_v{version}.yaml"
        file_path = self.repo_path / filename
        
        if file_path.exists():
            return file_path.read_text()
        return None
    
    def list_contracts(self) -> List[Dict[str, str]]:
        """
        List all contracts in the repository.
        
        Returns:
            List of contract information
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
        Get commit history for a file or entire repository.
        
        Args:
            filename: Optional filename to filter commits
            
        Returns:
            List of commit information
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
        Create a Git tag.
        
        Args:
            tag_name: Name of the tag
            message: Optional tag message
            
        Returns:
            Tag name
        """
        tag = self.repo.create_tag(
            tag_name,
            message=message or f"Tag: {tag_name}"
        )
        return tag.name
    
    def get_diff(self, commit1: str, commit2: str) -> str:
        """
        Get diff between two commits.
        
        Args:
            commit1: First commit hash
            commit2: Second commit hash
            
        Returns:
            Diff string
        """
        commit_a = self.repo.commit(commit1)
        commit_b = self.repo.commit(commit2)
        
        diff = commit_a.diff(commit_b, create_patch=True)
        
        diff_text = []
        for item in diff:
            if item.diff:
                diff_text.append(item.diff.decode('utf-8'))
        
        return '\n'.join(diff_text)

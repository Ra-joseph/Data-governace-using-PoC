"""
API endpoints for Git repository operations and contract version control.

This module provides REST API endpoints for interacting with the Git repository
that stores data contracts. It enables viewing commit history, comparing versions,
retrieving contract contents, creating tags, and inspecting repository status
for complete audit trails and version control.
"""

from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from app.services.git_service import GitService

router = APIRouter(prefix="/git", tags=["git"])
git_service = GitService()


@router.get("/history")
def get_commit_history(filename: Optional[str] = None):
    """
    Get Git commit history for contracts.

    Retrieves the full commit history for the contract repository or for a
    specific contract file, providing complete audit trail information.

    Args:
        filename: Optional contract filename to filter commits. If None,
                 returns all repository commits.

    Returns:
        Dictionary containing:
            - history: List of commit objects with hash, author, date, message
            - count: Total number of commits

    Raises:
        HTTPException 500: If Git operation fails.

    Example:
        GET /git/history
        GET /git/history?filename=customers_v1.0.0.yaml
    """
    try:
        history = git_service.get_commit_history(filename)
        return {"history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/contracts")
def list_git_contracts():
    """
    List all contracts in the Git repository.

    Scans the repository to discover all stored contract files with metadata.

    Returns:
        Dictionary containing:
            - contracts: List of contract file info (filename, path, size)
            - count: Total number of contracts

    Raises:
        HTTPException 500: If Git operation fails.

    Example:
        GET /git/contracts
    """
    try:
        contracts = git_service.list_contracts()
        return {"contracts": contracts, "count": len(contracts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list contracts: {str(e)}")


@router.get("/diff")
def get_commit_diff(commit1: str, commit2: str):
    """
    Get unified diff between two Git commits.

    Compares two commits to show exactly what changed, useful for understanding
    contract evolution and reviewing changes between versions.

    Args:
        commit1: First commit hash (full or short).
        commit2: Second commit hash (full or short).

    Returns:
        Dictionary containing:
            - commit1: First commit hash
            - commit2: Second commit hash
            - diff: Unified diff string showing changes

    Raises:
        HTTPException 500: If Git operation fails or commits invalid.

    Example:
        GET /git/diff?commit1=abc123&commit2=def456
    """
    try:
        diff = git_service.get_diff(commit1, commit2)
        return {
            "commit1": commit1,
            "commit2": commit2,
            "diff": diff
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get diff: {str(e)}")


@router.get("/contract/{dataset_name}/{version}")
def get_contract_content(dataset_name: str, version: str):
    """
    Get contract content from Git repository.

    Retrieves the raw YAML content for a specific contract version from
    the Git repository.

    Args:
        dataset_name: Name of the dataset.
        version: Semantic version string (e.g., "1.0.0").

    Returns:
        Dictionary containing:
            - dataset_name: Dataset name
            - version: Version string
            - content: Raw YAML contract content

    Raises:
        HTTPException 404: If contract not found.
        HTTPException 500: If Git operation fails.

    Example:
        GET /git/contract/customers/1.0.0
    """
    try:
        content = git_service.get_contract(dataset_name, version)
        if not content:
            raise HTTPException(status_code=404, detail="Contract not found")
        
        return {
            "dataset_name": dataset_name,
            "version": version,
            "content": content
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get contract: {str(e)}")


@router.post("/tags")
def create_git_tag(tag_name: str, message: Optional[str] = None):
    """
    Create a Git tag for marking important versions.

    Creates an annotated tag at the current HEAD, useful for marking release
    versions, production deployments, or important milestones.

    Args:
        tag_name: Name for the tag (e.g., "v1.0.0", "production").
        message: Optional annotation message.

    Returns:
        Dictionary containing:
            - tag: Created tag name
            - message: Tag message

    Raises:
        HTTPException 500: If tag creation fails.

    Example:
        POST /git/tags?tag_name=v1.0.0&message=First+production+release
    """
    try:
        tag = git_service.create_tag(tag_name, message)
        return {
            "tag": tag,
            "message": message or f"Tag: {tag_name}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create tag: {str(e)}")


@router.get("/status")
def get_repository_status():
    """
    Get Git repository status and statistics.

    Provides comprehensive repository information including contract count,
    commit history, branches, tags, and current status.

    Returns:
        Dictionary containing:
            - repository_path: Absolute path to repository
            - total_contracts: Number of contract files
            - total_commits: Total commit count
            - branches: List of branch names
            - tags: List of tag names
            - active_branch: Current branch name
            - last_commit: Most recent commit info

    Raises:
        HTTPException 500: If Git operation fails.

    Example:
        GET /git/status
    """
    try:
        contracts = git_service.list_contracts()
        history = git_service.get_commit_history()
        
        # Get repo statistics
        repo = git_service.repo
        branches = [ref.name for ref in repo.refs]
        tags = [tag.name for tag in repo.tags]
        
        return {
            "repository_path": str(git_service.repo_path),
            "total_contracts": len(contracts),
            "total_commits": len(history),
            "branches": branches,
            "tags": tags,
            "active_branch": repo.active_branch.name if repo.active_branch else None,
            "last_commit": history[0] if history else None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/file-history/{filename}")
def get_file_history(filename: str):
    """
    Get detailed commit history for a specific contract file.

    Retrieves all commits that modified a particular contract file, providing
    a complete audit trail for that contract's evolution.

    Args:
        filename: Name of the contract file (e.g., "customers_v1.0.0.yaml").

    Returns:
        Dictionary containing:
            - filename: Contract filename
            - commits: List of commits affecting this file
            - total_commits: Number of commits

    Raises:
        HTTPException 404: If file not found in repository.
        HTTPException 500: If Git operation fails.

    Example:
        GET /git/file-history/customers_v1.0.0.yaml
    """
    try:
        history = git_service.get_commit_history(filename)
        
        if not history:
            raise HTTPException(status_code=404, detail="File not found in repository")
        
        return {
            "filename": filename,
            "commits": history,
            "total_commits": len(history)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get file history: {str(e)}")


@router.get("/blame/{filename}")
def get_file_blame(filename: str):
    """
    Get Git blame (line-by-line authorship) for a contract file.

    Shows which commit and author last modified each line in a contract,
    useful for understanding who made specific changes and when.

    Args:
        filename: Name of the contract file (e.g., "customers_v1.0.0.yaml").

    Returns:
        Dictionary containing:
            - filename: Contract filename
            - blame: List of line objects with commit, author, date, message

    Raises:
        HTTPException 404: If file not found.
        HTTPException 500: If Git operation fails.

    Example:
        GET /git/blame/customers_v1.0.0.yaml
    """
    try:
        repo = git_service.repo
        file_path = git_service.repo_path / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        # Get blame information
        blame = repo.blame('HEAD', filename)
        
        blame_data = []
        for commit, lines in blame:
            for line in lines:
                blame_data.append({
                    "line": line,
                    "commit": commit.hexsha[:7],
                    "author": str(commit.author),
                    "date": commit.committed_datetime.isoformat(),
                    "message": commit.message.strip()
                })
        
        return {
            "filename": filename,
            "blame": blame_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get blame: {str(e)}")

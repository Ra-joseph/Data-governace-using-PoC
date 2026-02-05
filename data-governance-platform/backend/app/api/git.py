from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException
from app.services.git_service import GitService

router = APIRouter(prefix="/git", tags=["git"])
git_service = GitService()


@router.get("/history")
def get_commit_history(filename: Optional[str] = None):
    """
    Get Git commit history for contracts.
    
    Args:
        filename: Optional filename to filter commits
    """
    try:
        history = git_service.get_commit_history(filename)
        return {"history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get history: {str(e)}")


@router.get("/contracts")
def list_git_contracts():
    """List all contracts in the Git repository."""
    try:
        contracts = git_service.list_contracts()
        return {"contracts": contracts, "count": len(contracts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list contracts: {str(e)}")


@router.get("/diff")
def get_commit_diff(commit1: str, commit2: str):
    """
    Get diff between two Git commits.
    
    Args:
        commit1: First commit hash
        commit2: Second commit hash
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
    Get contract content from Git.
    
    Args:
        dataset_name: Name of the dataset
        version: Contract version
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
    Create a Git tag.
    
    Args:
        tag_name: Name of the tag
        message: Optional tag message
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
    """Get Git repository status and statistics."""
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
    Get detailed history for a specific contract file.
    
    Args:
        filename: Name of the contract file
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
    
    Args:
        filename: Name of the contract file
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

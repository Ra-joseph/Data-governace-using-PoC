"""
API endpoints for semantic policy scanning using LLM.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.contract import Contract
from app.services.semantic_policy_engine import SemanticPolicyEngine
from app.services.ollama_client import get_ollama_client
from app.schemas.contract import ValidationResult

router = APIRouter(prefix="/semantic", tags=["semantic-scanning"])


class SemanticHealthResponse(BaseModel):
    """Response model for semantic scanning health check."""
    available: bool
    ollama_running: bool
    available_models: List[str]
    current_model: str
    policies_loaded: int
    message: str


class SemanticValidationRequest(BaseModel):
    """Request model for semantic validation."""
    contract_id: int
    selected_policies: Optional[List[str]] = None


@router.get("/health", response_model=SemanticHealthResponse)
def check_semantic_health():
    """
    Check if semantic scanning is available and properly configured.

    Returns information about Ollama status, available models, and loaded policies.
    """
    try:
        # Initialize semantic engine
        semantic_engine = SemanticPolicyEngine(enabled=True)

        # Check Ollama availability
        ollama_client = semantic_engine.llm_client
        ollama_running = ollama_client.is_available() if ollama_client else False

        # Get available models
        available_models = []
        current_model = "not configured"

        if ollama_running:
            available_models = ollama_client.list_models()
            current_model = ollama_client.model

        # Count loaded policies
        policies_count = len(semantic_engine.policies.get('policies', []))

        # Determine overall availability
        is_available = semantic_engine.is_available()

        # Generate message
        if is_available:
            message = f"Semantic scanning is available with {policies_count} policies"
        elif not ollama_running:
            message = "Ollama is not running. Start it with: ollama serve"
        elif not available_models:
            message = f"Ollama is running but model '{current_model}' not found. Pull it with: ollama pull {current_model}"
        elif policies_count == 0:
            message = "No semantic policies loaded"
        else:
            message = "Semantic scanning is not available"

        return SemanticHealthResponse(
            available=is_available,
            ollama_running=ollama_running,
            available_models=available_models,
            current_model=current_model,
            policies_loaded=policies_count,
            message=message
        )

    except Exception as e:
        return SemanticHealthResponse(
            available=False,
            ollama_running=False,
            available_models=[],
            current_model="error",
            policies_loaded=0,
            message=f"Error checking semantic health: {str(e)}"
        )


@router.get("/policies")
def list_semantic_policies():
    """
    List all available semantic policies.

    Returns the semantic policies that can be run, with their descriptions.
    """
    try:
        semantic_engine = SemanticPolicyEngine(enabled=False)  # Don't need Ollama to list policies
        policies_list = semantic_engine.policies.get('policies', [])

        return {
            "total": len(policies_list),
            "policies": [
                {
                    "id": policy['id'],
                    "name": policy['name'],
                    "severity": policy['severity'],
                    "description": policy['description']
                }
                for policy in policies_list
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load policies: {str(e)}")


@router.post("/validate", response_model=ValidationResult)
def validate_with_semantic(
    request: SemanticValidationRequest,
    db: Session = Depends(get_db)
):
    """
    Run semantic validation on an existing contract.

    This endpoint runs only semantic policies (not rule-based policies)
    on a contract and returns the results.
    """
    # Get contract
    contract = db.query(Contract).filter(Contract.id == request.contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {request.contract_id} not found")

    # Initialize semantic engine
    semantic_engine = SemanticPolicyEngine(enabled=True)

    if not semantic_engine.is_available():
        raise HTTPException(
            status_code=503,
            detail="Semantic scanning is not available. Ensure Ollama is running and the model is loaded."
        )

    # Run semantic validation
    try:
        contract_data = contract.machine_readable

        result = semantic_engine.validate_contract(
            contract_data,
            selected_policies=request.selected_policies
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Semantic validation failed: {str(e)}"
        )


@router.get("/models")
def list_available_models():
    """
    List available LLM models in Ollama.

    Returns the models that can be used for semantic scanning.
    """
    try:
        ollama_client = get_ollama_client()

        if not ollama_client.is_available():
            raise HTTPException(
                status_code=503,
                detail="Ollama is not running. Start it with: ollama serve"
            )

        models = ollama_client.list_models()

        return {
            "total": len(models),
            "current_model": ollama_client.model,
            "models": models,
            "recommended_models": [
                "mistral:7b",
                "codellama:7b",
                "llama2:7b",
                "phi:latest"
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list models: {str(e)}")


@router.post("/models/pull/{model_name}")
def pull_model(model_name: str):
    """
    Trigger a model pull in Ollama.

    Note: This endpoint initiates the pull but returns immediately.
    The actual download happens in the background in Ollama.
    """
    import requests

    try:
        ollama_client = get_ollama_client()

        if not ollama_client.is_available():
            raise HTTPException(
                status_code=503,
                detail="Ollama is not running. Start it with: ollama serve"
            )

        # Trigger pull via Ollama API
        response = requests.post(
            f"{ollama_client.base_url}/api/pull",
            json={"name": model_name, "stream": False},
            timeout=120
        )

        response.raise_for_status()

        return {
            "message": f"Model '{model_name}' pull initiated",
            "model": model_name,
            "note": "Download is happening in background. Use /semantic/models to check when complete."
        }

    except requests.exceptions.Timeout:
        return {
            "message": f"Model '{model_name}' pull initiated (may take several minutes)",
            "model": model_name,
            "note": "Large models can take time to download. Check /semantic/models to verify completion."
        }
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to pull model: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

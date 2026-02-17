"""
API endpoints for semantic policy scanning using LLM.

This module provides REST API endpoints for semantic validation of data contracts
using large language models (LLMs) via Ollama. It enables checking semantic policies
that require contextual understanding beyond rule-based validation, such as naming
conventions, documentation quality, and business logic consistency.
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

    Verifies that Ollama is running, required models are available, and semantic
    policies are loaded. Provides diagnostic information for troubleshooting.

    Returns:
        Health status including:
            - available: Overall availability boolean
            - ollama_running: Whether Ollama service is running
            - available_models: List of pulled models
            - current_model: Configured model name
            - policies_loaded: Number of semantic policies loaded
            - message: Human-readable status message

    Example:
        GET /semantic/health
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

    Returns metadata about all semantic policies that can be run against
    contracts, including their IDs, names, severity levels, and descriptions.

    Returns:
        Dictionary containing:
            - total: Number of semantic policies
            - policies: List of policy objects (id, name, severity, description)

    Raises:
        HTTPException 500: If policies cannot be loaded.

    Example:
        GET /semantic/policies
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
    Run semantic validation on an existing contract using LLM.

    Performs semantic policy validation using large language models to check
    for issues that require contextual understanding. This runs only semantic
    policies (not rule-based policies) and returns detailed validation results.

    Args:
        request: Validation request containing:
            - contract_id: ID of contract to validate
            - selected_policies: Optional list of policy IDs to run
        db: Database session (injected dependency).

    Returns:
        ValidationResult with status, violation counts, and detailed violations.

    Raises:
        HTTPException 404: If contract not found.
        HTTPException 503: If Ollama is not available or model not loaded.
        HTTPException 500: If validation fails.

    Example:
        POST /semantic/validate
        {
          "contract_id": 1,
          "selected_policies": ["SEM001", "SEM002"]
        }
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

    Queries Ollama to get all downloaded models that can be used for semantic
    scanning, along with recommended models for optimal performance.

    Returns:
        Dictionary containing:
            - total: Number of available models
            - current_model: Currently configured model
            - models: List of available model names
            - recommended_models: List of recommended model names

    Raises:
        HTTPException 503: If Ollama is not running.
        HTTPException 500: If query fails.

    Example:
        GET /semantic/models
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
    Trigger a model download in Ollama.

    Initiates downloading a model from Ollama's registry. The endpoint returns
    immediately while the download continues in the background. Large models
    may take several minutes to download.

    Args:
        model_name: Name of the model to pull (e.g., "mistral:7b", "llama2:7b").

    Returns:
        Dictionary containing:
            - message: Status message
            - model: Model name being pulled
            - note: Additional information about background download

    Raises:
        HTTPException 503: If Ollama is not running.
        HTTPException 500: If pull request fails.

    Example:
        POST /semantic/models/pull/mistral:7b

    Note:
        The download happens asynchronously. Use GET /semantic/models to check
        when the model is available.
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

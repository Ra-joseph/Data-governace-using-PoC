"""
API endpoints for policy orchestration - intelligent routing between validation engines.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.models.contract import Contract
from app.services.policy_orchestrator import (
    PolicyOrchestrator,
    ValidationStrategy,
    RiskLevel
)
from app.schemas.contract import ValidationResult

router = APIRouter(prefix="/orchestration", tags=["orchestration"])


class AnalyzeContractRequest(BaseModel):
    """Request model for contract analysis."""
    contract_id: int


class AnalyzeContractResponse(BaseModel):
    """Response model for contract analysis."""
    contract_id: int
    contract_name: str
    risk_level: str
    complexity_score: int
    has_pii: bool
    has_sensitive_data: bool
    classification: str
    requires_compliance: bool
    compliance_frameworks: list
    field_count: int
    concerns: list
    recommended_strategy: str
    reasoning: str


class ValidateWithStrategyRequest(BaseModel):
    """Request model for validation with specific strategy."""
    contract_id: int
    strategy: ValidationStrategy = ValidationStrategy.ADAPTIVE


class StrategyRecommendationRequest(BaseModel):
    """Request model for strategy recommendation."""
    contract_id: int


class StrategyRecommendationResponse(BaseModel):
    """Response model for strategy recommendation."""
    contract_id: int
    recommended_strategy: str
    reasoning: str
    estimated_time_seconds: float
    will_use_rule_based: bool
    will_use_semantic: bool
    semantic_policies_count: Optional[int]


@router.get("/strategies")
def list_validation_strategies():
    """
    List available validation strategies.

    Returns information about each strategy and when to use it.
    """
    return {
        "strategies": [
            {
                "name": "FAST",
                "description": "Rule-based validation only",
                "use_when": "Low-risk data, simple schemas, development environments",
                "speed": "Very fast (<100ms)",
                "coverage": "Basic (rule-based policies only)"
            },
            {
                "name": "BALANCED",
                "description": "Rule-based + targeted semantic policies",
                "use_when": "Most production use cases (recommended default)",
                "speed": "Moderate (2-10 seconds)",
                "coverage": "Good (rules + relevant semantic policies)"
            },
            {
                "name": "THOROUGH",
                "description": "Complete validation with all policies",
                "use_when": "Critical data, compliance audits, production releases",
                "speed": "Slow (20-30 seconds)",
                "coverage": "Comprehensive (all policies)"
            },
            {
                "name": "ADAPTIVE",
                "description": "Automatically chooses strategy based on risk",
                "use_when": "Unknown risk level (smart default)",
                "speed": "Variable (adjusts to risk)",
                "coverage": "Risk-appropriate"
            }
        ],
        "default": "ADAPTIVE",
        "recommendation": "Use ADAPTIVE for automatic intelligence, or BALANCED for predictable performance"
    }


@router.post("/analyze", response_model=AnalyzeContractResponse)
def analyze_contract(
    request: AnalyzeContractRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a contract to determine its risk level and recommended validation strategy.

    This endpoint examines contract characteristics like PII, classification,
    complexity, and compliance requirements to assess risk and recommend
    an appropriate validation strategy.
    """
    # Get contract
    contract = db.query(Contract).filter(Contract.id == request.contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Contract {request.contract_id} not found"
        )

    # Initialize orchestrator
    orchestrator = PolicyOrchestrator(enable_semantic=True)

    # Analyze contract
    contract_data = contract.machine_readable
    analysis = orchestrator._analyze_contract(contract_data)

    # Get recommended strategy
    recommended_strategy, reasoning = orchestrator.get_recommended_strategy(contract_data)

    return AnalyzeContractResponse(
        contract_id=contract.id,
        contract_name=contract_data.get('dataset', {}).get('name', 'Unknown'),
        risk_level=analysis.risk_level.value,
        complexity_score=analysis.complexity_score,
        has_pii=analysis.has_pii,
        has_sensitive_data=analysis.has_sensitive_data,
        classification=analysis.classification,
        requires_compliance=analysis.requires_compliance,
        compliance_frameworks=analysis.compliance_frameworks,
        field_count=analysis.field_count,
        concerns=analysis.concerns,
        recommended_strategy=recommended_strategy.value,
        reasoning=reasoning
    )


@router.post("/validate", response_model=ValidationResult)
def validate_with_strategy(
    request: ValidateWithStrategyRequest,
    db: Session = Depends(get_db)
):
    """
    Validate a contract using a specific strategy.

    This endpoint allows you to choose the validation strategy:
    - FAST: Rule-based only (fastest)
    - BALANCED: Rules + targeted semantic (recommended)
    - THOROUGH: All policies (most comprehensive)
    - ADAPTIVE: Automatically chooses based on risk (smart default)
    """
    # Get contract
    contract = db.query(Contract).filter(Contract.id == request.contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Contract {request.contract_id} not found"
        )

    # Initialize orchestrator
    orchestrator = PolicyOrchestrator(enable_semantic=True)

    # Validate with specified strategy
    try:
        result = orchestrator.validate_contract(
            contract.machine_readable,
            strategy=request.strategy
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/recommend-strategy", response_model=StrategyRecommendationResponse)
def recommend_strategy(
    request: StrategyRecommendationRequest,
    db: Session = Depends(get_db)
):
    """
    Get recommended validation strategy for a contract.

    Analyzes the contract and recommends the optimal validation strategy
    based on risk level, complexity, and data sensitivity.
    """
    # Get contract
    contract = db.query(Contract).filter(Contract.id == request.contract_id).first()
    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Contract {request.contract_id} not found"
        )

    # Initialize orchestrator
    orchestrator = PolicyOrchestrator(enable_semantic=True)

    # Get recommendation
    contract_data = contract.machine_readable
    recommended_strategy, reasoning = orchestrator.get_recommended_strategy(contract_data)

    # Get decision details
    analysis = orchestrator._analyze_contract(contract_data)
    decision = orchestrator._make_orchestration_decision(analysis, recommended_strategy)

    return StrategyRecommendationResponse(
        contract_id=contract.id,
        recommended_strategy=recommended_strategy.value,
        reasoning=reasoning,
        estimated_time_seconds=decision.estimated_time_seconds,
        will_use_rule_based=decision.use_rule_based,
        will_use_semantic=decision.use_semantic,
        semantic_policies_count=len(decision.semantic_policies) if decision.semantic_policies else 0
    )


@router.get("/stats")
def get_orchestration_stats():
    """
    Get statistics about orchestration capabilities.

    Returns information about available engines, policies, and performance.
    """
    orchestrator = PolicyOrchestrator(enable_semantic=True)

    # Check semantic availability
    semantic_available = orchestrator.semantic_engine.is_available()

    # Count policies
    rule_policies = len(orchestrator.rule_engine._get_all_policy_ids())
    semantic_policies = len(orchestrator.semantic_engine.policies.get('policies', []))

    return {
        "engines": {
            "rule_based": {
                "available": True,
                "policies": rule_policies,
                "avg_time_ms": 50
            },
            "semantic": {
                "available": semantic_available,
                "policies": semantic_policies,
                "avg_time_ms": 3000
            }
        },
        "strategies": {
            "fast": {
                "uses_rule_based": True,
                "uses_semantic": False,
                "avg_time_seconds": 0.05
            },
            "balanced": {
                "uses_rule_based": True,
                "uses_semantic": True,
                "avg_semantic_policies": 3,
                "avg_time_seconds": 9.0
            },
            "thorough": {
                "uses_rule_based": True,
                "uses_semantic": True,
                "avg_semantic_policies": semantic_policies,
                "avg_time_seconds": 24.0
            }
        },
        "total_policies": rule_policies + (semantic_policies if semantic_available else 0),
        "recommendation": "Use ADAPTIVE strategy for automatic intelligence"
    }

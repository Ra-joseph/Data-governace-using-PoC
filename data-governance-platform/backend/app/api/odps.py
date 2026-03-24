"""ODPS 4.1 API endpoints.

Exposes data product descriptors in the Open Data Product Specification 4.1
format so that external tools (Alation, Collibra, AI agents) can
auto-discover and consume data products.

Spec: https://opendataproducts.org
MIME type: application/odps+yaml;version=1.0.0
"""

from typing import Any, Dict, List

import yaml
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.schemas.odps import OdpsProductSummary, OdpsValidationResult, OdpsViolation
from app.services.odps_service import OdpsService

router = APIRouter()

# Singleton service instance — loads descriptors from backend/odps/ on first use
_odps_service = OdpsService()

_ODPS_MIME_TYPE = "application/odps+yaml;version=1.0.0"


@router.get(
    "/products",
    response_model=List[OdpsProductSummary],
    summary="List all ODPS-described data products",
    description=(
        "Returns a lightweight summary of every data product that has an "
        "ODPS 4.1 descriptor in the backend/odps/ directory."
    ),
)
def list_odps_products() -> List[OdpsProductSummary]:
    """List all available ODPS 4.1 data product descriptors.

    Returns:
        List of product summaries with id, name, domain, owner, access type,
        and governance frameworks.
    """
    return _odps_service.list_all_products()


@router.get(
    "/products/{product_id}",
    summary="Get ODPS descriptor for a data product",
    description=(
        "Returns the full ODPS 4.1 YAML descriptor for the requested product. "
        "The response uses Content-Type: application/odps+yaml;version=1.0.0 "
        "so external catalogue tools can parse it directly."
    ),
    responses={
        200: {
            "content": {_ODPS_MIME_TYPE: {}},
            "description": "ODPS 4.1 YAML descriptor",
        },
        404: {"description": "No descriptor found for the given product_id"},
    },
)
def get_odps_descriptor(product_id: str) -> Response:
    """Return the ODPS 4.1 descriptor for *product_id* as YAML.

    Args:
        product_id: The product identifier (matches the file name in odps/).

    Returns:
        YAML-encoded ODPS descriptor with the correct MIME type.

    Raises:
        HTTPException: 404 if no descriptor exists for *product_id*.
    """
    try:
        descriptor = _odps_service.load_odps_descriptor(product_id)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"ODPS descriptor not found for product '{product_id}'.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    yaml_content = yaml.dump(descriptor, default_flow_style=False, allow_unicode=True)
    return Response(content=yaml_content, media_type=_ODPS_MIME_TYPE)


@router.get(
    "/products/{product_id}/validate",
    response_model=OdpsValidationResult,
    summary="Validate a dataset against its ODPS quality declarations",
    description=(
        "Runs ODPS quality threshold validation for the given product. "
        "Supply actual dataset statistics as query parameters. "
        "Dimensions not supplied are skipped (not failed)."
    ),
)
def validate_odps_product(
    product_id: str,
    completeness_pct: float = None,
    accuracy_pct: float = None,
    freshness_hours: float = None,
) -> OdpsValidationResult:
    """Validate a dataset's actual stats against its declared ODPS thresholds.

    Args:
        product_id: ODPS product identifier.
        completeness_pct: Actual completeness percentage (0–100).
        accuracy_pct: Actual accuracy percentage (0–100).
        freshness_hours: Age of the most recent data in hours.

    Returns:
        OdpsValidationResult with status (compliant | non-compliant) and
        a list of threshold violations.

    Raises:
        HTTPException: 404 if no descriptor exists for *product_id*.
    """
    if not _odps_service.descriptor_exists(product_id):
        raise HTTPException(
            status_code=404,
            detail=f"ODPS descriptor not found for product '{product_id}'.",
        )

    # Build stats dict from provided query params (only non-None values)
    dataset_stats: Dict[str, float] = {}
    if completeness_pct is not None:
        dataset_stats["completeness_pct"] = completeness_pct
    if accuracy_pct is not None:
        dataset_stats["accuracy_pct"] = accuracy_pct
    if freshness_hours is not None:
        dataset_stats["freshness_hours"] = freshness_hours

    violations: List[OdpsViolation] = _odps_service.validate_dataset_against_odps(
        product_id, dataset_stats
    )

    status = "non-compliant" if violations else "compliant"
    return OdpsValidationResult(
        product_id=product_id,
        status=status,
        violations=violations,
    )

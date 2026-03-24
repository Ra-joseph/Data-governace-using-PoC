"""Pydantic schemas for ODPS 4.1 (Open Data Product Specification) objects.

Covers: OdpsDescriptor, OdpsViolation, OdpsValidationResult and all
nested sub-models that mirror the ODPS 4.1 YAML structure.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Sub-models — nested inside OdpsDescriptor
# ---------------------------------------------------------------------------

class OdpsProduct(BaseModel):
    """Top-level product identity block."""

    id: str = Field(..., description="Unique product identifier (slug)")
    name: str = Field(..., description="Human-readable product name")
    status: str = Field(..., description="Lifecycle status: active | draft | deprecated")
    domain: str = Field(..., description="Business domain (analytics, finance, hr, commerce)")
    owner: str = Field(..., description="Owner email or team identifier")
    description: str = Field(..., description="Purpose and content of the data product")


class OdpsQualityDimension(BaseModel):
    """A single quality dimension with its declared threshold."""

    name: str = Field(
        ...,
        description="Dimension name: completeness | accuracy | timeliness | consistency | uniqueness",
    )
    threshold: float = Field(..., description="Declared threshold value")
    unit: str = Field(..., description="Unit of measurement: percentage | count | ms")


class OdpsQuality(BaseModel):
    """Quality block containing one or more declared dimensions."""

    dimensions: List[OdpsQualityDimension] = Field(
        default_factory=list,
        description="List of quality dimensions and their thresholds",
    )


class OdpsSla(BaseModel):
    """Service Level Agreement block."""

    updateFrequency: str = Field(
        ..., description="Data refresh cadence: realtime | hourly | daily | weekly"
    )
    uptimePercentage: float = Field(..., description="Minimum uptime guarantee (0–100)")
    responseTimeMs: int = Field(..., description="Maximum API response latency in milliseconds")


class OdpsOutputPort(BaseModel):
    """A single data access output port."""

    id: str = Field(..., description="Unique port identifier")
    type: str = Field(..., description="Port type: API | SQL | S3 | event | GraphQL")
    location: str = Field(..., description="Connection string, URL, or table reference")


class OdpsDataAccess(BaseModel):
    """Data access block describing how consumers connect to the product."""

    personalData: bool = Field(..., description="Whether the product contains personal data")
    accessType: str = Field(
        ..., description="Access model: open | restricted | private"
    )
    outputPorts: List[OdpsOutputPort] = Field(
        default_factory=list,
        description="Available output ports for data access",
    )


class OdpsLicense(BaseModel):
    """Licensing and governance framework block."""

    scope: str = Field(
        ..., description="License scope: internal | public | commercial"
    )
    governance: List[str] = Field(
        default_factory=list,
        description="Applicable governance frameworks (e.g., GDPR, SOX, PCI-DSS)",
    )


class OdpsPricing(BaseModel):
    """Pricing model block."""

    model: str = Field(
        ..., description="Pricing model: free | subscription | usage-based"
    )
    plan: str = Field(..., description="Plan name (e.g., internal-use)")


# ---------------------------------------------------------------------------
# Root descriptor
# ---------------------------------------------------------------------------

class OdpsDescriptor(BaseModel):
    """Complete ODPS 4.1 data product descriptor."""

    odpsVersion: str = Field("4.1", description="ODPS specification version")
    product: OdpsProduct
    quality: OdpsQuality
    sla: OdpsSla
    dataAccess: OdpsDataAccess
    license: OdpsLicense
    pricing: OdpsPricing

    class Config:
        json_schema_extra = {
            "example": {
                "odpsVersion": "4.1",
                "product": {
                    "id": "customer_accounts",
                    "name": "Customer Accounts",
                    "status": "active",
                    "domain": "analytics",
                    "owner": "alice.chen@company.com",
                    "description": "Core customer account data.",
                },
                "quality": {
                    "dimensions": [
                        {"name": "completeness", "threshold": 95, "unit": "percentage"}
                    ]
                },
                "sla": {
                    "updateFrequency": "daily",
                    "uptimePercentage": 99.5,
                    "responseTimeMs": 5000,
                },
                "dataAccess": {
                    "personalData": True,
                    "accessType": "restricted",
                    "outputPorts": [
                        {
                            "id": "sql-port",
                            "type": "SQL",
                            "location": "analytics.public.customer_accounts",
                        }
                    ],
                },
                "license": {"scope": "internal", "governance": ["GDPR", "CCPA"]},
                "pricing": {"model": "free", "plan": "internal-use"},
            }
        }


# ---------------------------------------------------------------------------
# Violation & validation result
# ---------------------------------------------------------------------------

class OdpsViolation(BaseModel):
    """A single ODPS quality threshold violation."""

    dimension: str = Field(
        ..., description="Quality dimension that failed (e.g., completeness)"
    )
    declared_threshold: float = Field(
        ..., description="Threshold declared in the ODPS descriptor"
    )
    actual_value: float = Field(
        ..., description="Actual measured value from the dataset"
    )
    unit: str = Field(..., description="Unit of measurement (percentage, count, ms)")
    message: str = Field(..., description="Human-readable violation description")
    source: str = Field(
        default="odps-spec",
        description="Source of this violation (always 'odps-spec' for ODPS checks)",
    )


class OdpsValidationResult(BaseModel):
    """Result of validating a dataset against its ODPS quality declarations."""

    product_id: str = Field(..., description="ODPS product identifier")
    status: str = Field(
        ..., description="Overall validation outcome: compliant | non-compliant"
    )
    violations: List[OdpsViolation] = Field(
        default_factory=list,
        description="List of threshold violations found",
    )
    checked_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when validation was performed",
    )


class OdpsProductSummary(BaseModel):
    """Lightweight summary for the list-all-products endpoint."""

    id: str
    name: str
    status: str
    domain: str
    owner: str
    personal_data: bool
    access_type: str
    governance_frameworks: List[str]
    descriptor_url: str

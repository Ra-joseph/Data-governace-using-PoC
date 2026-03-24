"""ODPS 4.1 (Open Data Product Specification) service.

Loads, validates, and queries ODPS 4.1 YAML descriptors stored in
``backend/odps/``.  Each descriptor describes a data product in a
machine-readable format compatible with the Linux Foundation LF AI & Data
Open Data Product Specification.

Spec reference: https://opendataproducts.org
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from app.schemas.odps import (
    OdpsDescriptor,
    OdpsProductSummary,
    OdpsValidationResult,
    OdpsViolation,
)


# Default path resolved relative to this file so the service works regardless
# of the working directory at start-up.
_DEFAULT_ODPS_DIR = Path(__file__).resolve().parents[3] / "odps"


class OdpsService:
    """Service for loading and validating ODPS 4.1 data product descriptors.

    Descriptors are stored as YAML files in ``backend/odps/``.  The file name
    (without extension) is used as the ``product_id``.

    Example usage::

        service = OdpsService()
        descriptor = service.load_odps_descriptor("customer_accounts")
        thresholds = service.get_quality_thresholds("customer_accounts")
        violations = service.validate_dataset_against_odps(
            "customer_accounts", {"completeness_pct": 92.0, "accuracy_pct": 97.0}
        )
    """

    def __init__(self, odps_dir: Optional[str] = None) -> None:
        """Initialise the service, pointing at the ODPS descriptors directory.

        Args:
            odps_dir: Absolute or relative path to the folder that contains
                the ODPS YAML files.  Defaults to ``backend/odps/`` resolved
                relative to this file.
        """
        self.odps_dir = Path(odps_dir) if odps_dir else _DEFAULT_ODPS_DIR

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_odps_descriptor(self, product_id: str) -> Dict[str, Any]:
        """Load and return the raw ODPS YAML descriptor for *product_id*.

        Args:
            product_id: The product identifier, which must match the YAML
                file name (without the ``.yaml`` extension) in ``odps/``.

        Returns:
            Parsed YAML as a Python dict.

        Raises:
            FileNotFoundError: If no descriptor exists for *product_id*.
            ValueError: If the YAML file cannot be parsed.
        """
        path = self.odps_dir / f"{product_id}.yaml"
        if not path.exists():
            raise FileNotFoundError(
                f"ODPS descriptor not found for product '{product_id}'. "
                f"Expected file: {path}"
            )
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = yaml.safe_load(fh)
        except yaml.YAMLError as exc:
            raise ValueError(
                f"Failed to parse ODPS descriptor for '{product_id}': {exc}"
            ) from exc
        return data

    def get_quality_thresholds(self, product_id: str) -> List[Dict[str, Any]]:
        """Return the list of quality dimensions declared in the descriptor.

        Args:
            product_id: ODPS product identifier.

        Returns:
            List of dicts, each with keys ``name``, ``threshold``, ``unit``.
            Returns an empty list if the descriptor has no quality block.
        """
        descriptor = self.load_odps_descriptor(product_id)
        quality = descriptor.get("quality", {})
        return quality.get("dimensions", [])

    def get_governance_frameworks(self, product_id: str) -> List[str]:
        """Return the governance frameworks listed in the license block.

        Args:
            product_id: ODPS product identifier.

        Returns:
            List of framework names (e.g., ``["GDPR", "CCPA"]``).
            Returns an empty list if no governance entry is present.
        """
        descriptor = self.load_odps_descriptor(product_id)
        license_block = descriptor.get("license", {})
        return license_block.get("governance", [])

    def list_all_products(self) -> List[OdpsProductSummary]:
        """List summary metadata for every ODPS descriptor in the folder.

        Returns:
            List of :class:`OdpsProductSummary` objects, one per YAML file
            found in the ``odps/`` directory.  Files that cannot be parsed
            are silently skipped.
        """
        summaries: List[OdpsProductSummary] = []
        if not self.odps_dir.exists():
            return summaries

        for yaml_file in sorted(self.odps_dir.glob("*.yaml")):
            product_id = yaml_file.stem
            try:
                descriptor = self.load_odps_descriptor(product_id)
                product = descriptor.get("product", {})
                data_access = descriptor.get("dataAccess", {})
                license_block = descriptor.get("license", {})
                summaries.append(
                    OdpsProductSummary(
                        id=product.get("id", product_id),
                        name=product.get("name", product_id),
                        status=product.get("status", "unknown"),
                        domain=product.get("domain", ""),
                        owner=product.get("owner", ""),
                        personal_data=data_access.get("personalData", False),
                        access_type=data_access.get("accessType", "restricted"),
                        governance_frameworks=license_block.get("governance", []),
                        descriptor_url=f"/api/odps/products/{product_id}",
                    )
                )
            except (FileNotFoundError, ValueError):
                # Skip unreadable descriptors; do not crash the listing
                continue

        return summaries

    def validate_dataset_against_odps(
        self, product_id: str, dataset_stats: Dict[str, Any]
    ) -> List[OdpsViolation]:
        """Compare actual dataset statistics against declared ODPS thresholds.

        Only dimensions whose names appear in *dataset_stats* are checked.
        Unmeasured dimensions are skipped rather than flagged as violations.

        Supported *dataset_stats* keys:

        - ``completeness_pct`` — actual completeness percentage (0–100)
        - ``accuracy_pct`` — actual accuracy percentage (0–100)
        - ``freshness_hours`` — age of the most recent data, in hours

        Args:
            product_id: ODPS product identifier.
            dataset_stats: Dict of actual measured statistics.

        Returns:
            List of :class:`OdpsViolation` objects (empty if compliant).

        Raises:
            FileNotFoundError: If no descriptor exists for *product_id*.
        """
        dimensions = self.get_quality_thresholds(product_id)
        violations: List[OdpsViolation] = []

        # Mapping from ODPS dimension name → dataset_stats key
        stat_key_map: Dict[str, str] = {
            "completeness": "completeness_pct",
            "accuracy": "accuracy_pct",
            "timeliness": "freshness_hours",
        }

        for dim in dimensions:
            dim_name: str = dim.get("name", "")
            threshold: float = float(dim.get("threshold", 0))
            unit: str = dim.get("unit", "")

            stat_key = stat_key_map.get(dim_name)
            if stat_key is None or stat_key not in dataset_stats:
                # Dimension not measured — skip
                continue

            actual: float = float(dataset_stats[stat_key])

            # For timeliness, lower is better (freshness_hours should be ≤ threshold)
            is_violation = (
                actual > threshold
                if dim_name == "timeliness"
                else actual < threshold
            )

            if is_violation:
                if dim_name == "timeliness":
                    msg = (
                        f"Data freshness violation: data is {actual:.1f} hours old "
                        f"but ODPS declares a maximum of {threshold:.1f} hours."
                    )
                else:
                    msg = (
                        f"Quality violation for '{dim_name}': actual {actual:.1f}% "
                        f"is below the declared ODPS threshold of {threshold:.1f}%."
                    )
                violations.append(
                    OdpsViolation(
                        dimension=dim_name,
                        declared_threshold=threshold,
                        actual_value=actual,
                        unit=unit,
                        message=msg,
                        source="odps-spec",
                    )
                )

        return violations

    def build_odps_block(self, product_id: str, compliance_status: str) -> Dict[str, Any]:
        """Build the compact ``odps`` block embedded in generated contracts.

        Args:
            product_id: ODPS product identifier (must match a descriptor file).
            compliance_status: ``"compliant"`` or ``"non-compliant"``.

        Returns:
            Dict suitable for embedding under the ``odps`` key of a contract.
        """
        return {
            "specVersion": "4.1",
            "standard": "https://opendataproducts.org",
            "descriptorUrl": f"/api/odps/products/{product_id}",
            "complianceStatus": compliance_status,
        }

    def descriptor_exists(self, product_id: str) -> bool:
        """Return True if an ODPS descriptor file exists for *product_id*.

        Args:
            product_id: ODPS product identifier.

        Returns:
            True if ``odps/{product_id}.yaml`` exists, False otherwise.
        """
        return (self.odps_dir / f"{product_id}.yaml").exists()

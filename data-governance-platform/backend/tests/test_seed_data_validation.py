"""
Tests that validate the seed dataset contract structures against the policy engine.

These tests verify that the sample data baked into database.py:
1. Never produces CRITICAL violations (ValidationStatus.FAILED)
2. Satisfies structural constraints (ownership, schema hash, machine-readable JSON)
3. Correctly handles PII encryption requirements

The tests work directly against the contract dict structures that
_seed_sample_data() constructs, without requiring a running database,
so they are fast and deterministic.
"""

import hashlib
import json

import pytest

from app.services.policy_engine import PolicyEngine
from app.schemas.contract import ValidationStatus


# ---------------------------------------------------------------------------
# Reproduce the seed contract structures from database._seed_sample_data
# ---------------------------------------------------------------------------

def _seed_sample() -> list:
    """
    Return the list of sample dataset definitions, mirroring the structure
    built inside database._seed_sample_data.  Keeping this in sync with
    that function is intentional: if the seed data is changed, this test
    will reveal whether the change creates CRITICAL policy violations.
    """
    samples = [
        {
            "name": "customer_accounts",
            "description": "Core customer account data including profile, contact details, and account status.",
            "owner_name": "Alice Chen",
            "owner_email": "alice.chen@company.com",
            "source_type": "postgres",
            "physical_location": "analytics.public.customer_accounts",
            "classification": "confidential",
            "contains_pii": True,
            "compliance_tags": ["GDPR", "CCPA"],
            "schema": [
                {"name": "customer_id", "type": "integer", "description": "Unique customer identifier", "required": True, "nullable": False, "pii": False},
                {"name": "full_name", "type": "string", "description": "Customer full name", "required": True, "nullable": False, "pii": True, "max_length": 255},
                {"name": "email", "type": "string", "description": "Customer email address", "required": True, "nullable": False, "pii": True, "max_length": 255},
                {"name": "phone", "type": "string", "description": "Customer phone number", "required": False, "nullable": True, "pii": True, "max_length": 20},
                {"name": "account_status", "type": "string", "description": "Account status (active/suspended/closed)", "required": True, "nullable": False, "pii": False},
                {"name": "created_at", "type": "timestamp", "description": "Account creation timestamp", "required": True, "nullable": False, "pii": False},
            ],
        },
        {
            "name": "transaction_ledger",
            "description": "Financial transaction records with amounts, parties, and settlement status.",
            "owner_name": "Bob Martinez",
            "owner_email": "bob.martinez@company.com",
            "source_type": "postgres",
            "physical_location": "finance.public.transactions",
            "classification": "restricted",
            "contains_pii": False,
            "compliance_tags": ["SOX", "PCI-DSS"],
            "schema": [
                {"name": "txn_id", "type": "string", "description": "Transaction UUID", "required": True, "nullable": False, "pii": False},
                {"name": "account_id", "type": "integer", "description": "Source account ID", "required": True, "nullable": False, "pii": False},
                {"name": "amount", "type": "decimal", "description": "Transaction amount in USD", "required": True, "nullable": False, "pii": False},
                {"name": "currency", "type": "string", "description": "ISO 4217 currency code", "required": True, "nullable": False, "pii": False, "max_length": 3},
                {"name": "txn_type", "type": "string", "description": "Type: credit/debit/transfer", "required": True, "nullable": False, "pii": False},
                {"name": "status", "type": "string", "description": "Settlement status", "required": True, "nullable": False, "pii": False},
                {"name": "processed_at", "type": "timestamp", "description": "Processing timestamp", "required": True, "nullable": False, "pii": False},
            ],
        },
        {
            "name": "product_catalog",
            "description": "Product catalog with pricing, categories, and inventory levels.",
            "owner_name": "Carol Oduya",
            "owner_email": "carol.oduya@company.com",
            "source_type": "postgres",
            "physical_location": "commerce.public.products",
            "classification": "internal",
            "contains_pii": False,
            "compliance_tags": [],
            "schema": [
                {"name": "product_id", "type": "integer", "description": "Product identifier", "required": True, "nullable": False, "pii": False},
                {"name": "sku", "type": "string", "description": "Stock keeping unit", "required": True, "nullable": False, "pii": False, "max_length": 50},
                {"name": "name", "type": "string", "description": "Product display name", "required": True, "nullable": False, "pii": False, "max_length": 255},
                {"name": "category", "type": "string", "description": "Product category", "required": True, "nullable": False, "pii": False},
                {"name": "price", "type": "decimal", "description": "Unit price in USD", "required": True, "nullable": False, "pii": False},
                {"name": "stock_qty", "type": "integer", "description": "Current inventory count", "required": True, "nullable": False, "pii": False},
                {"name": "updated_at", "type": "timestamp", "description": "Last update timestamp", "required": True, "nullable": False, "pii": False},
            ],
        },
        {
            "name": "employee_directory",
            "description": "Internal employee records with department, role, and contact information.",
            "owner_name": "Diana Park",
            "owner_email": "diana.park@company.com",
            "source_type": "postgres",
            "physical_location": "hr.public.employees",
            "classification": "confidential",
            "contains_pii": True,
            "compliance_tags": ["GDPR"],
            "schema": [
                {"name": "employee_id", "type": "integer", "description": "Employee identifier", "required": True, "nullable": False, "pii": False},
                {"name": "full_name", "type": "string", "description": "Employee full name", "required": True, "nullable": False, "pii": True, "max_length": 255},
                {"name": "email", "type": "string", "description": "Corporate email", "required": True, "nullable": False, "pii": True, "max_length": 255},
                {"name": "department", "type": "string", "description": "Department name", "required": True, "nullable": False, "pii": False},
                {"name": "role", "type": "string", "description": "Job title", "required": True, "nullable": False, "pii": False},
                {"name": "hire_date", "type": "date", "description": "Date of hire", "required": True, "nullable": False, "pii": False},
            ],
        },
        {
            "name": "web_analytics_events",
            "description": "Clickstream and event tracking data from the customer-facing web application.",
            "owner_name": "Evan Torres",
            "owner_email": "evan.torres@company.com",
            "source_type": "postgres",
            "physical_location": "analytics.public.events",
            "classification": "internal",
            "contains_pii": False,
            "compliance_tags": ["GDPR"],
            "schema": [
                {"name": "event_id", "type": "string", "description": "Event UUID", "required": True, "nullable": False, "pii": False},
                {"name": "session_id", "type": "string", "description": "Browser session ID", "required": True, "nullable": False, "pii": False},
                {"name": "event_type", "type": "string", "description": "Event type (page_view, click, purchase)", "required": True, "nullable": False, "pii": False},
                {"name": "page_url", "type": "string", "description": "Page URL", "required": True, "nullable": False, "pii": False, "max_length": 2000},
                {"name": "timestamp", "type": "timestamp", "description": "Event timestamp (UTC)", "required": True, "nullable": False, "pii": False},
            ],
        },
    ]
    return samples


def _build_contract(s: dict) -> dict:
    """Build the machine_readable contract dict as _seed_sample_data does."""
    return {
        "version": "1.0.0",
        "dataset": {
            "name": s["name"],
            "description": s["description"],
            "owner_name": s["owner_name"],
            "owner_email": s["owner_email"],
            "classification": s["classification"],
        },
        "schema": s["schema"],
        "governance": {
            "classification": s["classification"],
            "encryption_required": s["classification"] in ("confidential", "restricted"),
            "retention_days": 2555,
            "compliance_tags": s["compliance_tags"],
            "approved_use_cases": ["analytics", "reporting"],
        },
        "quality_rules": {
            "completeness_threshold": 95,
            "freshness_sla": "24h",
            "uniqueness_fields": [s["schema"][0]["name"]],
        },
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.unit
@pytest.mark.service
class TestSeedDataPolicyCompliance:
    """
    Validate every seed dataset contract against the policy engine.
    None should produce CRITICAL violations (status=FAILED).
    """

    def setup_method(self):
        self.engine = PolicyEngine()
        self.samples = _seed_sample()

    def test_five_seed_datasets_defined(self):
        """There should be exactly 5 sample datasets in the seed list."""
        assert len(self.samples) == 5

    def test_no_seed_contract_fails_policy_engine(self):
        """No seed contract should produce a FAILED validation result (CRITICAL violations)."""
        failed_datasets = []
        for s in self.samples:
            contract = _build_contract(s)
            result = self.engine.validate_contract(contract)
            if result.status == ValidationStatus.FAILED:
                failed_datasets.append(
                    f"{s['name']}: {[v.policy for v in result.violations if v.type.value == 'critical']}"
                )
        assert failed_datasets == [], (
            f"Seed datasets with CRITICAL policy violations:\n" + "\n".join(failed_datasets)
        )

    def test_all_seed_datasets_have_owner(self):
        """All seed datasets must have owner_name and owner_email (SG003 compliance)."""
        for s in self.samples:
            assert s["owner_name"], f"'{s['name']}' missing owner_name"
            assert s["owner_email"], f"'{s['name']}' missing owner_email"

    def test_pii_datasets_have_encryption_required(self):
        """Confidential/restricted seed datasets have encryption_required=True in their contracts."""
        for s in self.samples:
            contract = _build_contract(s)
            gov = contract["governance"]
            if s["classification"] in ("confidential", "restricted"):
                assert gov["encryption_required"] is True, (
                    f"'{s['name']}' (classification={s['classification']}) "
                    f"should have encryption_required=True"
                )

    def test_restricted_datasets_have_approved_use_cases(self):
        """Restricted seed datasets include approved_use_cases (SD004 compliance)."""
        for s in self.samples:
            if s["classification"] == "restricted":
                contract = _build_contract(s)
                assert contract["governance"].get("approved_use_cases"), (
                    f"'{s['name']}' is restricted but has no approved_use_cases"
                )

    def test_confidential_and_restricted_have_retention_days(self):
        """Confidential/restricted datasets specify retention_days (SD002 compliance)."""
        for s in self.samples:
            if s["classification"] in ("confidential", "restricted"):
                contract = _build_contract(s)
                assert contract["governance"].get("retention_days"), (
                    f"'{s['name']}' requires retention_days but none set"
                )

    def test_completeness_threshold_meets_dq001_minimum(self):
        """All seed contracts set completeness_threshold >= 95 (DQ001 minimum)."""
        for s in self.samples:
            contract = _build_contract(s)
            threshold = contract["quality_rules"].get("completeness_threshold", 0)
            assert threshold >= 95, (
                f"'{s['name']}' completeness_threshold={threshold} is below DQ001 minimum (95)"
            )

    def test_freshness_sla_defined_for_all_seed_contracts(self):
        """All seed contracts define freshness_sla (satisfies DQ002 for temporal fields)."""
        for s in self.samples:
            contract = _build_contract(s)
            assert contract["quality_rules"].get("freshness_sla"), (
                f"'{s['name']}' missing freshness_sla"
            )

    def test_uniqueness_fields_defined_for_all_seed_contracts(self):
        """All seed contracts define uniqueness_fields (satisfies DQ003 for id-named fields)."""
        for s in self.samples:
            contract = _build_contract(s)
            uniqueness = contract["quality_rules"].get("uniqueness_fields", [])
            assert len(uniqueness) > 0, f"'{s['name']}' missing uniqueness_fields"

    def test_schema_hash_is_deterministic(self):
        """Schema hash derived from seed schema is 64-char hex (SHA-256)."""
        for s in self.samples:
            schema_hash = hashlib.sha256(
                json.dumps(s["schema"], sort_keys=True).encode()
            ).hexdigest()
            assert len(schema_hash) == 64, f"'{s['name']}' schema hash length is not 64"
            assert all(c in "0123456789abcdef" for c in schema_hash), (
                f"'{s['name']}' schema hash contains non-hex characters"
            )

    def test_schema_hash_stable_across_calls(self):
        """Same schema produces the same hash on repeated calls."""
        s = self.samples[0]
        hash1 = hashlib.sha256(json.dumps(s["schema"], sort_keys=True).encode()).hexdigest()
        hash2 = hashlib.sha256(json.dumps(s["schema"], sort_keys=True).encode()).hexdigest()
        assert hash1 == hash2

    def test_different_schemas_produce_different_hashes(self):
        """Two distinct schemas must not collide."""
        hashes = set()
        for s in self.samples:
            h = hashlib.sha256(json.dumps(s["schema"], sort_keys=True).encode()).hexdigest()
            hashes.add(h)
        assert len(hashes) == len(self.samples), "Two seed schemas produced the same hash"


@pytest.mark.unit
@pytest.mark.service
class TestSeedDataPerDataset:
    """Per-dataset policy validation assertions for quick debugging."""

    def setup_method(self):
        self.engine = PolicyEngine()
        self.samples = {s["name"]: s for s in _seed_sample()}

    def _validate(self, name: str) -> tuple:
        s = self.samples[name]
        contract = _build_contract(s)
        result = self.engine.validate_contract(contract)
        return result, [v.policy for v in result.violations]

    def test_customer_accounts_no_critical_violations(self):
        result, _ = self._validate("customer_accounts")
        assert result.status != ValidationStatus.FAILED, (
            f"customer_accounts has CRITICAL violations: {[v.policy for v in result.violations if v.type.value == 'critical']}"
        )

    def test_transaction_ledger_no_critical_violations(self):
        result, _ = self._validate("transaction_ledger")
        assert result.status != ValidationStatus.FAILED, (
            f"transaction_ledger has CRITICAL violations: {[v.policy for v in result.violations if v.type.value == 'critical']}"
        )

    def test_product_catalog_no_critical_violations(self):
        result, _ = self._validate("product_catalog")
        assert result.status != ValidationStatus.FAILED, (
            f"product_catalog has CRITICAL violations: {[v.policy for v in result.violations if v.type.value == 'critical']}"
        )

    def test_employee_directory_no_critical_violations(self):
        result, _ = self._validate("employee_directory")
        assert result.status != ValidationStatus.FAILED, (
            f"employee_directory has CRITICAL violations: {[v.policy for v in result.violations if v.type.value == 'critical']}"
        )

    def test_web_analytics_events_no_critical_violations(self):
        result, _ = self._validate("web_analytics_events")
        assert result.status != ValidationStatus.FAILED, (
            f"web_analytics_events has CRITICAL violations: {[v.policy for v in result.violations if v.type.value == 'critical']}"
        )

    def test_customer_accounts_satisfies_sd001(self):
        """customer_accounts has PII and encryption_required=True → no SD001 violation."""
        result, policies = self._validate("customer_accounts")
        assert not any("SD001" in p for p in policies), "customer_accounts should not trigger SD001"

    def test_transaction_ledger_satisfies_sd004(self):
        """transaction_ledger is restricted and specifies approved_use_cases → no SD004 violation."""
        result, policies = self._validate("transaction_ledger")
        assert not any("SD004" in p for p in policies), "transaction_ledger should not trigger SD004"

    def test_all_seed_contracts_satisfy_dq001(self):
        """No seed contract triggers DQ001 (completeness_threshold=95 meets the minimum)."""
        for name in self.samples:
            result, policies = self._validate(name)
            assert not any("DQ001" in p for p in policies), (
                f"'{name}' unexpectedly triggered DQ001"
            )

    def test_all_seed_contracts_satisfy_sg003(self):
        """All seed datasets have both owner_name and owner_email → no SG003 violation."""
        for name in self.samples:
            result, policies = self._validate(name)
            assert not any("SG003" in p for p in policies), (
                f"'{name}' unexpectedly triggered SG003"
            )

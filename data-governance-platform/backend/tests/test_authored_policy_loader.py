"""
Unit tests for authored_policy_loader service.
"""
import pytest
from unittest.mock import patch, Mock
from datetime import date

from app.services.authored_policy_loader import (
    load_authored_policies,
    validate_contract_with_authored_policies,
    _check_rule_heuristic,
    get_combined_validation,
)
from app.models.policy_draft import PolicyDraft
from app.models.policy_artifact import PolicyArtifact
from app.schemas.contract import ViolationType, ValidationStatus


@pytest.fixture
def seed_approved_policy(db):
    """Seed an approved policy with artifact."""
    draft = PolicyDraft(
        policy_uid="POL-001",
        title="Encryption Required for PII",
        description="All PII must be encrypted",
        policy_category="security",
        affected_domains=["ALL"],
        severity="CRITICAL",
        scanner_hint="rule_based",
        remediation_guide="Enable encryption",
        status="approved",
        version=1,
        authored_by="Test Author",
    )
    db.add(draft)
    db.flush()

    artifact = PolicyArtifact(
        policy_id=draft.id,
        version=1,
        yaml_content="""policies:
  - id: AUTH001
    name: encryption_required
    severity: critical
    rule: "IF schema contains PII fields THEN encryption must be enabled"
    remediation: "Enable AES-256 encryption"
""",
        json_content="{}",
        scanner_type="rule_based",
    )
    db.add(artifact)
    db.commit()
    return draft


@pytest.fixture
def seed_domain_policy(db):
    """Seed an approved policy with domain filter."""
    draft = PolicyDraft(
        policy_uid="POL-002",
        title="Finance Retention Policy",
        description="Finance data needs retention",
        policy_category="compliance",
        affected_domains=["finance"],
        severity="WARNING",
        scanner_hint="rule_based",
        remediation_guide="Set retention days",
        status="approved",
        version=1,
        authored_by="Test Author",
    )
    db.add(draft)
    db.flush()

    artifact = PolicyArtifact(
        policy_id=draft.id,
        version=1,
        yaml_content="""policies:
  - id: AUTH002
    name: retention_required
    severity: warning
    rule: "IF classification is confidential THEN retention must be set"
    remediation: "Set retention_days to 2555"
""",
        json_content="{}",
        scanner_type="rule_based",
    )
    db.add(artifact)
    db.commit()
    return draft


@pytest.mark.unit
@pytest.mark.service
class TestLoadAuthoredPolicies:
    """Test load_authored_policies function."""

    def test_load_no_approved_policies(self, db):
        """Test loading when no approved policies exist."""
        result = load_authored_policies(db)
        assert result == []

    def test_load_approved_policies_no_filter(self, db, seed_approved_policy):
        """Test loading all approved policies without domain filter."""
        result = load_authored_policies(db)
        assert len(result) == 1
        assert result[0]["policy_uid"] == "POL-001"
        assert result[0]["scanner_type"] == "rule_based"

    def test_load_approved_policies_domain_filter(self, db, seed_approved_policy, seed_domain_policy):
        """Test loading policies filtered by domain."""
        result = load_authored_policies(db, domain="finance")
        # Should include POL-001 (ALL) and POL-002 (finance)
        uids = [p["policy_uid"] for p in result]
        assert "POL-001" in uids
        assert "POL-002" in uids

    def test_load_approved_policies_domain_filter_excludes(self, db, seed_domain_policy):
        """Test domain filter excludes non-matching policies."""
        result = load_authored_policies(db, domain="healthcare")
        # POL-002 is finance-only, should not appear for healthcare
        assert len(result) == 0

    def test_load_approved_policies_domain_all_matches(self, db, seed_approved_policy):
        """Test that 'ALL' domain matches any filter."""
        result = load_authored_policies(db, domain="random_domain")
        assert len(result) == 1  # POL-001 has affected_domains=["ALL"]

    def test_load_approved_skips_no_artifact(self, db):
        """Test that policies without artifacts are skipped."""
        draft = PolicyDraft(
            policy_uid="POL-NOART",
            title="No Artifact Policy",
            description="This has no artifact",
            policy_category="security",
            affected_domains=["ALL"],
            severity="WARNING",
            scanner_hint="rule_based",
            status="approved",
            version=1,
            authored_by="Test",
        )
        db.add(draft)
        db.commit()

        result = load_authored_policies(db)
        assert len(result) == 0

    def test_load_approved_skips_bad_yaml(self, db):
        """Test that policies with malformed YAML are skipped."""
        draft = PolicyDraft(
            policy_uid="POL-BADYML",
            title="Bad YAML Policy",
            description="Has invalid YAML",
            policy_category="security",
            affected_domains=["ALL"],
            severity="WARNING",
            scanner_hint="rule_based",
            status="approved",
            version=1,
            authored_by="Test",
        )
        db.add(draft)
        db.flush()

        artifact = PolicyArtifact(
            policy_id=draft.id,
            version=1,
            yaml_content="invalid: yaml: [[[",
            json_content="{}",
            scanner_type="rule_based",
        )
        db.add(artifact)
        db.commit()

        result = load_authored_policies(db)
        # Should still work but skip the bad one
        assert isinstance(result, list)


@pytest.mark.unit
@pytest.mark.service
class TestCheckRuleHeuristic:
    """Test _check_rule_heuristic function."""

    def test_heuristic_encryption_violation(self):
        """Test encryption heuristic detects missing encryption for PII."""
        result = _check_rule_heuristic(
            rule_text="if schema contains pii fields then encryption must be enabled",
            governance={"encryption_required": False},
            schema=[{"name": "email", "pii": True}],
            quality_rules={},
            dataset={},
        )
        assert result is not None
        assert result["field"] == "governance.encryption_required"

    def test_heuristic_encryption_no_violation(self):
        """Test encryption heuristic passes when encryption is enabled."""
        result = _check_rule_heuristic(
            rule_text="if schema contains pii fields then encryption must be enabled",
            governance={"encryption_required": True},
            schema=[{"name": "email", "pii": True}],
            quality_rules={},
            dataset={},
        )
        assert result is None

    def test_heuristic_retention_violation(self):
        """Test retention heuristic detects missing retention for confidential data."""
        result = _check_rule_heuristic(
            rule_text="if classification is confidential then retention must be set",
            governance={"classification": "confidential"},
            schema=[],
            quality_rules={},
            dataset={},
        )
        assert result is not None
        assert result["field"] == "governance.retention_days"

    def test_heuristic_completeness_95_violation(self):
        """Test completeness heuristic detects threshold below 95%."""
        result = _check_rule_heuristic(
            rule_text="completeness threshold must be at least 95 percent",
            governance={},
            schema=[],
            quality_rules={"completeness_threshold": 90},
            dataset={},
        )
        assert result is not None
        assert "95%" in result["message"]

    def test_heuristic_completeness_90_violation(self):
        """Test completeness heuristic detects threshold below 90%."""
        result = _check_rule_heuristic(
            rule_text="completeness threshold must meet minimum requirements",
            governance={},
            schema=[],
            quality_rules={"completeness_threshold": 80},
            dataset={},
        )
        assert result is not None
        assert "below minimum" in result["message"]

    def test_heuristic_freshness_violation(self):
        """Test freshness heuristic detects missing SLA for temporal data."""
        result = _check_rule_heuristic(
            rule_text="temporal datasets must define freshness sla",
            governance={},
            schema=[{"name": "created_at", "type": "timestamp"}],
            quality_rules={},
            dataset={},
        )
        assert result is not None
        assert "freshness SLA" in result["message"]

    def test_heuristic_compliance_tags_violation(self):
        """Test compliance tag heuristic for PII without tags."""
        result = _check_rule_heuristic(
            rule_text="pii dataset requires compliance framework tags",
            governance={},
            schema=[{"name": "ssn", "pii": True}],
            quality_rules={},
            dataset={},
        )
        assert result is not None
        assert "compliance" in result["message"].lower()

    def test_heuristic_owner_missing_violation(self):
        """Test owner heuristic detects missing owner info."""
        result = _check_rule_heuristic(
            rule_text="dataset must have an owner defined",
            governance={},
            schema=[],
            quality_rules={},
            dataset={},
        )
        assert result is not None
        assert "owner_name" in result["field"]

    def test_heuristic_description_missing_violation(self):
        """Test description heuristic detects fields without descriptions."""
        result = _check_rule_heuristic(
            rule_text="all fields must have a description",
            governance={},
            schema=[
                {"name": "id"},
                {"name": "name", "description": "Full name"},
            ],
            quality_rules={},
            dataset={},
        )
        assert result is not None
        assert "id" in result["field"]

    def test_heuristic_no_match(self):
        """Test heuristic returns None for unmatched rule text."""
        result = _check_rule_heuristic(
            rule_text="some completely unrelated rule about cosmic alignment",
            governance={"classification": "public"},
            schema=[],
            quality_rules={},
            dataset={"owner_name": "Test", "owner_email": "test@test.com"},
        )
        assert result is None


@pytest.mark.unit
@pytest.mark.service
class TestValidateContractWithAuthored:
    """Test validate_contract_with_authored_policies."""

    def test_validate_with_authored_semantic_skipped(self):
        """Test that ai_semantic scanner type doesn't produce violations."""
        authored = [{
            "parsed_yaml": {
                "policies": [{
                    "id": "SEM_AUTH",
                    "name": "semantic_check",
                    "severity": "WARNING",
                    "rule": "check something semantically",
                    "remediation": "fix it"
                }]
            },
            "scanner_type": "ai_semantic",
            "title": "Semantic Policy"
        }]
        contract_data = {"governance": {}, "schema": [], "quality_rules": {}, "dataset": {}}

        violations = validate_contract_with_authored_policies(contract_data, authored)
        assert len(violations) == 0

    def test_validate_with_authored_rule_based(self, db, seed_approved_policy):
        """Test that rule_based authored policies produce violations."""
        authored = load_authored_policies(db)
        contract_data = {
            "governance": {"encryption_required": False},
            "schema": [{"name": "email", "pii": True}],
            "quality_rules": {},
            "dataset": {},
        }

        violations = validate_contract_with_authored_policies(contract_data, authored)
        assert len(violations) > 0
        assert violations[0].type == ViolationType.CRITICAL


@pytest.mark.unit
@pytest.mark.service
class TestGetCombinedValidation:
    """Test get_combined_validation function."""

    def test_combined_validation_no_authored(self, db):
        """Test combined validation when no authored policies exist."""
        contract_data = {
            "dataset": {"name": "test", "owner_name": "Owner", "owner_email": "o@e.com"},
            "schema": [{"name": "id", "type": "integer", "description": "ID", "pii": False}],
            "governance": {"classification": "public"},
            "quality_rules": {"uniqueness_fields": ["id"]},
        }

        result = get_combined_validation(contract_data, db)
        assert result.status in [ValidationStatus.PASSED, ValidationStatus.WARNING]

    def test_combined_validation_with_authored(self, db, seed_approved_policy):
        """Test combined validation includes authored policy violations."""
        contract_data = {
            "dataset": {"name": "test", "owner_name": "Owner", "owner_email": "o@e.com"},
            "schema": [
                {"name": "email", "type": "string", "description": "Email", "pii": True}
            ],
            "governance": {
                "classification": "confidential",
                "encryption_required": False,
            },
            "quality_rules": {"completeness_threshold": 80},
        }

        result = get_combined_validation(contract_data, db)
        # Should have violations from both YAML policies and authored policies
        assert result.status == ValidationStatus.FAILED
        assert len(result.violations) > 0

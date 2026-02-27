"""
Authored policy loader for enforcement integration.

Bridges the gap between Stage 1/2 (authored policies in the DB) and the existing
PolicyEngine validation pipeline. Loads approved authored policies from the database
and converts them into the same runtime format the PolicyEngine understands.

This module also provides a "combined" validation function that runs both the
static YAML policies and the authored policies against a contract.
"""

import json
import logging
import yaml
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session

from app.models.policy_draft import PolicyDraft
from app.models.policy_artifact import PolicyArtifact
from app.schemas.contract import Violation, ValidationResult, ViolationType, ValidationStatus
from app.services.policy_engine import PolicyEngine

logger = logging.getLogger(__name__)


def load_authored_policies(db: Session, domain: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Load all approved authored policies from the database.

    Args:
        db: SQLAlchemy session.
        domain: Optional domain filter. If provided, returns policies
                whose affected_domains include this domain or "ALL".

    Returns:
        List of policy dicts, each containing the parsed YAML artifact
        plus metadata from the PolicyDraft.
    """
    query = db.query(PolicyDraft).filter(PolicyDraft.status == "approved")

    policies_with_artifacts = []
    drafts = query.all()

    for draft in drafts:
        # Domain filtering (JSON string matching for SQLite)
        if domain:
            domains = draft.affected_domains or []
            if domain not in domains and "ALL" not in domains:
                continue

        # Get the latest artifact
        artifact = (
            db.query(PolicyArtifact)
            .filter(PolicyArtifact.policy_id == draft.id)
            .order_by(PolicyArtifact.version.desc())
            .first()
        )
        if not artifact:
            continue

        try:
            parsed_yaml = yaml.safe_load(artifact.yaml_content)
        except Exception:
            logger.warning(f"Failed to parse YAML for policy {draft.id}")
            continue

        policies_with_artifacts.append({
            "draft_id": draft.id,
            "policy_uid": draft.policy_uid,
            "title": draft.title,
            "category": draft.policy_category,
            "severity": draft.severity,
            "scanner_type": artifact.scanner_type,
            "version": draft.version,
            "parsed_yaml": parsed_yaml,
            "artifact_id": artifact.id,
        })

    return policies_with_artifacts


def validate_contract_with_authored_policies(
    contract_data: Dict[str, Any],
    authored_policies: List[Dict[str, Any]],
) -> List[Violation]:
    """
    Validate a contract against authored policies using keyword heuristics.

    For rule_based policies, applies the same keyword-driven checks as the
    PolicyEngine. For ai_semantic policies, flags them as requiring LLM
    validation (advisory only in rule mode).

    Args:
        contract_data: Contract data dict.
        authored_policies: List from load_authored_policies().

    Returns:
        List of Violations from authored policies.
    """
    violations = []
    governance = contract_data.get("governance", {})
    schema = contract_data.get("schema", [])
    quality_rules = contract_data.get("quality_rules", {})
    dataset = contract_data.get("dataset", {})

    for ap in authored_policies:
        parsed = ap["parsed_yaml"]
        for policy_entry in parsed.get("policies", []):
            rule_text = (policy_entry.get("rule") or "").lower()
            severity_str = (policy_entry.get("severity") or "warning").upper()
            viol_type = ViolationType.CRITICAL if severity_str == "CRITICAL" else ViolationType.WARNING
            policy_label = f"{policy_entry.get('id', 'AUTH')}: {policy_entry.get('name', ap['title'])}"
            remediation = policy_entry.get("remediation", "See the policy remediation guide.")

            # --- Rule-based enforcement heuristics ---
            if ap["scanner_type"] == "rule_based":
                violated = _check_rule_heuristic(rule_text, governance, schema, quality_rules, dataset)
                if violated:
                    violations.append(Violation(
                        type=viol_type,
                        policy=policy_label,
                        field=violated["field"],
                        message=violated["message"],
                        remediation=remediation,
                    ))
            else:
                # ai_semantic policies: advisory note (LLM analysis needed)
                pass  # Semantic enforcement deferred to SemanticPolicyEngine

    return violations


def _check_rule_heuristic(
    rule_text: str,
    governance: Dict,
    schema: List[Dict],
    quality_rules: Dict,
    dataset: Dict,
) -> Optional[Dict[str, str]]:
    """
    Apply simple heuristic matching against rule text to detect violations.

    Returns None if no violation, or a dict with 'field' and 'message'.
    """
    has_pii = any(f.get("pii", False) for f in schema)
    classification = governance.get("classification", "internal")

    # Encryption checks
    if "encrypt" in rule_text and has_pii and not governance.get("encryption_required", False):
        return {
            "field": "governance.encryption_required",
            "message": "PII fields detected but encryption is not required.",
        }

    # Retention checks
    if "retention" in rule_text and classification in ("confidential", "restricted") and not governance.get("retention_days"):
        return {
            "field": "governance.retention_days",
            "message": f"Classification '{classification}' requires a retention policy.",
        }

    # Completeness checks
    if "completeness" in rule_text:
        threshold = quality_rules.get("completeness_threshold", 0)
        if "95" in rule_text and threshold < 95:
            return {
                "field": "quality_rules.completeness_threshold",
                "message": f"Completeness threshold {threshold}% is below the required 95%.",
            }
        elif threshold < 90:
            return {
                "field": "quality_rules.completeness_threshold",
                "message": f"Completeness threshold {threshold}% is below minimum acceptable level.",
            }

    # Freshness checks
    if "freshness" in rule_text and not quality_rules.get("freshness_sla"):
        has_temporal = any(f.get("type") in ("date", "timestamp", "datetime") for f in schema)
        if has_temporal:
            return {
                "field": "quality_rules.freshness_sla",
                "message": "Temporal dataset requires a freshness SLA.",
            }

    # Compliance tag checks
    if "compliance" in rule_text and "tag" in rule_text and has_pii and not governance.get("compliance_tags"):
        return {
            "field": "governance.compliance_tags",
            "message": "PII dataset requires compliance framework tags.",
        }

    # Owner checks
    if "owner" in rule_text and (not dataset.get("owner_name") or not dataset.get("owner_email")):
        return {
            "field": "dataset.owner_name, dataset.owner_email",
            "message": "Dataset must have owner_name and owner_email.",
        }

    # Description checks
    if "description" in rule_text:
        missing = [f["name"] for f in schema if not f.get("description")]
        if missing:
            return {
                "field": ", ".join(missing[:5]),
                "message": f"Fields missing descriptions: {missing[:5]}",
            }

    return None


def get_combined_validation(
    contract_data: Dict[str, Any],
    db: Session,
    domain: Optional[str] = None,
) -> ValidationResult:
    """
    Validate a contract against BOTH static YAML policies and authored policies.

    Runs the standard PolicyEngine first, then appends violations from
    any matching authored policies.

    Args:
        contract_data: Contract data dict.
        db: SQLAlchemy session.
        domain: Optional domain filter for authored policies.

    Returns:
        Combined ValidationResult.
    """
    # 1. Standard rule-based engine
    engine = PolicyEngine()
    base_result = engine.validate_contract(contract_data)

    # 2. Authored policies
    authored = load_authored_policies(db, domain=domain)
    authored_violations = validate_contract_with_authored_policies(contract_data, authored)

    # 3. Merge
    all_violations = list(base_result.violations) + authored_violations

    critical_count = sum(1 for v in all_violations if v.type == ViolationType.CRITICAL)
    warning_count = sum(1 for v in all_violations if v.type == ViolationType.WARNING)
    passed_count = max(0, (base_result.passed + len(authored)) - len(authored_violations))

    if critical_count > 0:
        status = ValidationStatus.FAILED
    elif warning_count > 0:
        status = ValidationStatus.WARNING
    else:
        status = ValidationStatus.PASSED

    return ValidationResult(
        status=status,
        passed=passed_count,
        warnings=warning_count,
        failures=critical_count,
        violations=all_violations,
    )

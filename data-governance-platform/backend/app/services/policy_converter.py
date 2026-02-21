"""
Policy conversion engine.

Transforms an approved PolicyDraft into structured YAML and JSON artifacts
that follow the same format as existing hand-written policy files
(e.g. sensitive_data_policies.yaml, data_quality_policies.yaml).

The converter:
  1. Generates a deterministic policy ID from the category and a sequence counter.
  2. Builds a rule DSL expression from the plain-English description using
     keyword heuristics, or falls back to the description itself for semantic
     policies that need LLM evaluation.
  3. Emits YAML and JSON representations matching the existing policy schema.
  4. Resolves the scanner_hint (auto → rule_based or ai_semantic).
"""

import json
import re
from datetime import date
from typing import Dict, Any, Optional, Tuple

import yaml

# Keyword patterns that suggest a rule can be expressed deterministically.
_RULE_KEYWORDS = [
    (r"\bencrypt", "governance.encryption_required must be true"),
    (r"\bretention", "governance.retention_days must be specified"),
    (r"\bcompleteness", "quality_rules.completeness_threshold"),
    (r"\bfreshness", "quality_rules.freshness_sla must be specified"),
    (r"\buniqueness|unique", "quality_rules.uniqueness_fields must be specified"),
    (r"\bcompliance\s*tag", "governance.compliance_tags should not be empty"),
    (r"\bowner", "dataset.owner_name and dataset.owner_email must be specified"),
    (r"\bdescription", "schema fields must have descriptions"),
    (r"\bmax.?length", "string fields must specify max_length"),
    (r"\bnullable.*required|required.*nullable", "required fields must not be nullable"),
    (r"\bpii", "schema fields with pii=true"),
    (r"\baccuracy", "quality_rules.accuracy_threshold"),
    (r"\bresidency", "governance.data_residency must be specified"),
    (r"\buse.?case", "governance.approved_use_cases must be specified"),
]

# Category → ID prefix mapping (matches existing convention)
_CATEGORY_PREFIX = {
    "data_quality": "DQ",
    "security": "SD",
    "privacy": "SD",
    "compliance": "SD",
    "lineage": "LN",
    "sla": "SLA",
}


def _generate_policy_id(category: str, uid_suffix: str) -> str:
    """Generate a short policy ID like DQ006 or SD006."""
    prefix = _CATEGORY_PREFIX.get(category, "POL")
    # Use last 3 hex chars of uid to get a numeric suffix
    num = int(uid_suffix[-3:], 16) % 900 + 100  # 100-999
    return f"{prefix}{num}"


def _name_from_title(title: str) -> str:
    """Convert human title to snake_case policy name."""
    name = re.sub(r"[^a-zA-Z0-9\s]", "", title)
    name = re.sub(r"\s+", "_", name.strip()).lower()
    return name[:60]


def _build_rule_expression(description: str) -> Tuple[str, bool]:
    """
    Try to build a deterministic rule expression from the description.

    Returns (rule_text, is_deterministic).
    If the description doesn't match keyword patterns, returns the
    description as-is with is_deterministic=False.
    """
    desc_lower = description.lower()
    conditions = []
    actions = []

    for pattern, template in _RULE_KEYWORDS:
        if re.search(pattern, desc_lower):
            conditions.append(f"Matches pattern: {template}")

    if conditions:
        # Build a pseudo-DSL rule from the description
        rule = _description_to_rule_dsl(description)
        return rule, True

    # Fallback — the description itself becomes the rule for semantic scanning
    return description.strip(), False


def _description_to_rule_dsl(description: str) -> str:
    """
    Convert a plain-English description to an IF/THEN rule DSL.

    This uses simple heuristics to identify conditions and requirements
    in the text and renders them in the same style as existing policy YAML.
    """
    desc_lower = description.lower()
    parts = []

    # Detect conditional patterns
    if_match = re.search(r"(?:if|when|where|for)\s+(.+?)(?:,|\bthen\b|must|should|require)", desc_lower)
    then_match = re.search(r"(?:must|should|require|then)\s+(.+?)(?:\.|$)", desc_lower)

    if if_match and then_match:
        condition = if_match.group(1).strip()
        action = then_match.group(1).strip()
        return f"IF {condition}\nTHEN {action}"

    # Fallback: wrap the description as a single rule statement
    # Remove trailing period for cleaner YAML
    desc = description.strip().rstrip(".")
    return desc


def _resolve_scanner(scanner_hint: str, is_deterministic: bool) -> str:
    """Resolve 'auto' scanner hint based on rule determinism."""
    if scanner_hint == "auto":
        return "rule_based" if is_deterministic else "ai_semantic"
    return scanner_hint


def convert_policy_to_yaml(
    policy_uid: str,
    title: str,
    description: str,
    policy_category: str,
    affected_domains: list,
    severity: str,
    scanner_hint: str,
    remediation_guide: str,
    effective_date: Optional[date],
    authored_by: str,
    version: int,
) -> Dict[str, Any]:
    """
    Convert a PolicyDraft's fields into YAML and JSON strings.

    Returns a dict with:
      - yaml_content: str
      - json_content: str
      - scanner_type: resolved scanner type
      - policy_id: generated short ID
    """
    policy_id = _generate_policy_id(policy_category, policy_uid)
    policy_name = _name_from_title(title)
    rule_text, is_deterministic = _build_rule_expression(description)
    scanner_type = _resolve_scanner(scanner_hint, is_deterministic)

    # Build the structured policy dict (matches existing YAML format)
    policy_entry = {
        "id": policy_id,
        "name": policy_name,
        "severity": severity.lower(),
        "description": description,
        "rule": rule_text,
        "remediation": remediation_guide or "",
    }

    # Top-level YAML document (matches existing files)
    yaml_doc = {
        "name": f"authored_policy_{policy_name}",
        "version": f"{version}.0.0",
        "description": f"Auto-generated policy: {title}",
        "metadata": {
            "policy_uid": policy_uid,
            "authored_by": authored_by,
            "category": policy_category,
            "affected_domains": affected_domains,
            "scanner_type": scanner_type,
        },
        "policies": [policy_entry],
    }

    if effective_date:
        yaml_doc["metadata"]["effective_date"] = effective_date.isoformat()

    # If the scanner is semantic, add a prompt_template
    if scanner_type == "ai_semantic":
        policy_entry["prompt_template"] = (
            f"Analyze the following data contract for compliance with this policy:\n\n"
            f"Policy: {title}\n"
            f"Rule: {description}\n\n"
            f"Contract data:\n"
            f"  Dataset: {{dataset_name}}\n"
            f"  Classification: {{classification}}\n"
            f"  Fields: {{fields_summary}}\n\n"
            f"Respond with JSON:\n"
            f'{{"compliant": true/false, "confidence": 0-100, "issues": [...], "reasoning": "..."}}'
        )

    yaml_content = yaml.dump(yaml_doc, default_flow_style=False, sort_keys=False, allow_unicode=True)

    # JSON is the same structure, just in JSON format
    json_content = json.dumps(yaml_doc, indent=2, default=str)

    return {
        "yaml_content": yaml_content,
        "json_content": json_content,
        "scanner_type": scanner_type,
        "policy_id": policy_id,
    }

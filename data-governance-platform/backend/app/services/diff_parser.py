"""
Diff parser for PR governance scanning.

This module parses GitHub PR file changes to identify governance-relevant
files (contracts, schemas, policy definitions) and extract their content
into the contract data format expected by the PolicyOrchestrator for
validation.
"""

import fnmatch
import json
import logging
from typing import List, Dict, Any, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

# Directory names and file-name keywords that signal governance-relevant content.
_GOVERNANCE_DIRS = {"contracts", "policies"}
_GOVERNANCE_KEYWORDS = {"schema", "contract"}


def is_governance_relevant(filepath: str) -> bool:
    """
    Check if a file path matches governance-relevant patterns.

    A file is considered governance-relevant when:
    * It has a YAML or JSON extension, **and**
    * Any directory component is ``contracts`` or ``policies``, **or**
    * The filename contains the substring ``schema`` or ``contract``.

    Args:
        filepath: File path from the PR diff.

    Returns:
        True if the file should be scanned for governance violations.
    """
    normalized = filepath.replace("\\", "/").lower()

    # Must be a data file (YAML / JSON)
    if not normalized.endswith((".yaml", ".yml", ".json")):
        return False

    parts = normalized.split("/")

    # Check if any directory component is a governance directory
    for part in parts[:-1]:  # exclude filename
        if part in _GOVERNANCE_DIRS:
            return True

    # Check if the filename contains a governance keyword
    filename = parts[-1]
    for keyword in _GOVERNANCE_KEYWORDS:
        if keyword in filename:
            return True

    return False


def filter_governance_files(
    files: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Filter PR files to only governance-relevant ones.

    Args:
        files: List of file change objects from GitHub API.

    Returns:
        Filtered list containing only governance-relevant files.
    """
    relevant = []
    for f in files:
        filename = f.get("filename", "")
        if f.get("status") == "removed":
            continue  # Skip deleted files
        if is_governance_relevant(filename):
            relevant.append(f)
    return relevant


def parse_file_content(content: str, filepath: str) -> Optional[Dict[str, Any]]:
    """
    Parse file content (YAML or JSON) into a dictionary.

    Args:
        content: Raw file content string.
        filepath: File path for format detection.

    Returns:
        Parsed dictionary, or None if parsing fails.
    """
    if not content or not content.strip():
        return None

    try:
        if filepath.endswith((".yaml", ".yml")):
            return yaml.safe_load(content)
        elif filepath.endswith(".json"):
            return json.loads(content)
    except (yaml.YAMLError, json.JSONDecodeError) as e:
        logger.warning(f"Failed to parse {filepath}: {e}")
    return None


def extract_contract_data(parsed: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Extract or build a contract data structure from parsed file content.

    The PolicyOrchestrator expects a contract dict with keys:
    dataset, schema, governance, quality_rules.

    This function handles:
    1. Full contracts (already have the expected structure)
    2. Partial schemas (wraps them in the expected contract structure)
    3. Policy files (returns None, not validated as contracts)

    Args:
        parsed: Parsed file content dictionary.

    Returns:
        Contract data dict suitable for PolicyOrchestrator, or None.
    """
    if not isinstance(parsed, dict):
        return None

    # Case 1: Full contract with expected keys
    if "dataset" in parsed and "schema" in parsed:
        return _normalize_contract(parsed)

    # Case 2: Has a "policies" key - this is a policy file, not a contract
    if "policies" in parsed:
        return None

    # Case 3: Has schema-like content at top level (list of field defs)
    if "schema" in parsed and isinstance(parsed["schema"], list):
        return _wrap_partial_schema(parsed)

    # Case 4: Has fields array directly
    if "fields" in parsed and isinstance(parsed["fields"], list):
        return _wrap_fields_as_contract(parsed)

    # Case 5: The parsed content itself looks like a list of fields
    if isinstance(parsed, list) and len(parsed) > 0 and isinstance(parsed[0], dict):
        if "name" in parsed[0] and "type" in parsed[0]:
            return _wrap_fields_as_contract({"fields": parsed})

    return None


def _normalize_contract(contract: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure contract has all expected keys with defaults."""
    normalized = {
        "dataset": contract.get("dataset", {}),
        "schema": contract.get("schema", []),
        "governance": contract.get("governance", {}),
        "quality_rules": contract.get("quality_rules", {}),
    }

    # Ensure dataset has required fields
    dataset = normalized["dataset"]
    if not dataset.get("name"):
        dataset["name"] = "unknown"
    if not dataset.get("description"):
        dataset["description"] = ""

    return normalized


def _wrap_partial_schema(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap a partial schema definition into a full contract structure."""
    return {
        "dataset": {
            "name": parsed.get("name", parsed.get("dataset_name", "unknown")),
            "description": parsed.get("description", ""),
            "owner_name": parsed.get("owner_name", parsed.get("owner", "")),
            "owner_email": parsed.get("owner_email", ""),
        },
        "schema": parsed["schema"],
        "governance": parsed.get("governance", {}),
        "quality_rules": parsed.get("quality_rules", {}),
    }


def _wrap_fields_as_contract(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap a fields-only definition into a full contract structure."""
    return {
        "dataset": {
            "name": parsed.get("name", "unknown"),
            "description": parsed.get("description", ""),
            "owner_name": parsed.get("owner_name", ""),
            "owner_email": parsed.get("owner_email", ""),
        },
        "schema": parsed["fields"],
        "governance": parsed.get("governance", {}),
        "quality_rules": parsed.get("quality_rules", {}),
    }


def parse_pr_files(
    files: List[Dict[str, Any]], file_contents: Dict[str, str]
) -> List[Tuple[str, Dict[str, Any]]]:
    """
    Parse all governance-relevant PR files into validatable contract data.

    This is the main entry point for diff parsing. It:
    1. Filters files to governance-relevant ones
    2. Parses their content (YAML/JSON)
    3. Extracts contract data structures

    Args:
        files: List of file change objects from GitHub API.
        file_contents: Mapping of filename -> full file content.

    Returns:
        List of (filename, contract_data) tuples ready for validation.
    """
    relevant = filter_governance_files(files)
    results = []

    for f in relevant:
        filename = f.get("filename", "")
        content = file_contents.get(filename)

        if not content:
            logger.warning(f"No content available for {filename}")
            continue

        parsed = parse_file_content(content, filename)
        if parsed is None:
            logger.warning(f"Failed to parse {filename}")
            continue

        contract_data = extract_contract_data(parsed)
        if contract_data is None:
            logger.info(f"Skipping {filename}: not a validatable contract")
            continue

        results.append((filename, contract_data))

    return results

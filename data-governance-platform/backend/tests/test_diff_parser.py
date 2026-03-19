"""
Tests for the diff parser service.

Tests file pattern matching, content parsing, and contract data extraction
for the PR governance agent.
"""

import pytest
from app.services.diff_parser import (
    is_governance_relevant,
    filter_governance_files,
    parse_file_content,
    extract_contract_data,
    parse_pr_files,
)


@pytest.mark.unit
class TestIsGovernanceRelevant:
    """Test file pattern matching for governance-relevant files."""

    def test_contract_yaml(self):
        assert is_governance_relevant("contracts/customer.yaml") is True

    def test_contract_yml(self):
        assert is_governance_relevant("contracts/data/orders.yml") is True

    def test_contract_json(self):
        assert is_governance_relevant("contracts/schema.json") is True

    def test_nested_contract(self):
        assert is_governance_relevant("backend/contracts/v2/dataset.yaml") is True

    def test_policy_yaml(self):
        assert is_governance_relevant("policies/sensitive_data.yaml") is True

    def test_nested_policy(self):
        assert is_governance_relevant("backend/policies/quality.yml") is True

    def test_schema_file(self):
        assert is_governance_relevant("data/schema_v2.yaml") is True

    def test_contract_named_file(self):
        assert is_governance_relevant("data/contract_customer.json") is True

    def test_irrelevant_python(self):
        assert is_governance_relevant("app/services/main.py") is False

    def test_irrelevant_readme(self):
        assert is_governance_relevant("README.md") is False

    def test_irrelevant_requirements(self):
        assert is_governance_relevant("requirements.txt") is False

    def test_irrelevant_javascript(self):
        assert is_governance_relevant("frontend/src/App.jsx") is False

    def test_irrelevant_test_file(self):
        assert is_governance_relevant("tests/test_api.py") is False


@pytest.mark.unit
class TestFilterGovernanceFiles:
    """Test filtering PR files to governance-relevant ones."""

    def test_filters_relevant_files(self):
        files = [
            {"filename": "contracts/customer.yaml", "status": "modified"},
            {"filename": "app/main.py", "status": "modified"},
            {"filename": "policies/quality.yaml", "status": "added"},
        ]
        result = filter_governance_files(files)
        assert len(result) == 2
        assert result[0]["filename"] == "contracts/customer.yaml"
        assert result[1]["filename"] == "policies/quality.yaml"

    def test_excludes_removed_files(self):
        files = [
            {"filename": "contracts/old.yaml", "status": "removed"},
            {"filename": "contracts/new.yaml", "status": "added"},
        ]
        result = filter_governance_files(files)
        assert len(result) == 1
        assert result[0]["filename"] == "contracts/new.yaml"

    def test_empty_list(self):
        assert filter_governance_files([]) == []

    def test_no_relevant_files(self):
        files = [
            {"filename": "app/main.py", "status": "modified"},
            {"filename": "README.md", "status": "modified"},
        ]
        assert filter_governance_files(files) == []


@pytest.mark.unit
class TestParseFileContent:
    """Test YAML/JSON content parsing."""

    def test_parse_yaml(self):
        content = "name: test\nversion: '1.0'"
        result = parse_file_content(content, "test.yaml")
        assert result == {"name": "test", "version": "1.0"}

    def test_parse_yml(self):
        content = "key: value"
        result = parse_file_content(content, "test.yml")
        assert result == {"key": "value"}

    def test_parse_json(self):
        content = '{"name": "test", "version": "1.0"}'
        result = parse_file_content(content, "test.json")
        assert result == {"name": "test", "version": "1.0"}

    def test_invalid_yaml(self):
        content = "{ invalid: yaml: content: [["
        result = parse_file_content(content, "test.yaml")
        assert result is None

    def test_invalid_json(self):
        content = "not json"
        result = parse_file_content(content, "test.json")
        assert result is None

    def test_empty_content(self):
        assert parse_file_content("", "test.yaml") is None
        assert parse_file_content("  ", "test.yaml") is None

    def test_none_content(self):
        assert parse_file_content(None, "test.yaml") is None


@pytest.mark.unit
class TestExtractContractData:
    """Test contract data extraction from parsed content."""

    def test_full_contract(self):
        parsed = {
            "dataset": {"name": "test", "description": "Test dataset"},
            "schema": [{"name": "id", "type": "integer"}],
            "governance": {"classification": "internal"},
            "quality_rules": {"completeness_threshold": 95},
        }
        result = extract_contract_data(parsed)
        assert result is not None
        assert result["dataset"]["name"] == "test"
        assert len(result["schema"]) == 1

    def test_partial_schema(self):
        parsed = {
            "name": "customers",
            "schema": [
                {"name": "id", "type": "integer"},
                {"name": "email", "type": "string"},
            ],
        }
        result = extract_contract_data(parsed)
        assert result is not None
        assert result["dataset"]["name"] == "customers"
        assert len(result["schema"]) == 2

    def test_policy_file_returns_none(self):
        parsed = {
            "policies": [
                {"id": "SD001", "name": "test_policy"},
            ]
        }
        result = extract_contract_data(parsed)
        assert result is None

    def test_fields_format(self):
        parsed = {
            "name": "orders",
            "fields": [
                {"name": "order_id", "type": "integer"},
            ],
        }
        result = extract_contract_data(parsed)
        assert result is not None
        assert result["dataset"]["name"] == "orders"
        assert len(result["schema"]) == 1

    def test_non_dict_returns_none(self):
        assert extract_contract_data("string") is None
        assert extract_contract_data(None) is None

    def test_unrecognized_format_returns_none(self):
        parsed = {"random_key": "random_value"}
        result = extract_contract_data(parsed)
        assert result is None

    def test_contract_with_missing_keys_gets_defaults(self):
        parsed = {
            "dataset": {},
            "schema": [],
        }
        result = extract_contract_data(parsed)
        assert result is not None
        assert result["dataset"]["name"] == "unknown"
        assert result["governance"] == {}


@pytest.mark.unit
class TestParsePrFiles:
    """Test end-to-end PR file parsing."""

    def test_parse_valid_contract_file(self):
        import yaml
        contract = {
            "dataset": {"name": "test", "description": "Test"},
            "schema": [{"name": "id", "type": "integer"}],
            "governance": {"classification": "internal"},
        }
        files = [{"filename": "contracts/test.yaml", "status": "modified"}]
        contents = {"contracts/test.yaml": yaml.dump(contract)}
        result = parse_pr_files(files, contents)
        assert len(result) == 1
        assert result[0][0] == "contracts/test.yaml"
        assert result[0][1]["dataset"]["name"] == "test"

    def test_skip_missing_content(self):
        files = [{"filename": "contracts/test.yaml", "status": "modified"}]
        contents = {}
        result = parse_pr_files(files, contents)
        assert len(result) == 0

    def test_skip_policy_files(self):
        import yaml
        policy = {"policies": [{"id": "SD001", "name": "test"}]}
        files = [{"filename": "policies/test.yaml", "status": "modified"}]
        contents = {"policies/test.yaml": yaml.dump(policy)}
        result = parse_pr_files(files, contents)
        assert len(result) == 0

    def test_skip_irrelevant_files(self):
        files = [{"filename": "app/main.py", "status": "modified"}]
        contents = {"app/main.py": "print('hello')"}
        result = parse_pr_files(files, contents)
        assert len(result) == 0

    def test_multiple_files(self):
        import yaml
        contract1 = {
            "dataset": {"name": "c1"},
            "schema": [{"name": "id", "type": "int"}],
        }
        contract2 = {
            "dataset": {"name": "c2"},
            "schema": [{"name": "id", "type": "int"}],
        }
        files = [
            {"filename": "contracts/c1.yaml", "status": "modified"},
            {"filename": "contracts/c2.yaml", "status": "added"},
        ]
        contents = {
            "contracts/c1.yaml": yaml.dump(contract1),
            "contracts/c2.yaml": yaml.dump(contract2),
        }
        result = parse_pr_files(files, contents)
        assert len(result) == 2

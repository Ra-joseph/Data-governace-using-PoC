"""
Unit tests for ContractService.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.contract_service import ContractService
from app.models.contract import Contract
from app.schemas.contract import ValidationStatus


@pytest.mark.unit
@pytest.mark.service
class TestContractService:
    """Test cases for ContractService."""

    def test_contract_service_initialization(self):
        """Test that ContractService initializes correctly."""
        service = ContractService()
        assert service is not None
        assert service.policy_engine is not None
        assert service.git_service is not None

    def test_calculate_schema_hash(self):
        """Test schema hash calculation."""
        service = ContractService()
        schema = [
            {"name": "id", "type": "integer"},
            {"name": "email", "type": "string"}
        ]

        hash1 = service._calculate_schema_hash(schema)
        hash2 = service._calculate_schema_hash(schema)

        # Same schema should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64 hex characters

    def test_calculate_schema_hash_different_schemas(self):
        """Test that different schemas produce different hashes."""
        service = ContractService()
        schema1 = [{"name": "id", "type": "integer"}]
        schema2 = [{"name": "email", "type": "string"}]

        hash1 = service._calculate_schema_hash(schema1)
        hash2 = service._calculate_schema_hash(schema2)

        assert hash1 != hash2

    def test_generate_yaml(self):
        """Test YAML generation."""
        service = ContractService()
        contract_data = {
            "dataset": {"name": "test", "version": "1.0.0"},
            "schema": [{"name": "id", "type": "integer"}],
            "governance": {"classification": "internal"}
        }

        yaml_output = service._generate_yaml(contract_data, "test", "1.0.0")

        assert "# Data Contract" in yaml_output
        assert "# Dataset: test" in yaml_output
        assert "# Version: 1.0.0" in yaml_output
        assert "dataset:" in yaml_output
        assert "schema:" in yaml_output
        assert "governance:" in yaml_output

    def test_validate_contract_with_json(self, sample_contract_data):
        """Test contract validation with JSON input."""
        service = ContractService()
        result = service.validate_contract(contract_json=sample_contract_data)

        assert result is not None
        assert hasattr(result, 'status')
        assert result.status == ValidationStatus.PASSED

    def test_validate_contract_with_yaml(self):
        """Test contract validation with YAML input."""
        service = ContractService()
        yaml_content = """
dataset:
  name: test
  owner_name: Test Owner
  owner_email: test@example.com
schema:
  - name: id
    type: integer
    description: ID field
    pii: false
governance:
  classification: internal
quality_rules: {}
"""
        result = service.validate_contract(contract_yaml=yaml_content)

        assert result is not None
        assert hasattr(result, 'status')

    def test_validate_contract_no_input(self):
        """Test that validation fails when no input is provided."""
        service = ContractService()

        with pytest.raises(ValueError, match="Either contract_yaml or contract_json must be provided"):
            service.validate_contract()

    @patch('app.services.contract_service.GitService')
    def test_create_contract_from_dataset(self, mock_git_service, db, sample_dataset):
        """Test contract creation from dataset."""
        # Mock GitService
        mock_git_instance = MagicMock()
        mock_git_instance.commit_contract.return_value = {
            'commit_hash': 'abc123',
            'file_path': 'contracts/test_customers_v1.0.0.yaml'
        }
        mock_git_service.return_value = mock_git_instance

        service = ContractService()
        service.git_service = mock_git_instance

        contract = service.create_contract_from_dataset(db, sample_dataset.id, version="1.0.0")

        assert contract is not None
        assert contract.dataset_id == sample_dataset.id
        assert contract.version == "1.0.0"
        assert contract.human_readable is not None
        assert contract.machine_readable is not None
        assert contract.schema_hash is not None
        assert contract.validation_status is not None
        assert mock_git_instance.commit_contract.called

    @patch('app.services.contract_service.GitService')
    def test_create_contract_dataset_not_found(self, mock_git_service, db):
        """Test contract creation with non-existent dataset."""
        mock_git_instance = MagicMock()
        mock_git_service.return_value = mock_git_instance

        service = ContractService()
        service.git_service = mock_git_instance

        with pytest.raises(ValueError, match="Dataset with ID 99999 not found"):
            service.create_contract_from_dataset(db, 99999, version="1.0.0")

    @patch('app.services.contract_service.GitService')
    def test_create_contract_sets_encryption_for_pii(self, mock_git_service, db, sample_dataset):
        """Test that encryption is set when dataset contains PII."""
        # Mock GitService
        mock_git_instance = MagicMock()
        mock_git_instance.commit_contract.return_value = {
            'commit_hash': 'abc123',
            'file_path': 'contracts/test.yaml'
        }
        mock_git_service.return_value = mock_git_instance

        service = ContractService()
        service.git_service = mock_git_instance

        contract = service.create_contract_from_dataset(db, sample_dataset.id, version="1.0.0")

        # Dataset has PII, so encryption should be required
        assert contract.governance_rules.get('encryption_required') is True

    @patch('app.services.contract_service.GitService')
    def test_enrich_contract_with_slas(self, mock_git_service, db, sample_dataset):
        """Test enriching contract with SLA requirements."""
        # First create a contract
        mock_git_instance = MagicMock()
        mock_git_instance.commit_contract.return_value = {
            'commit_hash': 'abc123',
            'file_path': 'contracts/test.yaml'
        }
        mock_git_service.return_value = mock_git_instance

        service = ContractService()
        service.git_service = mock_git_instance

        initial_contract = service.create_contract_from_dataset(db, sample_dataset.id, version="1.0.0")

        # Now enrich with SLAs
        sla_data = {
            "availability": "99.9%",
            "latency": "< 100ms",
            "support_hours": "24/7"
        }

        enriched_contract = service.enrich_contract_with_slas(db, initial_contract.id, sla_data)

        assert enriched_contract is not None
        assert enriched_contract.version == "1.1.0"  # Minor version bump
        assert enriched_contract.sla_requirements == sla_data
        assert 'sla_requirements' in enriched_contract.machine_readable

    def test_enrich_contract_not_found(self, db):
        """Test enriching non-existent contract."""
        service = ContractService()

        with pytest.raises(ValueError, match="Contract with ID 99999 not found"):
            service.enrich_contract_with_slas(db, 99999, {})

    @patch('app.services.contract_service.GitService')
    def test_get_contract_diff(self, mock_git_service, db, sample_dataset):
        """Test getting diff between two contract versions."""
        # Create two versions
        mock_git_instance = MagicMock()
        mock_git_instance.commit_contract.return_value = {
            'commit_hash': 'abc123',
            'file_path': 'contracts/test.yaml'
        }
        mock_git_service.return_value = mock_git_instance

        service = ContractService()
        service.git_service = mock_git_instance

        v1 = service.create_contract_from_dataset(db, sample_dataset.id, version="1.0.0")
        v2 = service.enrich_contract_with_slas(db, v1.id, {"availability": "99.9%"})

        diff = service.get_contract_diff(db, v1.id, v2.id)

        assert diff is not None
        assert 'version_change' in diff
        assert 'schema_changed' in diff
        assert 'sla_added' in diff
        assert diff['version_change'] == "1.0.0 -> 1.1.0"
        assert diff['sla_added'] is True
        assert diff['schema_changed'] is False

    def test_get_contract_diff_not_found(self, db):
        """Test diff with non-existent contracts."""
        service = ContractService()

        with pytest.raises(ValueError, match="One or both contracts not found"):
            service.get_contract_diff(db, 99999, 99998)

    def test_get_yaml_diff(self):
        """Test YAML diff generation."""
        service = ContractService()
        old_yaml = "line1\nline2\nline3"
        new_yaml = "line1\nline2_modified\nline3\nline4"

        diff = service._get_yaml_diff(old_yaml, new_yaml)

        assert len(diff) > 0
        assert diff[0]['line'] == 2
        assert diff[0]['old'] == 'line2'
        assert diff[0]['new'] == 'line2_modified'

    @patch('app.services.contract_service.GitService')
    def test_add_subscription_to_contract(self, mock_git_service, db, sample_dataset):
        """Test adding subscription to contract."""
        # First create a contract
        mock_git_instance = MagicMock()
        mock_git_instance.commit_contract.return_value = {
            'commit_hash': 'abc123',
            'file_path': 'contracts/test.yaml'
        }
        mock_git_service.return_value = mock_git_instance

        service = ContractService(db=db)
        service.git_service = mock_git_instance

        initial_contract = service.create_contract_from_dataset(db, sample_dataset.id, version="1.0.0")

        # Add subscription
        subscription_data = {
            "consumer": "Analytics Team",
            "sla_requirements": {"latency": "< 100ms"},
            "approved_fields": ["customer_id", "email"]
        }

        updated_contract = service.add_subscription_to_contract(
            initial_contract.id,
            123,
            subscription_data
        )

        assert updated_contract is not None
        assert updated_contract.version == "1.1.0"
        assert 'subscriptions' in updated_contract.machine_readable
        assert len(updated_contract.machine_readable['subscriptions']) == 1

    def test_add_subscription_no_db_session(self):
        """Test adding subscription without db session."""
        service = ContractService()  # No db session

        with pytest.raises(ValueError, match="Database session required"):
            service.add_subscription_to_contract(1, 1, {})

    def test_contract_contains_all_dataset_info(self, db, sample_dataset):
        """Test that contract includes all dataset information."""
        with patch('app.services.contract_service.GitService') as mock_git:
            mock_git_instance = MagicMock()
            mock_git_instance.commit_contract.return_value = {
                'commit_hash': 'abc123',
                'file_path': 'contracts/test.yaml'
            }
            mock_git.return_value = mock_git_instance

            service = ContractService()
            service.git_service = mock_git_instance

            contract = service.create_contract_from_dataset(db, sample_dataset.id, version="1.0.0")

            contract_data = contract.machine_readable
            assert contract_data['dataset']['name'] == sample_dataset.name
            assert contract_data['dataset']['description'] == sample_dataset.description
            assert contract_data['dataset']['owner_name'] == sample_dataset.owner_name
            assert contract_data['dataset']['owner_email'] == sample_dataset.owner_email
            assert contract_data['schema'] == sample_dataset.schema_definition
            assert contract_data['governance']['classification'] == sample_dataset.classification

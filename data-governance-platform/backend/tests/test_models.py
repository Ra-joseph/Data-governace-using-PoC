"""
Unit tests for database models.
"""
import pytest
from datetime import datetime
from app.models.dataset import Dataset
from app.models.contract import Contract
from app.models.subscription import Subscription


@pytest.mark.unit
class TestDatasetModel:
    """Test cases for Dataset model."""

    def test_create_dataset(self, db):
        """Test creating a dataset."""
        dataset = Dataset(
            name="test_dataset",
            description="Test dataset",
            owner_name="Test Owner",
            owner_email="test@example.com",
            source_type="postgres",
            source_connection="postgresql://localhost/test",
            physical_location="public.test_table",
            schema_definition=[
                {"name": "id", "type": "integer", "pii": False}
            ],
            classification="internal",
            contains_pii=False,
            status="draft"
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        assert dataset.id is not None
        assert dataset.name == "test_dataset"
        assert dataset.created_at is not None
        assert dataset.is_active is True

    def test_dataset_defaults(self, db):
        """Test dataset default values."""
        dataset = Dataset(
            name="test",
            description="Test",
            owner_name="Owner",
            owner_email="owner@example.com",
            source_type="postgres",
            classification="internal"
        )

        db.add(dataset)
        db.commit()
        db.refresh(dataset)

        assert dataset.is_active is True
        assert dataset.status == "draft"
        assert dataset.contains_pii is False

    def test_dataset_relationships(self, db, sample_dataset):
        """Test dataset relationships."""
        # Create a contract for the dataset
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={},
            schema_hash="abc123",
            governance_rules={},
            validation_status="passed"
        )
        db.add(contract)

        # Create a subscription for the dataset
        subscription = Subscription(
            dataset_id=sample_dataset.id,
            consumer_name="Consumer",
            consumer_email="consumer@example.com",
            status="pending",
            access_granted=False
        )
        db.add(subscription)

        db.commit()
        db.refresh(sample_dataset)

        assert len(sample_dataset.contracts) == 1
        assert len(sample_dataset.subscriptions) == 1


@pytest.mark.unit
class TestContractModel:
    """Test cases for Contract model."""

    def test_create_contract(self, db, sample_dataset):
        """Test creating a contract."""
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Data Contract\nversion: 1.0.0",
            machine_readable={
                "dataset": {"name": "test", "version": "1.0.0"},
                "schema": []
            },
            schema_hash="abc123def456",
            governance_rules={"classification": "internal"},
            quality_rules={"completeness_threshold": 95},
            validation_status="passed",
            git_commit_hash="commit123",
            git_file_path="contracts/test_v1.0.0.yaml"
        )

        db.add(contract)
        db.commit()
        db.refresh(contract)

        assert contract.id is not None
        assert contract.dataset_id == sample_dataset.id
        assert contract.version == "1.0.0"
        assert contract.created_at is not None
        assert contract.last_validated_at is not None

    def test_contract_validation_results(self, db, sample_dataset):
        """Test storing validation results."""
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={},
            schema_hash="abc",
            governance_rules={},
            validation_status="failed",
            validation_results={
                "status": "failed",
                "passed": 10,
                "failures": 2,
                "warnings": 1,
                "violations": [
                    {"policy": "SD001", "type": "critical", "message": "Error"}
                ]
            }
        )

        db.add(contract)
        db.commit()
        db.refresh(contract)

        assert contract.validation_results is not None
        assert contract.validation_results["status"] == "failed"
        assert len(contract.validation_results["violations"]) == 1

    def test_contract_relationship_with_dataset(self, db, sample_dataset):
        """Test contract-dataset relationship."""
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={},
            schema_hash="abc",
            governance_rules={},
            validation_status="passed"
        )

        db.add(contract)
        db.commit()
        db.refresh(contract)

        assert contract.dataset is not None
        assert contract.dataset.id == sample_dataset.id
        assert contract.dataset.name == sample_dataset.name


@pytest.mark.unit
class TestSubscriptionModel:
    """Test cases for Subscription model."""

    def test_create_subscription(self, db, sample_dataset):
        """Test creating a subscription."""
        subscription = Subscription(
            dataset_id=sample_dataset.id,
            consumer_name="Analytics Team",
            consumer_email="analytics@example.com",
            consumer_team="Data Science",
            purpose="Monthly reporting",
            use_case="analytics",
            status="pending",
            access_granted=False
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        assert subscription.id is not None
        assert subscription.dataset_id == sample_dataset.id
        assert subscription.status == "pending"
        assert subscription.created_at is not None

    def test_subscription_approval(self, db, sample_dataset):
        """Test subscription approval workflow."""
        subscription = Subscription(
            dataset_id=sample_dataset.id,
            consumer_name="Test Consumer",
            consumer_email="consumer@example.com",
            status="pending",
            access_granted=False
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        # Approve subscription
        subscription.status = "approved"
        subscription.access_granted = True
        subscription.approved_at = datetime.utcnow()
        subscription.access_credentials = "username: test_user"
        subscription.access_endpoint = "postgresql://localhost/test"

        db.commit()
        db.refresh(subscription)

        assert subscription.status == "approved"
        assert subscription.access_granted is True
        assert subscription.approved_at is not None
        assert subscription.access_credentials is not None

    def test_subscription_with_data_filters(self, db, sample_dataset):
        """Test subscription with data filters and SLA."""
        subscription = Subscription(
            dataset_id=sample_dataset.id,
            consumer_name="Consumer",
            consumer_email="consumer@example.com",
            status="pending",
            access_granted=False,
            data_filters={
                "sla_requirements": {
                    "availability": "99.9%",
                    "latency": "< 100ms"
                },
                "required_fields": ["id", "name", "email"],
                "access_duration_days": 365
            }
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        assert subscription.data_filters is not None
        assert "sla_requirements" in subscription.data_filters
        assert subscription.data_filters["sla_requirements"]["availability"] == "99.9%"

    def test_subscription_rejection(self, db, sample_dataset):
        """Test subscription rejection."""
        subscription = Subscription(
            dataset_id=sample_dataset.id,
            consumer_name="Test Consumer",
            consumer_email="consumer@example.com",
            status="pending",
            access_granted=False
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        # Reject subscription
        subscription.status = "rejected"
        subscription.rejection_reason = "Insufficient business justification"

        db.commit()
        db.refresh(subscription)

        assert subscription.status == "rejected"
        assert subscription.access_granted is False
        assert "business justification" in subscription.rejection_reason

    def test_subscription_relationship_with_dataset(self, db, sample_dataset):
        """Test subscription-dataset relationship."""
        subscription = Subscription(
            dataset_id=sample_dataset.id,
            consumer_name="Consumer",
            consumer_email="consumer@example.com",
            status="pending",
            access_granted=False
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        assert subscription.dataset is not None
        assert subscription.dataset.id == sample_dataset.id
        assert subscription.dataset.name == sample_dataset.name

    def test_subscription_with_contract(self, db, sample_dataset):
        """Test subscription linked to a contract."""
        # Create contract
        contract = Contract(
            dataset_id=sample_dataset.id,
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={},
            schema_hash="abc",
            governance_rules={},
            validation_status="passed"
        )
        db.add(contract)
        db.commit()

        # Create subscription linked to contract
        subscription = Subscription(
            dataset_id=sample_dataset.id,
            contract_id=contract.id,
            consumer_name="Consumer",
            consumer_email="consumer@example.com",
            status="approved",
            access_granted=True
        )

        db.add(subscription)
        db.commit()
        db.refresh(subscription)

        assert subscription.contract_id == contract.id
        assert subscription.contract is not None


@pytest.mark.unit
class TestModelConstraints:
    """Test model constraints and validations."""

    def test_dataset_unique_name(self, db, sample_dataset):
        """Test that dataset names must be unique."""
        duplicate_dataset = Dataset(
            name="test_customers",  # Same name as sample_dataset
            description="Duplicate",
            owner_name="Owner",
            owner_email="owner@example.com",
            source_type="postgres",
            classification="internal"
        )

        db.add(duplicate_dataset)

        with pytest.raises(Exception):  # Will raise IntegrityError
            db.commit()

    def test_contract_requires_dataset(self, db):
        """Test that contract requires a valid dataset."""
        contract = Contract(
            dataset_id=99999,  # Non-existent dataset
            version="1.0.0",
            human_readable="# Contract",
            machine_readable={},
            schema_hash="abc",
            governance_rules={},
            validation_status="passed"
        )

        db.add(contract)

        with pytest.raises(Exception):  # Will raise IntegrityError
            db.commit()

    def test_subscription_requires_dataset(self, db):
        """Test that subscription requires a valid dataset."""
        subscription = Subscription(
            dataset_id=99999,  # Non-existent dataset
            consumer_name="Consumer",
            consumer_email="consumer@example.com",
            status="pending",
            access_granted=False
        )

        db.add(subscription)

        with pytest.raises(Exception):  # Will raise IntegrityError
            db.commit()

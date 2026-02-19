"""
Unit tests for datasets API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from fastapi.testclient import TestClient


@pytest.mark.api
@pytest.mark.unit
class TestDatasetsAPI:
    """Test cases for datasets API endpoints."""

    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "docs" in data

    def test_list_datasets_empty(self, client):
        """Test listing datasets when database is empty."""
        response = client.get("/api/v1/datasets/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @patch('app.api.datasets.contract_service.create_contract_from_dataset')
    def test_create_dataset(self, mock_create_contract, client):
        """Test creating a new dataset."""
        # Mock contract creation
        mock_contract = MagicMock()
        mock_contract.validation_status = "passed"
        mock_contract.created_at = datetime(2024, 1, 1)
        mock_create_contract.return_value = mock_contract

        dataset_data = {
            "name": "test_dataset",
            "description": "Test dataset for unit testing",
            "owner_name": "Test Owner",
            "owner_email": "test@example.com",
            "source_type": "postgres",
            "source_connection": "postgresql://localhost/test",
            "physical_location": "public.test_table",
            "schema_definition": [
                {
                    "name": "id",
                    "type": "integer",
                    "description": "ID field",
                    "required": True,
                    "nullable": False,
                    "pii": False
                }
            ],
            "governance": {
                "classification": "internal",
                "compliance_tags": []
            }
        }

        response = client.post("/api/v1/datasets/", json=dataset_data)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test_dataset"
        assert data["owner_email"] == "test@example.com"
        assert data["status"] == "published"

    def test_create_dataset_duplicate(self, client, sample_dataset):
        """Test creating a dataset with duplicate name."""
        dataset_data = {
            "name": "test_customers",  # Same as sample_dataset
            "description": "Duplicate",
            "owner_name": "Test",
            "owner_email": "test@example.com",
            "source_type": "postgres",
            "source_connection": "postgresql://localhost/test",
            "physical_location": "public.test",
            "schema_definition": [
                {
                    "name": "id",
                    "type": "integer",
                    "description": "ID",
                    "required": True,
                    "nullable": False,
                    "pii": False
                }
            ],
            "governance": {
                "classification": "internal",
                "compliance_tags": []
            }
        }

        response = client.post("/api/v1/datasets/", json=dataset_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]

    @patch('app.api.datasets.contract_service.create_contract_from_dataset')
    def test_list_datasets_with_data(self, mock_create_contract, client, sample_dataset):
        """Test listing datasets when data exists."""
        response = client.get("/api/v1/datasets/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["name"] == "test_customers"

    def test_get_dataset_by_id(self, client, sample_dataset):
        """Test getting a specific dataset by ID."""
        response = client.get(f"/api/v1/datasets/{sample_dataset.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_dataset.id
        assert data["name"] == sample_dataset.name
        assert data["owner_email"] == sample_dataset.owner_email

    def test_get_dataset_not_found(self, client):
        """Test getting a non-existent dataset."""
        response = client.get("/api/v1/datasets/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    @patch('app.api.datasets.contract_service.create_contract_from_dataset')
    def test_update_dataset(self, mock_create_contract, client, sample_dataset):
        """Test updating a dataset."""
        mock_contract = MagicMock()
        mock_contract.validation_status = "passed"
        mock_contract.created_at = datetime(2024, 1, 1)
        mock_contract.version = "2.0.0"
        mock_create_contract.return_value = mock_contract

        update_data = {
            "description": "Updated description",
            "owner_name": "Updated Owner"
        }

        response = client.put(f"/api/v1/datasets/{sample_dataset.id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"
        assert data["owner_name"] == "Updated Owner"

    def test_update_dataset_not_found(self, client):
        """Test updating a non-existent dataset."""
        update_data = {"description": "Updated"}

        response = client.put("/api/v1/datasets/99999", json=update_data)
        assert response.status_code == 404

    def test_delete_dataset(self, client, sample_dataset):
        """Test deleting a dataset (soft delete)."""
        response = client.delete(f"/api/v1/datasets/{sample_dataset.id}")
        assert response.status_code == 204

        # Verify it's soft deleted
        response = client.get(f"/api/v1/datasets/{sample_dataset.id}")
        assert response.status_code == 404

    def test_delete_dataset_not_found(self, client):
        """Test deleting a non-existent dataset."""
        response = client.delete("/api/v1/datasets/99999")
        assert response.status_code == 404

    def test_list_datasets_with_filters(self, client, sample_dataset):
        """Test listing datasets with filters."""
        # Filter by owner_email
        response = client.get(f"/api/v1/datasets/?owner_email={sample_dataset.owner_email}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert all(d["owner_email"] == sample_dataset.owner_email for d in data)

        # Filter by classification
        response = client.get(f"/api/v1/datasets/?classification={sample_dataset.classification}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    def test_list_datasets_pagination(self, client):
        """Test dataset listing with pagination."""
        response = client.get("/api/v1/datasets/?skip=0&limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    @patch('app.api.datasets.PostgresConnector')
    def test_import_schema_postgres(self, mock_connector_class, client):
        """Test schema import from PostgreSQL."""
        # Mock PostgresConnector
        mock_connector = MagicMock()
        mock_connector.test_connection.return_value = True
        mock_connector.import_table_schema.return_value = {
            "table_name": "customers",
            "schema_name": "public",
            "description": "Customer table",
            "schema_definition": [
                {
                    "name": "id",
                    "type": "integer",
                    "description": "Customer ID",
                    "pii": False
                }
            ],
            "metadata": {
                "contains_pii": False,
                "suggested_classification": "internal",
                "primary_keys": ["id"],
                "row_count": 100
            }
        }
        mock_connector_class.return_value = mock_connector

        import_request = {
            "source_type": "postgres",
            "table_name": "customers",
            "schema_name": "public"
        }

        response = client.post("/api/v1/datasets/import-schema", json=import_request)
        assert response.status_code == 200
        data = response.json()
        assert data["table_name"] == "customers"
        assert "schema_definition" in data

    def test_import_schema_missing_table_name(self, client):
        """Test schema import without table name."""
        import_request = {
            "source_type": "postgres",
            "schema_name": "public"
        }

        response = client.post("/api/v1/datasets/import-schema", json=import_request)
        assert response.status_code == 400  # Missing table_name

    def test_import_schema_unsupported_source(self, client):
        """Test schema import with unsupported source type."""
        import_request = {
            "source_type": "file",
            "table_name": "test"
        }

        response = client.post("/api/v1/datasets/import-schema", json=import_request)
        assert response.status_code == 501  # Not implemented
        assert "not yet implemented" in response.json()["detail"]

    @patch('app.api.datasets.PostgresConnector')
    def test_list_postgres_tables(self, mock_connector_class, client, mock_postgres_tables):
        """Test listing PostgreSQL tables."""
        # Mock PostgresConnector
        mock_connector = MagicMock()
        mock_connector.test_connection.return_value = True
        mock_connector.list_tables.return_value = mock_postgres_tables
        mock_connector_class.return_value = mock_connector

        response = client.get("/api/v1/datasets/postgres/tables?schema=public")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["table_name"] == "customers"

    @patch('app.api.datasets.PostgresConnector')
    def test_list_postgres_tables_connection_failure(self, mock_connector_class, client):
        """Test listing tables when connection fails."""
        # Mock connection failure
        mock_connector = MagicMock()
        mock_connector.test_connection.return_value = False
        mock_connector_class.return_value = mock_connector

        response = client.get("/api/v1/datasets/postgres/tables")
        assert response.status_code == 500
        assert "Failed to connect" in response.json()["detail"]

    @patch('app.api.datasets.contract_service.create_contract_from_dataset')
    def test_dataset_contains_pii_detection(self, mock_create_contract, client):
        """Test that PII is detected in schema."""
        mock_contract = MagicMock()
        mock_contract.validation_status = "passed"
        mock_contract.created_at = datetime(2024, 1, 1)
        mock_create_contract.return_value = mock_contract

        dataset_data = {
            "name": "pii_dataset",
            "description": "Dataset with PII",
            "owner_name": "Test Owner",
            "owner_email": "test@example.com",
            "source_type": "postgres",
            "source_connection": "postgresql://localhost/test",
            "physical_location": "public.pii_table",
            "schema_definition": [
                {
                    "name": "ssn",
                    "type": "string",
                    "description": "Social Security Number",
                    "required": True,
                    "nullable": False,
                    "pii": True  # PII field
                }
            ],
            "governance": {
                "classification": "confidential",
                "compliance_tags": ["GDPR"]
            }
        }

        response = client.post("/api/v1/datasets/", json=dataset_data)
        assert response.status_code == 201
        data = response.json()
        assert data["contains_pii"] is True

    @patch('app.api.datasets.contract_service.create_contract_from_dataset')
    def test_dataset_status_draft_on_validation_failure(self, mock_create_contract, client):
        """Test that dataset status is draft when validation fails."""
        mock_contract = MagicMock()
        mock_contract.validation_status = "failed"  # Failed validation
        mock_contract.created_at = datetime(2024, 1, 1)
        mock_create_contract.return_value = mock_contract

        dataset_data = {
            "name": "failed_dataset",
            "description": "Dataset with validation failures",
            "owner_name": "Test Owner",
            "owner_email": "test@example.com",
            "source_type": "postgres",
            "source_connection": "postgresql://localhost/test",
            "physical_location": "public.failed_table",
            "schema_definition": [
                {
                    "name": "id",
                    "type": "integer",
                    "description": "ID",
                    "required": True,
                    "nullable": False,
                    "pii": False
                }
            ],
            "governance": {
                "classification": "internal",
                "compliance_tags": []
            }
        }

        response = client.post("/api/v1/datasets/", json=dataset_data)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "draft"  # Should be draft due to failed validation

"""
Unit tests for subscriptions API endpoints.
"""
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta


@pytest.mark.api
@pytest.mark.unit
class TestSubscriptionsAPI:
    """Test cases for subscriptions API endpoints."""

    def test_list_subscriptions_empty(self, client):
        """Test listing subscriptions when database is empty."""
        response = client.get("/api/v1/subscriptions/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_create_subscription(self, client, sample_dataset):
        """Test creating a new subscription request."""
        subscription_data = {
            "dataset_id": sample_dataset.id,
            "consumer_name": "Analytics Team",
            "consumer_email": "analytics@example.com",
            "consumer_organization": "Data Science Dept",
            "business_justification": "For monthly reporting",
            "use_case": "analytics",
            "sla_requirements": {
                "availability": "99.9%",
                "latency": "< 100ms"
            },
            "required_fields": ["customer_id", "email"],
            "access_duration_days": 365
        }

        response = client.post("/api/v1/subscriptions/", json=subscription_data)
        assert response.status_code == 201
        data = response.json()
        assert data["consumer_name"] == "Analytics Team"
        assert data["status"] == "pending"
        assert data["access_granted"] is False

    def test_create_subscription_dataset_not_found(self, client):
        """Test creating subscription with non-existent dataset."""
        subscription_data = {
            "dataset_id": 99999,
            "consumer_name": "Test",
            "consumer_email": "test@example.com",
            "consumer_organization": "Test Org",
            "business_justification": "Testing"
        }

        response = client.post("/api/v1/subscriptions/", json=subscription_data)
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_get_subscription_by_id(self, client, sample_dataset):
        """Test getting a specific subscription by ID."""
        # First create a subscription
        subscription_data = {
            "dataset_id": sample_dataset.id,
            "consumer_name": "Test Consumer",
            "consumer_email": "consumer@example.com",
            "consumer_organization": "Test Org",
            "business_justification": "Testing"
        }
        create_response = client.post("/api/v1/subscriptions/", json=subscription_data)
        subscription_id = create_response.json()["id"]

        # Now get it
        response = client.get(f"/api/v1/subscriptions/{subscription_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == subscription_id
        assert data["consumer_name"] == "Test Consumer"

    def test_get_subscription_not_found(self, client):
        """Test getting a non-existent subscription."""
        response = client.get("/api/v1/subscriptions/99999")
        assert response.status_code == 404

    def test_list_subscriptions_with_filters(self, client, sample_dataset):
        """Test listing subscriptions with filters."""
        # Create subscriptions
        subscription_data = {
            "dataset_id": sample_dataset.id,
            "consumer_name": "Consumer 1",
            "consumer_email": "consumer1@example.com",
            "consumer_organization": "Org 1",
            "business_justification": "Testing"
        }
        client.post("/api/v1/subscriptions/", json=subscription_data)

        # Filter by dataset_id
        response = client.get(f"/api/v1/subscriptions/?dataset_id={sample_dataset.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

        # Filter by status
        response = client.get("/api/v1/subscriptions/?status=pending")
        assert response.status_code == 200
        data = response.json()
        assert all(sub["status"] == "pending" for sub in data)

        # Filter by consumer_email
        response = client.get("/api/v1/subscriptions/?consumer_email=consumer1@example.com")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1

    @patch('app.api.subscriptions.ContractService')
    def test_approve_subscription(self, mock_contract_service, client, sample_dataset, db):
        """Test approving a subscription request."""
        # Create subscription
        subscription_data = {
            "dataset_id": sample_dataset.id,
            "consumer_name": "Test Consumer",
            "consumer_email": "consumer@example.com",
            "consumer_organization": "Test Org",
            "business_justification": "Testing",
            "sla_requirements": {"availability": "99.9%"}
        }
        create_response = client.post("/api/v1/subscriptions/", json=subscription_data)
        subscription_id = create_response.json()["id"]

        # Mock contract service
        mock_service_instance = MagicMock()
        mock_service_instance.add_subscription_to_contract.return_value = MagicMock(id=1)
        mock_contract_service.return_value = mock_service_instance

        # Approve subscription
        approval_data = {
            "status": "approved",
            "access_credentials": {
                "username": "consumer1",
                "api_key": "test-api-key-123",
                "connection_string": "postgresql://localhost/test"
            },
            "approved_fields": ["customer_id", "email"]
        }

        response = client.post(
            f"/api/v1/subscriptions/{subscription_id}/approve",
            json=approval_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "approved"
        assert data["access_granted"] is True
        assert data["approved_at"] is not None

    def test_approve_subscription_not_pending(self, client, sample_dataset):
        """Test that only pending subscriptions can be approved."""
        # Create and approve subscription
        subscription_data = {
            "dataset_id": sample_dataset.id,
            "consumer_name": "Test",
            "consumer_email": "test@example.com",
            "consumer_organization": "Test Org",
            "business_justification": "Testing"
        }
        create_response = client.post("/api/v1/subscriptions/", json=subscription_data)
        subscription_id = create_response.json()["id"]

        # Approve once
        approval_data = {"status": "approved", "approved_fields": []}
        client.post(f"/api/v1/subscriptions/{subscription_id}/approve", json=approval_data)

        # Try to approve again
        response = client.post(
            f"/api/v1/subscriptions/{subscription_id}/approve",
            json=approval_data
        )
        assert response.status_code == 400
        assert "not pending" in response.json()["detail"]

    def test_reject_subscription(self, client, sample_dataset):
        """Test rejecting a subscription request."""
        # Create subscription
        subscription_data = {
            "dataset_id": sample_dataset.id,
            "consumer_name": "Test Consumer",
            "consumer_email": "consumer@example.com",
            "consumer_organization": "Test Org",
            "business_justification": "Testing"
        }
        create_response = client.post("/api/v1/subscriptions/", json=subscription_data)
        subscription_id = create_response.json()["id"]

        # Reject subscription
        rejection_data = {
            "status": "rejected",
            "reviewer_notes": "Does not meet security requirements"
        }

        response = client.post(
            f"/api/v1/subscriptions/{subscription_id}/approve",
            json=rejection_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "rejected"
        assert data["access_granted"] is False
        assert "security requirements" in data["rejection_reason"]

    def test_update_subscription(self, client, sample_dataset):
        """Test updating a pending subscription."""
        # Create subscription
        subscription_data = {
            "dataset_id": sample_dataset.id,
            "consumer_name": "Test Consumer",
            "consumer_email": "consumer@example.com",
            "consumer_organization": "Test Org",
            "business_justification": "Initial reason"
        }
        create_response = client.post("/api/v1/subscriptions/", json=subscription_data)
        subscription_id = create_response.json()["id"]

        # Update subscription
        update_data = {
            "purpose": "Updated business justification"
        }

        response = client.put(f"/api/v1/subscriptions/{subscription_id}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["purpose"] == "Updated business justification"

    def test_update_subscription_not_pending(self, client, sample_dataset):
        """Test that approved subscriptions cannot be updated."""
        # Create and approve subscription
        subscription_data = {
            "dataset_id": sample_dataset.id,
            "consumer_name": "Test",
            "consumer_email": "test@example.com",
            "consumer_organization": "Test Org",
            "business_justification": "Testing"
        }
        create_response = client.post("/api/v1/subscriptions/", json=subscription_data)
        subscription_id = create_response.json()["id"]

        # Approve
        approval_data = {"status": "approved", "approved_fields": []}
        client.post(f"/api/v1/subscriptions/{subscription_id}/approve", json=approval_data)

        # Try to update
        update_data = {"purpose": "New reason"}
        response = client.put(f"/api/v1/subscriptions/{subscription_id}", json=update_data)
        assert response.status_code == 400
        assert "pending" in response.json()["detail"]

    def test_cancel_subscription(self, client, sample_dataset):
        """Test cancelling a subscription."""
        # Create subscription
        subscription_data = {
            "dataset_id": sample_dataset.id,
            "consumer_name": "Test Consumer",
            "consumer_email": "consumer@example.com",
            "consumer_organization": "Test Org",
            "business_justification": "Testing"
        }
        create_response = client.post("/api/v1/subscriptions/", json=subscription_data)
        subscription_id = create_response.json()["id"]

        # Cancel subscription
        response = client.delete(f"/api/v1/subscriptions/{subscription_id}")
        assert response.status_code == 204

        # Verify it's cancelled
        get_response = client.get(f"/api/v1/subscriptions/{subscription_id}")
        assert get_response.json()["status"] == "cancelled"

    def test_cancel_subscription_not_found(self, client):
        """Test cancelling a non-existent subscription."""
        response = client.delete("/api/v1/subscriptions/99999")
        assert response.status_code == 404

    def test_subscription_stores_sla_requirements(self, client, sample_dataset):
        """Test that SLA requirements are stored correctly."""
        subscription_data = {
            "dataset_id": sample_dataset.id,
            "consumer_name": "Test Consumer",
            "consumer_email": "consumer@example.com",
            "consumer_organization": "Test Org",
            "business_justification": "Testing",
            "sla_requirements": {
                "availability": "99.99%",
                "latency": "< 50ms",
                "throughput": "1000 req/s"
            },
            "required_fields": ["id", "name", "email"],
            "access_duration_days": 180
        }

        response = client.post("/api/v1/subscriptions/", json=subscription_data)
        assert response.status_code == 201
        data = response.json()

        # Check that SLA data is stored
        assert data["data_filters"] is not None
        assert "sla_requirements" in data["data_filters"]
        assert data["data_filters"]["sla_requirements"]["availability"] == "99.99%"
        assert data["data_filters"]["required_fields"] == ["id", "name", "email"]
        assert data["data_filters"]["access_duration_days"] == 180

    def test_subscription_expiration_date(self, client, sample_dataset):
        """Test that expiration date is set correctly on approval."""
        # Create subscription
        subscription_data = {
            "dataset_id": sample_dataset.id,
            "consumer_name": "Test Consumer",
            "consumer_email": "consumer@example.com",
            "consumer_organization": "Test Org",
            "business_justification": "Testing",
            "access_duration_days": 90
        }
        create_response = client.post("/api/v1/subscriptions/", json=subscription_data)
        subscription_id = create_response.json()["id"]

        # Approve subscription
        approval_data = {
            "status": "approved",
            "approved_fields": []
        }

        response = client.post(
            f"/api/v1/subscriptions/{subscription_id}/approve",
            json=approval_data
        )
        assert response.status_code == 200
        data = response.json()

        # Check expiration date (should be ~90 days from now)
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(data["expires_at"].replace("Z", "+00:00"))
            now = datetime.now(expires_at.tzinfo)
            days_until_expiry = (expires_at - now).days
            assert 85 <= days_until_expiry <= 95  # Allow some tolerance

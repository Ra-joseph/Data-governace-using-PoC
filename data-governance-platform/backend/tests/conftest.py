"""
Pytest configuration and fixtures for testing.
"""
import pytest
import sys
from pathlib import Path
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app
from app.database import Base, get_db
from app.models.dataset import Dataset
from app.models.contract import Contract
from app.models.subscription import Subscription


# Test database engine (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db() -> Generator[Session, None, None]:
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session) -> Generator[TestClient, None, None]:
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_schema():
    """Sample schema definition for testing."""
    return [
        {
            "name": "customer_id",
            "type": "integer",
            "description": "Unique customer identifier",
            "required": True,
            "nullable": False,
            "pii": False
        },
        {
            "name": "email",
            "type": "string",
            "description": "Customer email address",
            "required": True,
            "nullable": False,
            "pii": True,
            "max_length": 255
        },
        {
            "name": "created_at",
            "type": "timestamp",
            "description": "Account creation timestamp",
            "required": True,
            "nullable": False,
            "pii": False
        }
    ]


@pytest.fixture
def sample_dataset(db: Session, sample_schema):
    """Create a sample dataset for testing."""
    dataset = Dataset(
        name="test_customers",
        description="Test customer dataset",
        owner_name="John Doe",
        owner_email="john@example.com",
        source_type="postgres",
        source_connection="postgresql://localhost/test",
        physical_location="public.customers",
        schema_definition=sample_schema,
        classification="internal",
        contains_pii=True,
        compliance_tags=["GDPR"],
        status="draft"
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


@pytest.fixture
def sample_contract_data():
    """Sample contract data for testing."""
    return {
        "version": "1.0.0",
        "dataset": {
            "name": "customer_accounts",
            "description": "Customer account information",
            "owner_name": "John Doe",
            "owner_email": "john.doe@company.com",
            "classification": "confidential"
        },
        "schema": [
            {
                "name": "account_id",
                "type": "integer",
                "description": "Account ID",
                "required": True,
                "nullable": False,
                "pii": False
            },
            {
                "name": "email",
                "type": "string",
                "description": "Email address",
                "required": True,
                "nullable": False,
                "pii": True,
                "max_length": 255
            },
            {
                "name": "created_at",
                "type": "timestamp",
                "description": "Creation date",
                "required": False,
                "nullable": True,
                "pii": False
            }
        ],
        "governance": {
            "classification": "confidential",
            "encryption_required": True,
            "retention_days": 2555,
            "compliance_tags": ["GDPR", "CCPA"],
            "approved_use_cases": ["customer_service"]
        },
        "quality_rules": {
            "completeness_threshold": 99,
            "freshness_sla": "24h",
            "uniqueness_fields": ["account_id"]
        }
    }


@pytest.fixture
def sample_contract_with_violations():
    """Sample contract data with intentional policy violations."""
    return {
        "version": "1.0.0",
        "dataset": {
            "name": "customer_accounts",
            "description": "Customer account information",
            # Missing owner_name and owner_email (SG003 violation)
        },
        "schema": [
            {
                "name": "account_id",
                "type": "integer",
                # Missing description (SG001 violation)
                "required": True,
                "nullable": True,  # Inconsistent (SG002 violation)
                "pii": False
            },
            {
                "name": "ssn",
                "type": "string",
                # Missing description (SG001 violation)
                # Missing max_length (SG004 violation)
                "required": True,
                "nullable": False,
                "pii": True
            }
        ],
        "governance": {
            "classification": "confidential",
            # Missing encryption_required (SD001 violation)
            # Missing retention_days (SD002 violation)
            # Missing compliance_tags (SD003 violation)
        },
        "quality_rules": {
            "completeness_threshold": 80,  # Too low (DQ001 violation)
            # Missing freshness_sla (DQ002 violation)
            # Missing uniqueness_fields (DQ003 violation)
        }
    }


@pytest.fixture
def mock_postgres_tables():
    """Mock PostgreSQL table information."""
    return [
        {
            "table_name": "customers",
            "table_type": "BASE TABLE",
            "schema_name": "public"
        },
        {
            "table_name": "orders",
            "table_type": "BASE TABLE",
            "schema_name": "public"
        },
        {
            "table_name": "products",
            "table_type": "BASE TABLE",
            "schema_name": "public"
        }
    ]

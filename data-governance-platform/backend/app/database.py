"""
Database configuration and session management.

This module sets up SQLAlchemy database connections, session management,
and provides utilities for database initialization. It configures both
SQLite for metadata storage and provides dependency injection for
database sessions in FastAPI endpoints.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create SQLAlchemy engine
engine = create_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.SQLALCHEMY_DATABASE_URL else {}
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()


def get_db():
    """
    Get database session for dependency injection.

    Creates a new database session for each request and ensures
    proper cleanup after the request is complete. Use this as a
    FastAPI dependency for endpoints that need database access.

    Yields:
        Session: SQLAlchemy database session.

    Example:
        >>> @app.get("/items")
        >>> def get_items(db: Session = Depends(get_db)):
        ...     return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database tables and seed sample data if empty.

    Creates all database tables defined in models if they don't exist.
    On first run, populates the database with sample datasets and contracts
    so the platform is usable out of the box.

    Note:
        This function imports models to ensure they are registered with
        SQLAlchemy before creating tables.
    """
    from app.models import dataset, contract, subscription, user
    from app.models import policy_draft, policy_version, policy_artifact, policy_approval_log
    Base.metadata.create_all(bind=engine)

    # Seed sample data if the datasets table is empty
    db = SessionLocal()
    try:
        if db.query(dataset.Dataset).count() == 0:
            _seed_sample_data(db)
    finally:
        db.close()


def _seed_sample_data(db):
    """Populate the database with sample datasets and contracts for demo purposes."""
    import hashlib
    import json
    import yaml
    from datetime import datetime
    from app.models.dataset import Dataset
    from app.models.contract import Contract

    samples = [
        {
            "name": "customer_accounts",
            "description": "Core customer account data including profile, contact details, and account status.",
            "owner_name": "Alice Chen",
            "owner_email": "alice.chen@company.com",
            "source_type": "postgres",
            "physical_location": "analytics.public.customer_accounts",
            "classification": "confidential",
            "contains_pii": True,
            "compliance_tags": ["GDPR", "CCPA"],
            "schema": [
                {"name": "customer_id", "type": "integer", "description": "Unique customer identifier", "required": True, "nullable": False, "pii": False},
                {"name": "full_name", "type": "string", "description": "Customer full name", "required": True, "nullable": False, "pii": True, "max_length": 255},
                {"name": "email", "type": "string", "description": "Customer email address", "required": True, "nullable": False, "pii": True, "max_length": 255},
                {"name": "phone", "type": "string", "description": "Customer phone number", "required": False, "nullable": True, "pii": True, "max_length": 20},
                {"name": "account_status", "type": "string", "description": "Account status (active/suspended/closed)", "required": True, "nullable": False, "pii": False},
                {"name": "created_at", "type": "timestamp", "description": "Account creation timestamp", "required": True, "nullable": False, "pii": False},
            ],
        },
        {
            "name": "transaction_ledger",
            "description": "Financial transaction records with amounts, parties, and settlement status.",
            "owner_name": "Bob Martinez",
            "owner_email": "bob.martinez@company.com",
            "source_type": "postgres",
            "physical_location": "finance.public.transactions",
            "classification": "restricted",
            "contains_pii": False,
            "compliance_tags": ["SOX", "PCI-DSS"],
            "schema": [
                {"name": "txn_id", "type": "string", "description": "Transaction UUID", "required": True, "nullable": False, "pii": False},
                {"name": "account_id", "type": "integer", "description": "Source account ID", "required": True, "nullable": False, "pii": False},
                {"name": "amount", "type": "decimal", "description": "Transaction amount in USD", "required": True, "nullable": False, "pii": False},
                {"name": "currency", "type": "string", "description": "ISO 4217 currency code", "required": True, "nullable": False, "pii": False, "max_length": 3},
                {"name": "txn_type", "type": "string", "description": "Type: credit/debit/transfer", "required": True, "nullable": False, "pii": False},
                {"name": "status", "type": "string", "description": "Settlement status", "required": True, "nullable": False, "pii": False},
                {"name": "processed_at", "type": "timestamp", "description": "Processing timestamp", "required": True, "nullable": False, "pii": False},
            ],
        },
        {
            "name": "product_catalog",
            "description": "Product catalog with pricing, categories, and inventory levels.",
            "owner_name": "Carol Oduya",
            "owner_email": "carol.oduya@company.com",
            "source_type": "postgres",
            "physical_location": "commerce.public.products",
            "classification": "internal",
            "contains_pii": False,
            "compliance_tags": [],
            "schema": [
                {"name": "product_id", "type": "integer", "description": "Product identifier", "required": True, "nullable": False, "pii": False},
                {"name": "sku", "type": "string", "description": "Stock keeping unit", "required": True, "nullable": False, "pii": False, "max_length": 50},
                {"name": "name", "type": "string", "description": "Product display name", "required": True, "nullable": False, "pii": False, "max_length": 255},
                {"name": "category", "type": "string", "description": "Product category", "required": True, "nullable": False, "pii": False},
                {"name": "price", "type": "decimal", "description": "Unit price in USD", "required": True, "nullable": False, "pii": False},
                {"name": "stock_qty", "type": "integer", "description": "Current inventory count", "required": True, "nullable": False, "pii": False},
                {"name": "updated_at", "type": "timestamp", "description": "Last update timestamp", "required": True, "nullable": False, "pii": False},
            ],
        },
        {
            "name": "employee_directory",
            "description": "Internal employee records with department, role, and contact information.",
            "owner_name": "Diana Park",
            "owner_email": "diana.park@company.com",
            "source_type": "postgres",
            "physical_location": "hr.public.employees",
            "classification": "confidential",
            "contains_pii": True,
            "compliance_tags": ["GDPR"],
            "schema": [
                {"name": "employee_id", "type": "integer", "description": "Employee identifier", "required": True, "nullable": False, "pii": False},
                {"name": "full_name", "type": "string", "description": "Employee full name", "required": True, "nullable": False, "pii": True, "max_length": 255},
                {"name": "email", "type": "string", "description": "Corporate email", "required": True, "nullable": False, "pii": True, "max_length": 255},
                {"name": "department", "type": "string", "description": "Department name", "required": True, "nullable": False, "pii": False},
                {"name": "role", "type": "string", "description": "Job title", "required": True, "nullable": False, "pii": False},
                {"name": "hire_date", "type": "date", "description": "Date of hire", "required": True, "nullable": False, "pii": False},
            ],
        },
        {
            "name": "web_analytics_events",
            "description": "Clickstream and event tracking data from the customer-facing web application.",
            "owner_name": "Evan Torres",
            "owner_email": "evan.torres@company.com",
            "source_type": "postgres",
            "physical_location": "analytics.public.events",
            "classification": "internal",
            "contains_pii": False,
            "compliance_tags": ["GDPR"],
            "schema": [
                {"name": "event_id", "type": "string", "description": "Event UUID", "required": True, "nullable": False, "pii": False},
                {"name": "session_id", "type": "string", "description": "Browser session ID", "required": True, "nullable": False, "pii": False},
                {"name": "event_type", "type": "string", "description": "Event type (page_view, click, purchase)", "required": True, "nullable": False, "pii": False},
                {"name": "page_url", "type": "string", "description": "Page URL", "required": True, "nullable": False, "pii": False, "max_length": 2000},
                {"name": "timestamp", "type": "timestamp", "description": "Event timestamp (UTC)", "required": True, "nullable": False, "pii": False},
            ],
        },
    ]

    for s in samples:
        ds = Dataset(
            name=s["name"],
            description=s["description"],
            owner_name=s["owner_name"],
            owner_email=s["owner_email"],
            source_type=s["source_type"],
            physical_location=s["physical_location"],
            schema_definition=s["schema"],
            classification=s["classification"],
            contains_pii=s["contains_pii"],
            compliance_tags=s["compliance_tags"],
            status="published",
            is_active=True,
        )
        db.add(ds)
        db.flush()

        # Build a contract for this dataset
        machine_readable = {
            "version": "1.0.0",
            "dataset": {
                "name": s["name"],
                "description": s["description"],
                "owner_name": s["owner_name"],
                "owner_email": s["owner_email"],
                "classification": s["classification"],
            },
            "schema": s["schema"],
            "governance": {
                "classification": s["classification"],
                "encryption_required": s["classification"] in ("confidential", "restricted"),
                "retention_days": 2555,
                "compliance_tags": s["compliance_tags"],
                "approved_use_cases": ["analytics", "reporting"],
            },
            "quality_rules": {
                "completeness_threshold": 95,
                "freshness_sla": "24h",
                "uniqueness_fields": [s["schema"][0]["name"]],
            },
        }

        human_readable = yaml.dump(machine_readable, default_flow_style=False, sort_keys=False)
        schema_hash = hashlib.sha256(json.dumps(s["schema"], sort_keys=True).encode()).hexdigest()

        ct = Contract(
            dataset_id=ds.id,
            version="1.0.0",
            human_readable=human_readable,
            machine_readable=machine_readable,
            schema_hash=schema_hash,
            governance_rules=machine_readable["governance"],
            quality_rules=machine_readable["quality_rules"],
            validation_status="passed",
            validation_results={"status": "passed", "passed": 5, "failures": 0, "warnings": 0, "violations": []},
            last_validated_at=datetime.utcnow(),
        )
        db.add(ct)

    db.commit()
    print(f"Seeded {len(samples)} sample datasets with contracts.")

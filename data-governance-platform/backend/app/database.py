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
    Initialize database tables.

    Creates all database tables defined in models if they don't exist.
    This function is called during application startup to ensure the
    database schema is properly initialized.

    Note:
        This function imports models to ensure they are registered with
        SQLAlchemy before creating tables.
    """
    from app.models import dataset, contract, subscription, user
    from app.models import policy_draft, policy_version, policy_artifact, policy_approval_log
    Base.metadata.create_all(bind=engine)

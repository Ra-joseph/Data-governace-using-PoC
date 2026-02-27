"""
Application configuration settings.

This module defines all configuration settings for the Data Governance Platform
using Pydantic BaseSettings. Settings can be overridden via environment variables
or a .env file. Includes database connections, API settings, Git configuration,
and external service credentials.
"""

import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve database path relative to the backend directory so it works
# regardless of the working directory the app is started from.
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_DB_PATH = _BACKEND_DIR / "governance_metadata.db"


class Settings(BaseSettings):
    """
    Application configuration settings.

    Configuration class for the Data Governance Platform. All settings can be
    overridden via environment variables or a .env file. Settings are validated
    using Pydantic and loaded at application startup.

    Attributes:
        APP_NAME: Application name displayed in API docs.
        APP_VERSION: Current version following semantic versioning.
        DEBUG: Enable debug mode for development.
        API_V1_PREFIX: API version prefix for all endpoints.
        SQLALCHEMY_DATABASE_URL: SQLite database URL for metadata storage.
        POSTGRES_HOST: PostgreSQL host for demo database.
        POSTGRES_PORT: PostgreSQL port number.
        POSTGRES_DB: PostgreSQL database name.
        POSTGRES_USER: PostgreSQL username.
        POSTGRES_PASSWORD: PostgreSQL password.
        GIT_CONTRACTS_REPO_PATH: Path to Git repository for contracts.
        GIT_USER_NAME: Git commit author name.
        GIT_USER_EMAIL: Git commit author email.
        POLICIES_PATH: Path to YAML policy definitions.
        CORS_ORIGINS: List of allowed CORS origins.

    Example:
        >>> settings = Settings()
        >>> print(settings.postgres_connection_string)
        postgresql://user:pass@localhost:5432/db
    """
    
    # Application Settings
    APP_NAME: str = "Data Governance Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Database - SQLite for metadata
    SQLALCHEMY_DATABASE_URL: str = f"sqlite:///{_DB_PATH}"
    
    # PostgreSQL - Demo Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "financial_demo"
    POSTGRES_USER: str = "governance_user"
    POSTGRES_PASSWORD: str = "governance_pass"
    
    # Azure (Optional - for future use)
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_ACCOUNT_NAME: str = ""
    AZURE_STORAGE_ACCOUNT_KEY: str = ""
    AZURE_TENANT_ID: str = ""
    AZURE_CLIENT_ID: str = ""
    AZURE_CLIENT_SECRET: str = ""
    
    # Git
    GIT_CONTRACTS_REPO_PATH: str = "./backend/contracts"
    GIT_USER_NAME: str = "Data Governance Platform"
    GIT_USER_EMAIL: str = "governance@company.com"
    
    # Policies
    POLICIES_PATH: str = "./backend/policies"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )
    
    @property
    def postgres_connection_string(self) -> str:
        """
        Generate PostgreSQL connection string.

        Constructs a PostgreSQL connection string from individual configuration
        values for use with SQLAlchemy or psycopg2.

        Returns:
            str: PostgreSQL connection string in the format
                 postgresql://user:password@host:port/database
        """
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()

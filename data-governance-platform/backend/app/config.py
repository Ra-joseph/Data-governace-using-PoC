from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration settings."""
    
    # Application Settings
    APP_NAME: str = "Data Governance Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    # Database - SQLite for metadata
    SQLALCHEMY_DATABASE_URL: str = "sqlite:///./governance_metadata.db"
    
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
        """Generate PostgreSQL connection string."""
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()

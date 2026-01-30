"""
Configuration settings using Pydantic.
"""
from pydantic import BaseSettings, Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # PostgreSQL Configuration
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="customs_kb", env="POSTGRES_DB")
    postgres_user: str = Field(default="customs_user", env="POSTGRES_USER")
    postgres_password: str = Field(default="customs_pass", env="POSTGRES_PASSWORD")

    # Qdrant Configuration
    qdrant_host: str = Field(default="localhost", env="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, env="QDRANT_PORT")
    qdrant_collection: str = Field(default="cbp_documents", env="QDRANT_COLLECTION")

    # Embedding Model
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        env="EMBEDDING_MODEL"
    )
    embedding_dimension: int = Field(default=384, env="EMBEDDING_DIMENSION")
    chunk_size: int = Field(default=512, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=50, env="CHUNK_OVERLAP")

    # Federal Register API
    federal_register_base_url: str = Field(
        default="https://www.federalregister.gov/api/v1",
        env="FEDERAL_REGISTER_BASE_URL"
    )
    federal_register_agency: str = Field(
        default="u-s-customs-and-border-protection",
        env="FEDERAL_REGISTER_AGENCY"
    )

    # Ingestion Settings
    batch_size: int = Field(default=32, env="BATCH_SIZE")
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    retry_delay: int = Field(default=1, env="RETRY_DELAY")

    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    @property
    def postgres_url(self) -> str:
        """Get PostgreSQL connection URL."""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def qdrant_url(self) -> str:
        """Get Qdrant connection URL."""
        return f"http://{self.qdrant_host}:{self.qdrant_port}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Global settings instance
settings = Settings()

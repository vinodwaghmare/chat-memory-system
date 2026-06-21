from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All application configuration in one place."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Database — PostgreSQL with pgvector
    # -------------------------------------------------------------------------
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/memory_system"

    # -------------------------------------------------------------------------
    # Redis — session memory, caching
    # -------------------------------------------------------------------------
    redis_url: str = "redis://localhost:6379/0"

    # -------------------------------------------------------------------------
    # LLM Providers
    # -------------------------------------------------------------------------
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    openai_embedding_model: str = "text-embedding-3-small"
    openai_embedding_dimensions: int = 1536

    # -------------------------------------------------------------------------
    # Application
    # -------------------------------------------------------------------------
    app_env: str = "development"
    log_level: str = "INFO"
    max_memories_per_user: int = 10000

    # -------------------------------------------------------------------------
    # Retrieval Weights (must sum to 1.0)
    # -------------------------------------------------------------------------
    semantic_weight: float = 0.4
    recency_weight: float = 0.2
    frequency_weight: float = 0.2
    importance_weight: float = 0.2
    retrieval_top_k: int = 10

    # -------------------------------------------------------------------------
    # Decay
    # -------------------------------------------------------------------------
    decay_factor: float = Field(default=0.95, ge=0.0, le=1.0)
    archive_threshold: float = Field(default=0.1, ge=0.0, le=1.0)
    decay_schedule_hours: int = 24

    # -------------------------------------------------------------------------
    # API Authentication
    # -------------------------------------------------------------------------
    api_key: str = "dev-api-key-change-in-production"

    # -------------------------------------------------------------------------
    # Derived properties
    # -------------------------------------------------------------------------
    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"


@lru_cache()
def get_settings() -> Settings:
    return Settings()

"""Centralized, environment-based application configuration.

All tunables live here with sensible defaults so the service runs locally
with zero configuration, while every value remains overridable via
environment variables (or a local .env file) in any deployment.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "local"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg2://batch:batch@localhost:5432/batch"

    # Submission limits: protects the API from unbounded request bodies / table scans.
    max_batch_size: int = 1000
    default_page_size: int = 50
    max_page_size: int = 200

    # Worker tuning.
    worker_poll_interval_seconds: float = 1.0
    worker_claim_batch_size: int = 10
    worker_max_item_attempts: int = 3


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Cached so env parsing happens once per process; tests override via
    dependency-overrides or by calling get_settings.cache_clear().
    """
    return Settings()

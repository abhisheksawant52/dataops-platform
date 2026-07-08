"""Application configuration loaded from the environment.

Settings are read from ``DATAOPS_``-prefixed environment variables (and an
optional ``.env`` file), so the service can be configured without code changes
across local, staging, and production environments.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the DataOps platform."""

    model_config = SettingsConfigDict(
        env_prefix="DATAOPS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Connectivity
    db_url: str = "sqlite:///dataops.db"
    warehouse: str = "local"

    # Environment metadata
    env: str = "development"
    log_level: str = "INFO"

    # Data quality gate: fraction of rules (0.0-1.0) allowed to fail before a
    # quality report is considered failed.
    quality_fail_threshold: float = 0.0


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()

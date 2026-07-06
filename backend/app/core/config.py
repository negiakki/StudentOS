"""Application configuration.

All settings are loaded from environment variables (or a local `.env` file).
The AI provider layer is intentionally config-driven so providers can be
swapped without code changes (Docs/03_System_Architecture.md §13).
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "StudentOS API"
    environment: str = "development"
    debug: bool = True

    # Comma-separated list of allowed CORS origins.
    cors_origins: str = "http://localhost:3000"

    # --- Database (Supabase Postgres); wired up in Phase 3 ---
    database_url: str = ""

    # --- Supabase Auth; wired up in Phase 2 ---
    supabase_url: str = ""
    supabase_jwt_secret: str = ""

    # --- AI provider layer; wired up in Phase 9 ---
    ai_provider: str = "gemini"
    gemini_api_key: str = ""
    watsonx_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor so the env is parsed only once."""
    return Settings()

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

    # --- Supabase Auth ---
    supabase_url: str = ""
    # Legacy HS256 shared secret. Optional: only used as a fallback when the
    # project still signs JWTs symmetrically. Asymmetric (JWKS) is preferred.
    supabase_jwt_secret: str = ""
    # Expected audience claim on Supabase access tokens.
    supabase_jwt_audience: str = "authenticated"

    # --- AI provider layer; wired up in Phase 9 ---
    ai_provider: str = "gemini"
    gemini_api_key: str = ""
    watsonx_api_key: str = ""

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def supabase_auth_url(self) -> str:
        """Base URL of the Supabase Auth (GoTrue) service."""
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    @property
    def supabase_jwt_issuer(self) -> str:
        """Expected `iss` claim on Supabase access tokens."""
        return self.supabase_auth_url

    @property
    def supabase_jwks_url(self) -> str:
        """JWKS endpoint exposing the project's asymmetric public signing keys."""
        return f"{self.supabase_auth_url}/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor so the env is parsed only once."""
    return Settings()

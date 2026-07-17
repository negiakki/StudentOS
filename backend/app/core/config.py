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

    # --- Supabase Storage (timetable uploads; Phase 4) ---
    # Service-role key: server-side only, bypasses RLS for storage writes. Never
    # expose to the frontend. Files are namespaced per user so access stays scoped.
    supabase_service_role_key: str = ""
    supabase_storage_bucket: str = "timetables"
    # Reject uploads larger than this (defense-in-depth alongside the parser).
    max_upload_bytes: int = 10 * 1024 * 1024  # 10 MB

    # --- AI provider layer (Phase 4.5) ---
    # The app talks only to the routers (app/ai/routers); provider choice is
    # configuration, never hard-coded. Selection is by these two switches.
    vision_provider: str = "gemini"
    chat_provider: str = "openrouter"

    gemini_api_key: str = ""
    # Vision-capable model used to extract timetable structure from an upload.
    gemini_model: str = "gemini-2.0-flash"

    openrouter_api_key: str = ""
    # Default chat model on OpenRouter (used from Phase 6).
    openrouter_model: str = "openai/gpt-4o-mini"
    # OpenRouter API base; override only for proxies or compatible gateways.
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    watsonx_api_key: str = ""

    # Master switch for automatic timetable parsing. V1 ships storage-only:
    # upload is instant and no AI provider is called. Flip to true in V2 to
    # re-enable the parse → preview → confirm flow (all code is preserved).
    enable_timetable_parsing: bool = False

    # Deprecated alias kept for backwards compatibility with earlier config.
    # Prefer `vision_provider` / `chat_provider`. Unused by the router layer.
    ai_provider: str = "gemini"

    @property
    def supabase_storage_url(self) -> str:
        """Base URL of the Supabase Storage REST API."""
        return f"{self.supabase_url.rstrip('/')}/storage/v1"

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

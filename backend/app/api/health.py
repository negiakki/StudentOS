"""Health check endpoint.

Used by uptime probes (Render) and as a smoke test that the app boots.
Kept free of auth and database access so it always reflects process liveness.
"""

from fastapi import APIRouter

from app import __version__
from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": __version__,
        "environment": settings.environment,
    }

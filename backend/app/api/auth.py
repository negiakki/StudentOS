"""Auth endpoints.

Supabase handles sign-up / sign-in / password reset directly from the frontend,
so the backend exposes only what it uniquely can: confirming who the caller is
from their verified token. This doubles as a smoke test that JWT verification is
wired correctly end-to-end.
"""

from fastapi import APIRouter

from app.api.deps import CurrentUserDep
from app.schemas.auth import CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=CurrentUser)
def read_current_user(current_user: CurrentUserDep) -> CurrentUser:
    """Return the authenticated user derived from the Supabase access token."""
    return current_user

"""Shared FastAPI dependencies.

`get_current_user` is the auth gate for protected endpoints: it extracts the
Bearer token, verifies it (Supabase JWKS / HS256), and returns the identity.
Routes depend on it rather than parsing tokens themselves.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import AuthError, verify_token
from app.schemas.auth import CurrentUser

# auto_error=False so we can return a clean 401 with a WWW-Authenticate header
# instead of FastAPI's default 403 when the header is absent.
_bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
) -> CurrentUser:
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = verify_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    return CurrentUser.from_claims(claims)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]

"""Auth-related API schemas."""

from __future__ import annotations

from pydantic import BaseModel


class CurrentUser(BaseModel):
    """The authenticated user, derived from a verified Supabase access token.

    `id` is the Supabase Auth user id (JWT `sub`) and is the same UUID used as the
    primary key of the StudentOS `users` table (Docs/04_Database_Design.md §4).
    The email arrives already validated by Supabase, so it needs no re-validation.
    """

    id: str
    email: str | None = None
    role: str | None = None

    @classmethod
    def from_claims(cls, claims: dict) -> "CurrentUser":
        return cls(
            id=claims["sub"],
            email=claims.get("email"),
            role=claims.get("role"),
        )

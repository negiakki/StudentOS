"""User profile service.

Business logic that bridges Supabase Auth and the StudentOS database: on first
authenticated request we lazily create the local profile row (keyed by the
Supabase user id) plus default settings. Services own logic; they delegate all
persistence to repositories (Docs/03_System_Architecture.md §7).
"""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.user import Settings, User
from app.repositories.user_repository import SettingsRepository, UserRepository
from app.schemas.auth import CurrentUser


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.users = UserRepository(db)
        self.settings = SettingsRepository(db)

    def get_or_create_profile(self, current_user: CurrentUser) -> User:
        """Return the StudentOS profile for the authenticated user, creating it
        (with default settings) on first sign-in."""
        user_id = uuid.UUID(current_user.id)

        user = self.users.get(user_id)
        if user is not None:
            return user

        user = User(
            id=user_id,
            email=current_user.email or "",
            onboarding_completed=False,
        )
        self.users.add(user)
        self.settings.add(Settings(user_id=user_id))
        return user

    def complete_onboarding(
        self,
        current_user: CurrentUser,
        *,
        full_name: str | None = None,
        college: str | None = None,
        degree: str | None = None,
    ) -> User:
        """Persist onboarding profile details and mark onboarding complete."""
        user = self.get_or_create_profile(current_user)
        if full_name is not None:
            user.full_name = full_name
        if college is not None:
            user.college = college
        if degree is not None:
            user.degree = degree
        user.onboarding_completed = True
        self.db.flush()
        return user

"""User and settings repositories."""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.user import Settings, User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    model = User

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))


class SettingsRepository(BaseRepository[Settings]):
    model = Settings

    def get_for_user(self, user_id: uuid.UUID) -> Settings | None:
        return self.db.scalar(select(Settings).where(Settings.user_id == user_id))

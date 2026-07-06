"""Base repository.

Repositories are the only layer that touches the database. They read and write
data and never perform calculations or business logic (Docs/03_System_Architecture.md
§8). Concrete repositories subclass this with a specific model.
"""

from __future__ import annotations

import uuid
from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, id_: uuid.UUID) -> ModelT | None:
        return self.db.get(self.model, id_)

    def list(self) -> list[ModelT]:
        return list(self.db.scalars(select(self.model)))

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()  # assign PKs/defaults without ending the transaction
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()


class UserScopedRepository(BaseRepository[ModelT]):
    """For tables with a `user_id` column. Every query is constrained to the
    authenticated user (Docs/04_Database_Design.md §18)."""

    def list_for_user(self, user_id: uuid.UUID) -> list[ModelT]:
        return list(
            self.db.scalars(select(self.model).where(self.model.user_id == user_id))
        )

    def get_for_user(self, id_: uuid.UUID, user_id: uuid.UUID) -> ModelT | None:
        obj = self.db.get(self.model, id_)
        if obj is None or obj.user_id != user_id:
            return None
        return obj

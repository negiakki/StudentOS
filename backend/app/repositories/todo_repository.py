"""Todo data access (Phase 8).

Repositories only read/write data — no calculations, no business logic
(Docs/03_System_Architecture.md §8). `Todo` has its own `user_id` column, so
ownership is enforced directly via `UserScopedRepository`
(Docs/04_Database_Design.md §10, §18).
"""

from __future__ import annotations

from app.models.planning import Todo
from app.repositories.base import UserScopedRepository


class TodoRepository(UserScopedRepository[Todo]):
    model = Todo

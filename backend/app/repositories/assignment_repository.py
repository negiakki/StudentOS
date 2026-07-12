"""Assignment data access (Phase 7).

Repositories only read/write data — no calculations, no business logic
(Docs/03_System_Architecture.md §8). `Assignment` has its own `user_id` column,
so ownership is enforced directly via `UserScopedRepository`
(Docs/04_Database_Design.md §9, §18).
"""

from __future__ import annotations

from app.models.planning import Assignment
from app.repositories.base import UserScopedRepository


class AssignmentRepository(UserScopedRepository[Assignment]):
    model = Assignment

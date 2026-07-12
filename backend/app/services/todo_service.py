"""Todo business logic (Phase 8).

Python performs every calculation; the database stores only raw fields
(Docs/03_System_Architecture.md §5, §16). "Today's tasks" is computed here from
`due_date` and `completed`, never stored.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.planning import Todo
from app.repositories.todo_repository import TodoRepository
from app.schemas.todo import TodoCreate, TodoOut, TodoUpdate


class TodoService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.todos = TodoRepository(db)

    def create(self, *, user_id: uuid.UUID, payload: TodoCreate) -> TodoOut:
        """Add a todo. Always starts incomplete."""
        todo = Todo(
            user_id=user_id,
            title=payload.title.strip(),
            due_date=payload.due_date,
            priority=payload.priority,
            completed=False,
        )
        self.todos.add(todo)
        return self._to_out(todo)

    def list(self, *, user_id: uuid.UUID) -> list[TodoOut]:
        """All of the user's todos, soonest due date first (undated last)."""
        items = self.todos.list_for_user(user_id)
        items.sort(key=self._sort_key)
        return [self._to_out(t) for t in items]

    def get(self, *, user_id: uuid.UUID, todo_id: uuid.UUID) -> TodoOut | None:
        """A single todo. None if not owned/found."""
        todo = self.todos.get_for_user(todo_id, user_id)
        if todo is None:
            return None
        return self._to_out(todo)

    def update(
        self, *, user_id: uuid.UUID, todo_id: uuid.UUID, payload: TodoUpdate
    ) -> TodoOut | None:
        """Edit a todo, including marking it complete/incomplete. None if not
        owned/found."""
        todo = self.todos.get_for_user(todo_id, user_id)
        if todo is None:
            return None

        if payload.title is not None:
            todo.title = payload.title.strip()
        # due_date is nullable and clearable, so apply it whenever the client
        # sent the field at all (even as null) — `is not None` would make it
        # impossible to ever clear it back out.
        if "due_date" in payload.model_fields_set:
            todo.due_date = payload.due_date
        if payload.priority is not None:
            todo.priority = payload.priority
        if payload.completed is not None:
            todo.completed = payload.completed

        self.db.flush()
        return self._to_out(todo)

    def delete(self, *, user_id: uuid.UUID, todo_id: uuid.UUID) -> bool:
        """Delete a todo. Returns False if not owned/found."""
        todo = self.todos.get_for_user(todo_id, user_id)
        if todo is None:
            return False
        self.todos.delete(todo)
        return True

    def today(self, *, user_id: uuid.UUID) -> list[TodoOut]:
        """Incomplete todos that are overdue, due today, or undated — soonest
        due date first (undated last).

        Completed todos have nothing left to act on, so they're excluded.
        Future-dated todos aren't "today's tasks" yet.
        """
        today = date.today()
        items = [
            t
            for t in self.todos.list_for_user(user_id)
            if not t.completed and (t.due_date is None or t.due_date <= today)
        ]
        items.sort(key=self._sort_key)
        return [self._to_out(t) for t in items]

    # --- internals ---

    @staticmethod
    def _sort_key(todo: Todo) -> tuple[bool, date, str]:
        """Soonest due date first; undated todos sort last."""
        return (
            todo.due_date is None,
            todo.due_date or date.max,
            todo.title.lower(),
        )

    @staticmethod
    def _to_out(todo: Todo) -> TodoOut:
        return TodoOut.model_validate(todo)

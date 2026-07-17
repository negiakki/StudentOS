"""Chat message data access (Phase 9, Coco).

Repositories only read/write data — no calculations, no business logic
(Docs/03_System_Architecture.md §8). The `chat_messages` table exists since
Phase 3; this adds the queries Coco needs: the recent context window and the
full history of one conversation, always scoped to the owning user.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from app.models.system import ChatMessage
from app.repositories.base import UserScopedRepository

# Within one exchange both rows share a `func.now()` timestamp, so ties are
# broken by role: "USER" sorts after "COCO" alphabetically, and the user's
# message always precedes Coco's reply chronologically.
_CHRONOLOGICAL = (
    ChatMessage.created_at.asc(),
    ChatMessage.role.desc(),
)


class ChatMessageRepository(UserScopedRepository[ChatMessage]):
    model = ChatMessage

    def list_conversation(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID
    ) -> list[ChatMessage]:
        """All messages of one conversation, oldest first."""
        return list(
            self.db.scalars(
                select(ChatMessage)
                .where(
                    ChatMessage.user_id == user_id,
                    ChatMessage.conversation_id == conversation_id,
                )
                .order_by(*_CHRONOLOGICAL)
            )
        )

    def list_recent(
        self, user_id: uuid.UUID, conversation_id: uuid.UUID, limit: int
    ) -> list[ChatMessage]:
        """The last `limit` messages of one conversation, oldest first."""
        newest_first = self.db.scalars(
            select(ChatMessage)
            .where(
                ChatMessage.user_id == user_id,
                ChatMessage.conversation_id == conversation_id,
            )
            .order_by(ChatMessage.created_at.desc(), ChatMessage.role.asc())
            .limit(limit)
        )
        return list(reversed(list(newest_first)))

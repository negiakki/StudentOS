"""Coco endpoints (Phase 9).

`POST /coco/chat` runs the two-call flow; `GET /coco/history` reloads a
conversation when the panel reopens. Every request is scoped to the
authenticated user (Docs/04_Database_Design.md §18); writes Coco proposes are
executed by the frontend against the existing REST endpoints, never here.
"""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import CurrentUserDep
from app.database.session import get_db
from app.schemas.coco import ChatHistoryOut, ChatIn, ChatOut
from app.services.coco_service import CocoService
from app.services.user_service import UserService

router = APIRouter(prefix="/coco", tags=["coco"])

DbDep = Annotated[Session, Depends(get_db)]


@router.post("/chat", response_model=ChatOut)
def chat(payload: ChatIn, current_user: CurrentUserDep, db: DbDep) -> ChatOut:
    """Send a message to Coco. Degrades to `coco_available: false` (never 5xx)
    when the AI provider is unavailable."""
    user = UserService(db).get_or_create_profile(current_user)
    return CocoService(db).chat(user=user, payload=payload)


@router.get("/history", response_model=ChatHistoryOut)
def history(
    conversation_id: uuid.UUID, current_user: CurrentUserDep, db: DbDep
) -> ChatHistoryOut:
    """All messages of one conversation, oldest first. An unknown or foreign
    conversation id simply yields an empty list."""
    user_id = uuid.UUID(current_user.id)
    messages = CocoService(db).get_history(
        user_id=user_id, conversation_id=conversation_id
    )
    return ChatHistoryOut(conversation_id=conversation_id, messages=messages)

"""OpenRouter provider (chat + vision) — STUB.

Prepared for Phase 6 (Coco), where OpenRouter is the primary chat provider. The
wiring, config, and contracts are in place; the network calls are intentionally
not implemented yet. Both methods fail gracefully so nothing breaks if a caller
selects OpenRouter before it is finished.

To complete in Phase 6: implement `complete()` (and optionally `generate()`)
against the OpenRouter API using `openrouter_api_key` / `openrouter_model`.
"""

from __future__ import annotations

from app.ai.interfaces.chat_provider import ChatProvider, ChatRequest, ChatResult
from app.ai.interfaces.vision_provider import (
    VisionProvider,
    VisionRequest,
    VisionResult,
)
from app.core.config import get_settings

_NOT_IMPLEMENTED = (
    "OpenRouter provider is a stub (planned for Phase 6). "
    "Set the chat provider to a configured provider or complete the integration."
)


class OpenRouterChatProvider(ChatProvider):
    name = "openrouter"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.openrouter_api_key
        self._model = settings.openrouter_model

    @property
    def available(self) -> bool:
        # Stub: never reports itself as ready until the integration lands.
        return False

    def complete(self, request: ChatRequest) -> ChatResult:  # noqa: ARG002
        return ChatResult.failure(_NOT_IMPLEMENTED)


class OpenRouterVisionProvider(VisionProvider):
    """Optional future vision path via OpenRouter. Stub for now."""

    name = "openrouter"

    @property
    def available(self) -> bool:
        return False

    def generate(self, request: VisionRequest) -> VisionResult:  # noqa: ARG002
        return VisionResult.failure(_NOT_IMPLEMENTED)

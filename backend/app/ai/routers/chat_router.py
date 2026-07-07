"""Chat router.

Selects the configured chat provider (`CHAT_PROVIDER`) and exposes a single
`complete()` the application calls. Used from Phase 6 (Coco). Providers are never
imported by application code directly (Docs/03_System_Architecture.md §13).
"""

from __future__ import annotations

from app.ai.interfaces.chat_provider import ChatProvider, ChatRequest, ChatResult
from app.ai.providers.openrouter import OpenRouterChatProvider
from app.core.config import get_settings

# Registry of known chat providers. Add new providers here only.
_CHAT_PROVIDERS: dict[str, type[ChatProvider]] = {
    "openrouter": OpenRouterChatProvider,
}


class ChatRouter:
    def __init__(self, provider: ChatProvider) -> None:
        self._provider = provider

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def available(self) -> bool:
        return self._provider.available

    def complete(self, request: ChatRequest) -> ChatResult:
        """Run a chat request through the selected provider."""
        return self._provider.complete(request)


def get_chat_router() -> ChatRouter:
    """Build the router for the configured chat provider.

    Falls back to OpenRouter (the planned primary) if `CHAT_PROVIDER` is unknown.
    """
    settings = get_settings()
    provider_cls = _CHAT_PROVIDERS.get(
        settings.chat_provider.lower(), OpenRouterChatProvider
    )
    return ChatRouter(provider_cls())

"""OpenRouter provider (chat + vision).

Chat is implemented against the OpenRouter chat-completions API (httpx); it is
the primary chat provider from Phase 9 (Coco). All expected failures — missing
key, network errors, non-2xx responses, malformed payloads — are returned as
`ChatResult.failure(...)` rather than raised (Docs/03_System_Architecture.md §15).

Vision via OpenRouter remains a stub (Gemini is the vision provider).
"""

from __future__ import annotations

from app.ai.interfaces.chat_provider import ChatProvider, ChatRequest, ChatResult
from app.ai.interfaces.vision_provider import (
    VisionProvider,
    VisionRequest,
    VisionResult,
)
from app.core.config import get_settings

_VISION_NOT_IMPLEMENTED = (
    "OpenRouter vision is a stub. Use the configured vision provider (Gemini)."
)

# Generous ceiling for a chat completion; OpenRouter can queue free-tier models.
_REQUEST_TIMEOUT_SECONDS = 60.0


class OpenRouterChatProvider(ChatProvider):
    name = "openrouter"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.openrouter_api_key
        self._model = settings.openrouter_model
        self._base_url = settings.openrouter_base_url.rstrip("/")

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def complete(self, request: ChatRequest) -> ChatResult:
        if not self.available:
            return ChatResult.failure(
                "OpenRouter is not configured (OPENROUTER_API_KEY)."
            )
        if not request.messages:
            return ChatResult.failure("Chat request has no messages.")

        try:
            text = self._complete(request)
        except Exception as exc:  # provider/network error — stay resilient
            return ChatResult.failure(f"OpenRouter request failed: {exc}")

        if not text:
            return ChatResult.failure("OpenRouter returned an empty response.")
        return ChatResult(ok=True, text=text)

    def _complete(self, request: ChatRequest) -> str:
        # Imported lazily to mirror the other providers (app boots regardless).
        import httpx

        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": [
                    {"role": message.role, "content": message.content}
                    for message in request.messages
                ],
                "temperature": request.temperature,
            },
            timeout=_REQUEST_TIMEOUT_SECONDS,
        )
        response.raise_for_status()

        payload = response.json()
        choices = payload.get("choices") or []
        if not choices:
            # OpenRouter reports some failures as 200s with an `error` object.
            error = payload.get("error") or {}
            detail = error.get("message") or "response contained no choices"
            raise ValueError(detail)
        content = (choices[0].get("message") or {}).get("content")
        return (content or "").strip()


class OpenRouterVisionProvider(VisionProvider):
    """Optional future vision path via OpenRouter. Stub for now."""

    name = "openrouter"

    @property
    def available(self) -> bool:
        return False

    def generate(self, request: VisionRequest) -> VisionResult:  # noqa: ARG002
        return VisionResult.failure(_VISION_NOT_IMPLEMENTED)

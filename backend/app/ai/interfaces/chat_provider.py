"""Chat provider interface (port).

A chat provider turns a list of messages into a text reply. Used from Phase 6
(Coco). Callers depend on this via the chat router, never on a concrete provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ChatMessage:
    """One message in a conversation. `role` is "system" | "user" | "assistant"."""

    role: str
    content: str


@dataclass
class ChatRequest:
    """A single chat completion request."""

    messages: list[ChatMessage] = field(default_factory=list)
    temperature: float = 0.7


@dataclass
class ChatResult:
    """Outcome of a chat request. Providers return `ok=False` with an `error`
    instead of raising for expected failures (Docs/03_System_Architecture.md §15)."""

    ok: bool
    text: str = ""
    error: str | None = None

    @classmethod
    def failure(cls, error: str) -> "ChatResult":
        return cls(ok=False, text="", error=error)


class ChatProvider(ABC):
    """Contract for all chat providers (OpenRouter, future Gemini chat, etc.)."""

    name: str = "chat"

    @property
    @abstractmethod
    def available(self) -> bool:
        """True when the provider is configured (e.g. an API key is present)."""

    @abstractmethod
    def complete(self, request: ChatRequest) -> ChatResult:
        """Run the request. Must not raise for expected failures."""

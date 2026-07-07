"""Vision provider interface (port).

A vision provider turns an image/PDF + a text prompt into a text response
(typically JSON we then parse). Providers implement this; callers depend on it
via the vision router, never on a concrete provider.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class VisionRequest:
    """A single vision generation request."""

    content: bytes
    mime_type: str
    prompt: str
    # Ask the provider for a JSON response when supported.
    json_response: bool = True


@dataclass
class VisionResult:
    """Outcome of a vision request. `text` is the raw provider output.

    Providers never raise for expected failures (quota, network, bad response);
    they return `ok=False` with an `error` so the app can degrade gracefully
    (Docs/03_System_Architecture.md §15).
    """

    ok: bool
    text: str = ""
    error: str | None = None

    @classmethod
    def failure(cls, error: str) -> "VisionResult":
        return cls(ok=False, text="", error=error)


class VisionProvider(ABC):
    """Contract for all vision providers (Gemini, future OpenRouter, etc.)."""

    name: str = "vision"

    @property
    @abstractmethod
    def available(self) -> bool:
        """True when the provider is configured (e.g. an API key is present)."""

    @abstractmethod
    def generate(self, request: VisionRequest) -> VisionResult:
        """Run the request. Must not raise for expected failures."""

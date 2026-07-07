"""AI provider interfaces (ports).

These define the contracts every provider must satisfy. The application depends
on these abstractions and on the routers — never on a concrete provider
(Docs/03_System_Architecture.md §13).
"""

from app.ai.interfaces.vision_provider import VisionProvider, VisionRequest, VisionResult
from app.ai.interfaces.chat_provider import (
    ChatMessage,
    ChatProvider,
    ChatRequest,
    ChatResult,
)

__all__ = [
    "VisionProvider",
    "VisionRequest",
    "VisionResult",
    "ChatProvider",
    "ChatMessage",
    "ChatRequest",
    "ChatResult",
]

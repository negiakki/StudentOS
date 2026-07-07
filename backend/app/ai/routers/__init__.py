"""AI routers — the only AI entry points the application may use.

Application code calls `get_vision_router()` / `get_chat_router()` and the router
selects the configured provider (Docs/03_System_Architecture.md §13). Code must
never import a provider directly.
"""

from app.ai.routers.vision_router import VisionRouter, get_vision_router
from app.ai.routers.chat_router import ChatRouter, get_chat_router

__all__ = [
    "VisionRouter",
    "get_vision_router",
    "ChatRouter",
    "get_chat_router",
]

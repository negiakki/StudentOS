"""Vision router.

Selects the configured vision provider (`VISION_PROVIDER`) and exposes a single
`generate()` the application calls. This indirection is what lets us change
providers by editing config alone (Docs/03_System_Architecture.md §13).
"""

from __future__ import annotations

from app.ai.interfaces.vision_provider import (
    VisionProvider,
    VisionRequest,
    VisionResult,
)
from app.ai.providers.gemini import GeminiVisionProvider
from app.ai.providers.openrouter import OpenRouterVisionProvider
from app.core.config import get_settings

# Registry of known vision providers. Add new providers here only.
_VISION_PROVIDERS: dict[str, type[VisionProvider]] = {
    "gemini": GeminiVisionProvider,
    "openrouter": OpenRouterVisionProvider,
}


class VisionRouter:
    def __init__(self, provider: VisionProvider) -> None:
        self._provider = provider

    @property
    def provider_name(self) -> str:
        return self._provider.name

    @property
    def available(self) -> bool:
        return self._provider.available

    def generate(self, request: VisionRequest) -> VisionResult:
        """Run a vision request through the selected provider."""
        return self._provider.generate(request)


def get_vision_router() -> VisionRouter:
    """Build the router for the configured vision provider.

    Falls back to Gemini if `VISION_PROVIDER` is unknown, so a typo degrades to
    the primary provider rather than crashing.
    """
    settings = get_settings()
    provider_cls = _VISION_PROVIDERS.get(
        settings.vision_provider.lower(), GeminiVisionProvider
    )
    return VisionRouter(provider_cls())

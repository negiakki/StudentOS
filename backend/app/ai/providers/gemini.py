"""Gemini provider (vision).

Implements the VisionProvider contract using Google's google-genai SDK. This is
the primary vision provider (Docs/03_System_Architecture.md §13). The SDK is
imported lazily so the app boots even if the package is absent, and all expected
failures are returned as VisionResult.failure(...) rather than raised.
"""

from __future__ import annotations

from app.ai.interfaces.vision_provider import (
    VisionProvider,
    VisionRequest,
    VisionResult,
)
from app.core.config import get_settings


class GeminiVisionProvider(VisionProvider):
    name = "gemini"

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model

    @property
    def available(self) -> bool:
        return bool(self._api_key)

    def generate(self, request: VisionRequest) -> VisionResult:
        if not self.available:
            return VisionResult.failure(
                "Gemini is not configured (GEMINI_API_KEY)."
            )

        try:
            text = self._generate(request)
        except Exception as exc:  # provider/network/SDK error — stay resilient
            return VisionResult.failure(f"Gemini request failed: {exc}")

        return VisionResult(ok=True, text=text or "")

    def _generate(self, request: VisionRequest) -> str:
        # Imported lazily so the app boots even if the SDK is not installed.
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self._api_key)
        config = None
        if request.json_response:
            config = types.GenerateContentConfig(
                response_mime_type="application/json"
            )

        response = client.models.generate_content(
            model=self._model,
            contents=[
                types.Part.from_bytes(
                    data=request.content, mime_type=request.mime_type
                ),
                request.prompt,
            ],
            config=config,
        )
        return response.text or ""

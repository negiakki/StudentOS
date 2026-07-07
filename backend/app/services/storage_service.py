"""Supabase Storage access for timetable uploads.

Wraps the Supabase Storage REST API (Docs/03_System_Architecture.md — Storage).
Uses the service-role key server-side, so it must never be reachable from the
frontend. Files are namespaced per user (`{user_id}/timetable/{filename}`) so a
user can only ever touch their own objects (Docs/04_Database_Design.md §18).

V1 keeps a single timetable per user: a new upload overwrites the previous
object at a stable path, and deleting the account removes the folder.
"""

from __future__ import annotations

import uuid

import httpx

from app.core.config import get_settings

# Formats accepted by the timetable parser (Docs/02_PRD.md §7).
ALLOWED_MIME_TYPES: frozenset[str] = frozenset(
    {"application/pdf", "image/png", "image/jpeg"}
)


class StorageError(RuntimeError):
    """Raised when Supabase Storage returns an error or is misconfigured."""


class StorageService:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.supabase_storage_url
        self._bucket = settings.supabase_storage_bucket
        self._service_key = settings.supabase_service_role_key
        self._timeout = httpx.Timeout(30.0)

    @property
    def _configured(self) -> bool:
        return bool(self._base_url and self._service_key)

    def _headers(self, content_type: str | None = None) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self._service_key}",
            "apikey": self._service_key,
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    @staticmethod
    def build_object_path(user_id: uuid.UUID, filename: str) -> str:
        """Stable, user-scoped object key. One timetable per user, so the
        filename is fixed by category rather than the uploaded name."""
        return f"{user_id}/timetable/{filename}"

    def upload(
        self,
        *,
        user_id: uuid.UUID,
        filename: str,
        content: bytes,
        content_type: str,
    ) -> str:
        """Upload (or overwrite) the user's timetable object. Returns the
        storage path. Raises StorageError on failure or if unconfigured."""
        if not self._configured:
            raise StorageError(
                "Supabase Storage is not configured "
                "(SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY)."
            )

        object_path = self.build_object_path(user_id, filename)
        url = f"{self._base_url}/object/{self._bucket}/{object_path}"

        # x-upsert lets a re-upload replace the previous timetable in place.
        headers = self._headers(content_type)
        headers["x-upsert"] = "true"

        try:
            response = httpx.post(
                url, content=content, headers=headers, timeout=self._timeout
            )
        except httpx.HTTPError as exc:  # network / DNS / timeout
            raise StorageError(f"Storage upload failed: {exc}") from exc

        if response.status_code not in (200, 201):
            raise StorageError(
                f"Storage upload failed ({response.status_code}): {response.text}"
            )

        return object_path

    def delete(self, object_path: str) -> None:
        """Remove an object. Best-effort: a missing object is not an error."""
        if not self._configured:
            return

        url = f"{self._base_url}/object/{self._bucket}/{object_path}"
        try:
            httpx.request(
                "DELETE", url, headers=self._headers(), timeout=self._timeout
            )
        except httpx.HTTPError:
            # Deletion is cleanup; never let it break the caller's flow.
            return

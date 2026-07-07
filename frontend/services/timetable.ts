/**
 * Timetable API service (V1 — storage-only). Built on lib/api.ts; no React here.
 * Each call needs the caller's Supabase access token for the backend JWT gate.
 */

import { apiFetch } from "@/lib/api";
import type { TimetableFile, TimetableFileState } from "@/types/timetable";

/** Upload (or replace) the timetable file. Stored only — no parsing. */
export async function uploadTimetableFile(
  file: File,
  accessToken: string,
): Promise<TimetableFile> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<TimetableFile>("/timetable/upload", {
    method: "POST",
    body: form,
    accessToken,
  });
}

/** Get the current uploaded timetable file (with a signed view URL), if any. */
export async function getTimetableFile(
  accessToken: string,
): Promise<TimetableFileState> {
  return apiFetch<TimetableFileState>("/timetable", { accessToken });
}

/** Delete the uploaded timetable file. Idempotent. */
export async function deleteTimetableFile(
  accessToken: string,
): Promise<{ success: boolean; removed: boolean }> {
  return apiFetch<{ success: boolean; removed: boolean }>("/timetable", {
    method: "DELETE",
    accessToken,
  });
}

/**
 * Timetable API service (Phase 4). Built on lib/api.ts; no React here.
 * Each call needs the caller's Supabase access token for the backend JWT gate.
 */

import { apiFetch } from "@/lib/api";
import type {
  TimetableOut,
  TimetablePreview,
  TimetableSaveRequest,
} from "@/types/timetable";

/** Upload a PDF/PNG/JPG timetable and get back an editable, parsed preview. */
export async function uploadTimetable(
  file: File,
  accessToken: string,
): Promise<TimetablePreview> {
  const form = new FormData();
  form.append("file", file);
  return apiFetch<TimetablePreview>("/timetable/upload", {
    method: "POST",
    body: form,
    accessToken,
  });
}

/** Persist the user-confirmed timetable, replacing any existing one. */
export async function saveTimetable(
  payload: TimetableSaveRequest,
  accessToken: string,
): Promise<TimetableOut> {
  return apiFetch<TimetableOut>("/timetable", {
    method: "POST",
    body: JSON.stringify(payload),
    accessToken,
  });
}

/** Read the user's saved timetable (empty subjects if none yet). */
export async function getTimetable(accessToken: string): Promise<TimetableOut> {
  return apiFetch<TimetableOut>("/timetable", { accessToken });
}

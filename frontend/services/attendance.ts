/**
 * Attendance API service (V1 — manual attendance). Built on lib/api.ts.
 * Each call needs the caller's Supabase access token for the backend JWT gate.
 */

import { apiFetch } from "@/lib/api";
import type {
  AttendanceOverview,
  AttendanceRecord,
  AttendanceStatus,
  RecordMutationResult,
  SubjectAttendance,
  SubjectCreate,
  SubjectUpdate,
} from "@/types/attendance";

/** Aggregate attendance across the user's subjects (dashboard overview). */
export async function getAttendanceOverview(
  accessToken: string,
): Promise<AttendanceOverview> {
  return apiFetch<AttendanceOverview>("/attendance/overview", { accessToken });
}

/** List the user's subjects with computed attendance. */
export async function getSubjects(
  accessToken: string,
): Promise<SubjectAttendance[]> {
  return apiFetch<SubjectAttendance[]>("/attendance/subjects", { accessToken });
}

/** Add a subject with its initial attended / total counts. */
export async function addSubject(
  payload: SubjectCreate,
  accessToken: string,
): Promise<SubjectAttendance> {
  return apiFetch<SubjectAttendance>("/attendance/subjects", {
    method: "POST",
    body: JSON.stringify(payload),
    accessToken,
  });
}

/** Edit a subject's name or counts. */
export async function updateSubject(
  subjectId: string,
  payload: SubjectUpdate,
  accessToken: string,
): Promise<SubjectAttendance> {
  return apiFetch<SubjectAttendance>(`/attendance/subjects/${subjectId}`, {
    method: "PATCH",
    body: JSON.stringify(payload),
    accessToken,
  });
}

/** Delete a subject and its attendance summary. Idempotent. */
export async function deleteSubject(
  subjectId: string,
  accessToken: string,
): Promise<{ success: boolean; removed: boolean }> {
  return apiFetch<{ success: boolean; removed: boolean }>(
    `/attendance/subjects/${subjectId}`,
    { method: "DELETE", accessToken },
  );
}

// --- Phase 6: daily marking, calendar, history ---

/** A single subject's computed attendance (for its detail page). */
export async function getSubject(
  subjectId: string,
  accessToken: string,
): Promise<SubjectAttendance> {
  return apiFetch<SubjectAttendance>(`/attendance/subjects/${subjectId}`, {
    accessToken,
  });
}

/**
 * Attendance records for a subject. Pass `start`+`end` for a calendar month, or
 * `limit` for the most-recent history list — both read the same records.
 */
export async function getSubjectRecords(
  subjectId: string,
  params: { start?: string; end?: string; limit?: number },
  accessToken: string,
): Promise<AttendanceRecord[]> {
  const q = new URLSearchParams();
  if (params.start) q.set("start", params.start);
  if (params.end) q.set("end", params.end);
  if (params.limit != null) q.set("limit", String(params.limit));
  const qs = q.toString();
  return apiFetch<AttendanceRecord[]>(
    `/attendance/subjects/${subjectId}/records${qs ? `?${qs}` : ""}`,
    { accessToken },
  );
}

/** Mark present/absent (or edit a previous day) for one date. */
export async function markRecord(
  subjectId: string,
  attendanceDate: string,
  status: AttendanceStatus,
  accessToken: string,
): Promise<RecordMutationResult> {
  return apiFetch<RecordMutationResult>(
    `/attendance/subjects/${subjectId}/records/${attendanceDate}`,
    { method: "PUT", body: JSON.stringify({ status }), accessToken },
  );
}

/** Clear a day's mark, reversing its effect on the totals. Idempotent. */
export async function clearRecord(
  subjectId: string,
  attendanceDate: string,
  accessToken: string,
): Promise<RecordMutationResult> {
  return apiFetch<RecordMutationResult>(
    `/attendance/subjects/${subjectId}/records/${attendanceDate}`,
    { method: "DELETE", accessToken },
  );
}

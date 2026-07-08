/**
 * Attendance API service (V1 — manual attendance). Built on lib/api.ts.
 * Each call needs the caller's Supabase access token for the backend JWT gate.
 */

import { apiFetch } from "@/lib/api";
import type {
  AttendanceOverview,
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

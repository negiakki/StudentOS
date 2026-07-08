/**
 * Attendance domain types (V1 setup + Phase 6 daily marking).
 *
 * The user enters an attended/total baseline per subject; the backend computes
 * percentage, safe-skips, and the threshold warning. Phase 6 adds day-by-day
 * records (present/absent) that adjust those figures. Mirrors the backend schemas.
 */

export type AttendanceStatus = "PRESENT" | "ABSENT";

export interface AttendanceRecord {
  id: string;
  attendance_date: string; // ISO date, YYYY-MM-DD
  status: AttendanceStatus;
}

export interface RecordMutationResult {
  subject: SubjectAttendance;
  record: AttendanceRecord | null;
}

export interface SubjectAttendance {
  id: string;
  name: string;
  attended_classes: number;
  total_classes: number;
  percentage: number;
  safe_skips: number;
  meets_threshold: boolean;
}

export interface AttendanceOverview {
  threshold: number;
  subject_count: number;
  attended_total: number;
  total_total: number;
  overall_percentage: number;
  below_threshold_count: number;
  subjects: SubjectAttendance[];
}

export interface SubjectCreate {
  name: string;
  attended_classes: number;
  total_classes: number;
}

export interface SubjectUpdate {
  name?: string;
  attended_classes?: number;
  total_classes?: number;
}

/**
 * Attendance domain types (V1 — manual attendance).
 *
 * The user enters attended/total per subject; the backend computes percentage,
 * safe-skips, and the threshold warning. Mirrors the backend attendance schemas.
 */

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

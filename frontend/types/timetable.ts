/** Timetable domain types, mirroring the backend schemas (Phase 4). */

/** 1 = Monday .. 7 = Sunday (Docs/04_Database_Design.md §6). */
export type DayOfWeek = 1 | 2 | 3 | 4 | 5 | 6 | 7;

/** A lecture in a parsed preview: times are "HH:MM" strings. */
export interface SlotPreview {
  day_of_week: number;
  start_time: string;
  end_time: string;
  room: string | null;
}

export interface SubjectPreview {
  name: string;
  faculty: string | null;
  classroom: string | null;
  slots: SlotPreview[];
}

export interface TimetablePreview {
  file_id: string;
  parsing_status: string;
  parsing_confidence: number | null;
  parse_error: string | null;
  subjects: SubjectPreview[];
}

/** Payload shapes for saving a confirmed timetable. */
export interface SlotInput {
  day_of_week: number;
  start_time: string; // "HH:MM"
  end_time: string; // "HH:MM"
  room: string | null;
}

export interface SubjectInput {
  name: string;
  faculty: string | null;
  classroom: string | null;
  slots: SlotInput[];
}

export interface TimetableSaveRequest {
  subjects: SubjectInput[];
}

/** Saved timetable returned by the API (slots carry ids and full times). */
export interface SlotOut {
  id: string;
  day_of_week: number;
  start_time: string;
  end_time: string;
  room: string | null;
}

export interface SubjectOut {
  id: string;
  name: string;
  faculty: string | null;
  classroom: string | null;
  slots: SlotOut[];
}

export interface TimetableOut {
  subjects: SubjectOut[];
}

export const DAY_LABELS: Record<number, string> = {
  1: "Monday",
  2: "Tuesday",
  3: "Wednesday",
  4: "Thursday",
  5: "Friday",
  6: "Saturday",
  7: "Sunday",
};

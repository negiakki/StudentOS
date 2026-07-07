/**
 * Timetable domain types (V1 — storage-only).
 *
 * V1 uploads and displays the timetable file itself; there is no automatic
 * parsing or subject/slot editing. The parser and its structured types are
 * preserved on the backend for V2 (see ENABLE_TIMETABLE_PARSING).
 */

/** The user's uploaded timetable file, mirroring the backend TimetableFile. */
export interface TimetableFile {
  id: string;
  filename: string;
  mime_type: string;
  storage_path: string;
  uploaded_at: string;
  /** Short-lived signed URL for displaying/downloading the file. */
  view_url: string | null;
}

/** Whether a timetable file exists for the user, and its details if so. */
export interface TimetableFileState {
  has_file: boolean;
  file: TimetableFile | null;
}

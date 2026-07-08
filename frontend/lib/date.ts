/**
 * Small date helpers for attendance. All dates are handled in the user's LOCAL
 * time so "today" matches what the student sees; the backend stays date-agnostic
 * and only stores the ISO day string (YYYY-MM-DD) we send it.
 */

const MONTHS = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
];

/** Local calendar date as YYYY-MM-DD. */
export function toISODate(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

/** Today as YYYY-MM-DD (local). */
export function todayISODate(): string {
  return toISODate(new Date());
}

/** Parse a YYYY-MM-DD string into a local Date (no UTC shift). */
export function fromISODate(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

/** "Today" / "Yesterday" / "5 Jul" (adds the year if it isn't the current one). */
export function historyLabel(iso: string): string {
  const today = todayISODate();
  if (iso === today) return "Today";

  const yesterday = new Date();
  yesterday.setDate(yesterday.getDate() - 1);
  if (iso === toISODate(yesterday)) return "Yesterday";

  const d = fromISODate(iso);
  const base = `${d.getDate()} ${MONTHS[d.getMonth()]}`;
  return d.getFullYear() === new Date().getFullYear()
    ? base
    : `${base} ${d.getFullYear()}`;
}

/** "Saturday, 5 Jul 2026" — for the selected-day label in the calendar. */
export function longLabel(iso: string): string {
  const d = fromISODate(iso);
  const weekday = d.toLocaleDateString(undefined, { weekday: "long" });
  return `${weekday}, ${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

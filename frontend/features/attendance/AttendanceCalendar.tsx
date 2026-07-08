"use client";

/**
 * Month calendar for one subject. Renders the same attendance records as the
 * history list; click a past/today cell to mark Present / Absent or clear it
 * (edit previous days). Future days can't be marked. Marking here updates the
 * shared records/summary in the parent, so the history and totals stay in sync.
 */

import { useEffect, useState } from "react";

import { longLabel, toISODate, todayISODate } from "@/lib/date";
import type { AttendanceRecord, AttendanceStatus } from "@/types/attendance";

const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

export function AttendanceCalendar({
  recordsByDate,
  busyDate,
  onEnsureMonth,
  onSet,
  onClear,
}: {
  recordsByDate: Record<string, AttendanceRecord>;
  busyDate: string | null;
  onEnsureMonth: (year: number, month0: number) => void;
  onSet: (dateISO: string, status: AttendanceStatus) => void;
  onClear: (dateISO: string) => void;
}) {
  const now = new Date();
  const [viewYear, setViewYear] = useState(now.getFullYear());
  const [viewMonth, setViewMonth] = useState(now.getMonth()); // 0-11
  const [selected, setSelected] = useState<string | null>(null);

  const todayISO = todayISODate();

  // Load this month's records whenever the visible month changes.
  useEffect(() => {
    onEnsureMonth(viewYear, viewMonth);
  }, [viewYear, viewMonth, onEnsureMonth]);

  const firstWeekday = new Date(viewYear, viewMonth, 1).getDay(); // 0=Sun
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const monthName = new Date(viewYear, viewMonth, 1).toLocaleDateString(
    undefined,
    { month: "long", year: "numeric" },
  );

  // Can't navigate past the current month (no future marking).
  const atCurrentMonth =
    viewYear > now.getFullYear() ||
    (viewYear === now.getFullYear() && viewMonth >= now.getMonth());

  function shiftMonth(delta: number) {
    setSelected(null);
    const d = new Date(viewYear, viewMonth + delta, 1);
    setViewYear(d.getFullYear());
    setViewMonth(d.getMonth());
  }

  const cells: (string | null)[] = [];
  for (let i = 0; i < firstWeekday; i++) cells.push(null);
  for (let day = 1; day <= daysInMonth; day++) {
    cells.push(toISODate(new Date(viewYear, viewMonth, day)));
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <button
          type="button"
          onClick={() => shiftMonth(-1)}
          className="rounded-lg border border-neutral-300 px-2.5 py-1 text-sm text-neutral-600 transition hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
          aria-label="Previous month"
        >
          ‹
        </button>
        <span className="text-sm font-medium text-neutral-800 dark:text-neutral-200">
          {monthName}
        </span>
        <button
          type="button"
          onClick={() => shiftMonth(1)}
          disabled={atCurrentMonth}
          className="rounded-lg border border-neutral-300 px-2.5 py-1 text-sm text-neutral-600 transition hover:bg-neutral-100 disabled:opacity-40 disabled:hover:bg-transparent dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
          aria-label="Next month"
        >
          ›
        </button>
      </div>

      <div className="grid grid-cols-7 gap-1 text-center">
        {WEEKDAYS.map((w) => (
          <span
            key={w}
            className="py-1 text-xs font-medium text-neutral-400"
          >
            {w}
          </span>
        ))}
        {cells.map((iso, idx) => {
          if (iso === null) return <span key={`b${idx}`} />;
          const rec = recordsByDate[iso];
          const isFuture = iso > todayISO;
          const isToday = iso === todayISO;
          const isSelected = iso === selected;
          const day = Number(iso.slice(8, 10));

          const status = rec?.status;
          const tone =
            status === "PRESENT"
              ? "bg-emerald-500 text-white"
              : status === "ABSENT"
                ? "bg-red-500 text-white"
                : "text-neutral-700 dark:text-neutral-300";

          return (
            <button
              key={iso}
              type="button"
              disabled={isFuture}
              onClick={() => setSelected(iso)}
              className={[
                "aspect-square rounded-lg text-sm transition",
                tone,
                isFuture
                  ? "cursor-not-allowed opacity-30"
                  : "hover:ring-1 hover:ring-neutral-400",
                isSelected ? "ring-2 ring-neutral-900 dark:ring-neutral-100" : "",
                isToday && !status
                  ? "border border-neutral-400 dark:border-neutral-500"
                  : "",
              ].join(" ")}
            >
              {day}
            </button>
          );
        })}
      </div>

      <div className="flex flex-wrap items-center gap-3 text-xs text-neutral-500">
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" /> Present
        </span>
        <span className="flex items-center gap-1.5">
          <span className="h-2.5 w-2.5 rounded-full bg-red-500" /> Absent
        </span>
      </div>

      {selected && (
        <div className="rounded-xl border border-neutral-200 bg-neutral-50 p-3 dark:border-neutral-800 dark:bg-neutral-950/40">
          <p className="text-sm font-medium text-neutral-800 dark:text-neutral-200">
            {longLabel(selected)}
          </p>
          <div className="mt-2 flex flex-wrap gap-2">
            <button
              type="button"
              disabled={busyDate === selected}
              onClick={() => onSet(selected, "PRESENT")}
              className="rounded-lg bg-emerald-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-emerald-700 disabled:opacity-60"
            >
              Present
            </button>
            <button
              type="button"
              disabled={busyDate === selected}
              onClick={() => onSet(selected, "ABSENT")}
              className="rounded-lg bg-red-600 px-3 py-1.5 text-sm font-medium text-white transition hover:bg-red-700 disabled:opacity-60"
            >
              Absent
            </button>
            {recordsByDate[selected] && (
              <button
                type="button"
                disabled={busyDate === selected}
                onClick={() => onClear(selected)}
                className="rounded-lg border border-neutral-300 px-3 py-1.5 text-sm text-neutral-700 transition hover:bg-neutral-100 disabled:opacity-60 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
              >
                Clear
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

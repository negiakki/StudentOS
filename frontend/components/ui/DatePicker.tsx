"use client";

/**
 * Reusable date picker: a text-input-styled trigger that opens a popover
 * month-grid calendar. Mirrors the Attendance module's calendar pattern
 * (features/attendance/AttendanceCalendar.tsx) so the picking UX feels the
 * same across the app. Value/onChange use the same YYYY-MM-DD string the
 * backend already expects — no format translation needed by callers.
 */

import { useEffect, useRef, useState } from "react";

import { fromISODate, toISODate, todayISODate } from "@/lib/date";

const WEEKDAYS = ["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"];

export function DatePicker({
  value,
  onChange,
  placeholder = "No date",
  className = "",
}: {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
}) {
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const base = value ? fromISODate(value) : new Date();
  const [viewYear, setViewYear] = useState(base.getFullYear());
  const [viewMonth, setViewMonth] = useState(base.getMonth());

  useEffect(() => {
    if (!open) return;
    const anchor = value ? fromISODate(value) : new Date();
    setViewYear(anchor.getFullYear());
    setViewMonth(anchor.getMonth());
  }, [open, value]);

  useEffect(() => {
    if (!open) return;
    function handlePointerDown(e: MouseEvent) {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false);
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [open]);

  const firstWeekday = new Date(viewYear, viewMonth, 1).getDay();
  const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
  const monthName = new Date(viewYear, viewMonth, 1).toLocaleDateString(
    undefined,
    { month: "long", year: "numeric" },
  );
  const todayISO = todayISODate();

  function shiftMonth(delta: number) {
    const d = new Date(viewYear, viewMonth + delta, 1);
    setViewYear(d.getFullYear());
    setViewMonth(d.getMonth());
  }

  const cells: (string | null)[] = [];
  for (let i = 0; i < firstWeekday; i++) cells.push(null);
  for (let day = 1; day <= daysInMonth; day++) {
    cells.push(toISODate(new Date(viewYear, viewMonth, day)));
  }

  function pick(iso: string) {
    onChange(iso);
    setOpen(false);
  }

  const label = value
    ? fromISODate(value).toLocaleDateString(undefined, {
        day: "numeric",
        month: "short",
        year: "numeric",
      })
    : placeholder;

  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className={`flex w-full items-center justify-between rounded-lg border border-neutral-300 bg-white px-3 py-2 text-left text-sm outline-none focus:border-neutral-500 dark:border-neutral-700 dark:bg-neutral-950 ${
          value
            ? "text-neutral-900 dark:text-neutral-100"
            : "text-neutral-400 dark:text-neutral-500"
        } ${className}`}
      >
        <span>{label}</span>
        <svg
          viewBox="0 0 20 20"
          fill="none"
          className="h-4 w-4 shrink-0 text-neutral-400"
          aria-hidden="true"
        >
          <rect
            x="3"
            y="4"
            width="14"
            height="13"
            rx="2"
            stroke="currentColor"
            strokeWidth="1.5"
          />
          <path d="M3 8h14M7 2v4M13 2v4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </button>

      {open && (
        <div className="absolute z-20 mt-1 w-72 max-w-[90vw] space-y-3 rounded-xl border border-neutral-200 bg-white p-3 shadow-lg dark:border-neutral-800 dark:bg-neutral-900">
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
              className="rounded-lg border border-neutral-300 px-2.5 py-1 text-sm text-neutral-600 transition hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
              aria-label="Next month"
            >
              ›
            </button>
          </div>

          <div className="grid grid-cols-7 gap-1 text-center">
            {WEEKDAYS.map((w) => (
              <span key={w} className="py-1 text-xs font-medium text-neutral-400">
                {w}
              </span>
            ))}
            {cells.map((iso, idx) => {
              if (iso === null) return <span key={`b${idx}`} />;
              const isSelected = iso === value;
              const isToday = iso === todayISO;
              const day = Number(iso.slice(8, 10));

              return (
                <button
                  key={iso}
                  type="button"
                  onClick={() => pick(iso)}
                  className={[
                    "aspect-square rounded-lg text-sm transition",
                    isSelected
                      ? "bg-neutral-900 text-white dark:bg-white dark:text-neutral-900"
                      : "text-neutral-700 hover:bg-neutral-100 dark:text-neutral-300 dark:hover:bg-neutral-800",
                    isToday && !isSelected
                      ? "border border-neutral-400 dark:border-neutral-500"
                      : "",
                  ].join(" ")}
                >
                  {day}
                </button>
              );
            })}
          </div>

          <div className="flex items-center justify-between border-t border-neutral-100 pt-2 dark:border-neutral-800">
            <button
              type="button"
              onClick={() => pick(todayISODate())}
              className="text-xs font-medium text-neutral-600 hover:underline dark:text-neutral-300"
            >
              Today
            </button>
            {value && (
              <button
                type="button"
                onClick={() => {
                  onChange("");
                  setOpen(false);
                }}
                className="text-xs font-medium text-red-600 hover:underline dark:text-red-400"
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

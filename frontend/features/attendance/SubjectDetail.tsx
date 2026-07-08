"use client";

/**
 * Subject attendance detail (Phase 6). Shows the computed percentage, today's
 * status with Mark Present / Absent, a recent Attendance History list, and a
 * collapsible calendar for marking or editing any past day. History and calendar
 * render the SAME records; every mark updates the shared state and the backend
 * summary together, so the figures stay consistent.
 */

import { useCallback, useMemo, useRef, useState } from "react";

import { Card, CardHeader } from "@/components/ui/Card";
import { ApiError } from "@/lib/api";
import { historyLabel, todayISODate } from "@/lib/date";
import { createClient } from "@/lib/supabase/client";
import {
  clearRecord,
  getSubjectRecords,
  markRecord,
} from "@/services/attendance";
import type {
  AttendanceRecord,
  AttendanceStatus,
  RecordMutationResult,
  SubjectAttendance,
} from "@/types/attendance";
import { AttendanceCalendar } from "./AttendanceCalendar";

const HISTORY_LIMIT = 8;

async function getAccessToken(): Promise<string> {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();
  if (!session?.access_token) {
    throw new Error("Your session has expired. Please sign in again.");
  }
  return session.access_token;
}

function messageFor(err: unknown): string {
  if (err instanceof ApiError) return err.message;
  if (err instanceof Error) return err.message;
  return "Something went wrong. Please try again.";
}

function indexByDate(records: AttendanceRecord[]): Record<string, AttendanceRecord> {
  const map: Record<string, AttendanceRecord> = {};
  for (const r of records) map[r.attendance_date] = r;
  return map;
}

function monthRange(year: number, month0: number): { start: string; end: string } {
  const pad = (n: number) => String(n).padStart(2, "0");
  const last = new Date(year, month0 + 1, 0).getDate();
  const m = pad(month0 + 1);
  return { start: `${year}-${m}-01`, end: `${year}-${m}-${pad(last)}` };
}

export function SubjectDetail({
  subjectId,
  initialSubject,
  initialRecords,
}: {
  subjectId: string;
  initialSubject: SubjectAttendance;
  initialRecords: AttendanceRecord[];
}) {
  const [subject, setSubject] = useState(initialSubject);
  const [recordsByDate, setRecordsByDate] = useState(() =>
    indexByDate(initialRecords),
  );
  const [busyDate, setBusyDate] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showCalendar, setShowCalendar] = useState(false);

  const loadedMonths = useRef<Set<string>>(new Set());
  const today = todayISODate();

  const history = useMemo(
    () =>
      Object.values(recordsByDate)
        .sort((a, b) => b.attendance_date.localeCompare(a.attendance_date))
        .slice(0, HISTORY_LIMIT),
    [recordsByDate],
  );

  const applyResult = useCallback(
    (res: RecordMutationResult, dateISO: string) => {
      setSubject(res.subject);
      setRecordsByDate((prev) => {
        const next = { ...prev };
        if (res.record) next[dateISO] = res.record;
        else delete next[dateISO];
        return next;
      });
    },
    [],
  );

  const setStatus = useCallback(
    async (dateISO: string, status: AttendanceStatus) => {
      setError(null);
      setBusyDate(dateISO);
      try {
        const token = await getAccessToken();
        applyResult(await markRecord(subjectId, dateISO, status, token), dateISO);
      } catch (err) {
        setError(messageFor(err));
      } finally {
        setBusyDate(null);
      }
    },
    [subjectId, applyResult],
  );

  const clearDay = useCallback(
    async (dateISO: string) => {
      setError(null);
      setBusyDate(dateISO);
      try {
        const token = await getAccessToken();
        applyResult(await clearRecord(subjectId, dateISO, token), dateISO);
      } catch (err) {
        setError(messageFor(err));
      } finally {
        setBusyDate(null);
      }
    },
    [subjectId, applyResult],
  );

  const ensureMonth = useCallback(
    async (year: number, month0: number) => {
      const key = `${year}-${month0}`;
      if (loadedMonths.current.has(key)) return;
      loadedMonths.current.add(key);
      try {
        const token = await getAccessToken();
        const { start, end } = monthRange(year, month0);
        const rows = await getSubjectRecords(subjectId, { start, end }, token);
        setRecordsByDate((prev) => ({ ...prev, ...indexByDate(rows) }));
      } catch {
        // A failed month load just leaves that month unpopulated; allow retry.
        loadedMonths.current.delete(key);
      }
    },
    [subjectId],
  );

  const todayRec = recordsByDate[today];
  const pctOk = subject.meets_threshold;

  return (
    <div className="space-y-5">
      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
          {error}
        </div>
      )}

      {/* Overview */}
      <Card>
        <div className="flex items-center justify-between gap-4 px-5 py-5">
          <div>
            <h1 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
              {subject.name}
            </h1>
            <p className="mt-1 text-xs text-neutral-500">
              {subject.attended_classes}/{subject.total_classes} classes ·{" "}
              {pctOk
                ? `can skip ${subject.safe_skips}`
                : "below target"}
            </p>
          </div>
          <span
            className={`text-3xl font-semibold tabular-nums ${
              pctOk
                ? "text-emerald-600 dark:text-emerald-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            {subject.percentage}%
          </span>
        </div>
      </Card>

      {/* Today's status */}
      <Card>
        <CardHeader
          title="Today's Status"
          subtitle={
            todayRec
              ? todayRec.status === "PRESENT"
                ? "✅ Present"
                : "❌ Absent"
              : "Not marked yet"
          }
        />
        <div className="flex flex-wrap gap-2 px-5 py-4">
          <button
            type="button"
            disabled={busyDate === today}
            onClick={() => setStatus(today, "PRESENT")}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-60 ${
              todayRec?.status === "PRESENT"
                ? "bg-emerald-600 text-white hover:bg-emerald-700"
                : "border border-neutral-300 text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
            }`}
          >
            Present
          </button>
          <button
            type="button"
            disabled={busyDate === today}
            onClick={() => setStatus(today, "ABSENT")}
            className={`rounded-lg px-4 py-2 text-sm font-medium transition disabled:opacity-60 ${
              todayRec?.status === "ABSENT"
                ? "bg-red-600 text-white hover:bg-red-700"
                : "border border-neutral-300 text-neutral-700 hover:bg-neutral-100 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
            }`}
          >
            Absent
          </button>
          {todayRec && (
            <button
              type="button"
              disabled={busyDate === today}
              onClick={() => clearDay(today)}
              className="rounded-lg border border-neutral-300 px-4 py-2 text-sm text-neutral-700 transition hover:bg-neutral-100 disabled:opacity-60 dark:border-neutral-700 dark:text-neutral-300 dark:hover:bg-neutral-800"
            >
              Clear
            </button>
          )}
        </div>
      </Card>

      {/* Attendance History */}
      <Card>
        <CardHeader
          title="Attendance History"
          action={
            <button
              type="button"
              onClick={() => setShowCalendar((v) => !v)}
              className="text-xs font-medium text-neutral-500 transition hover:text-neutral-900 dark:hover:text-neutral-200"
            >
              {showCalendar ? "Hide Calendar" : "View Calendar"}
            </button>
          }
        />
        {history.length === 0 ? (
          <p className="px-5 py-8 text-center text-sm text-neutral-500">
            No days marked yet. Mark today above, or open the calendar to record
            past classes.
          </p>
        ) : (
          <ul className="divide-y divide-neutral-100 dark:divide-neutral-800">
            {history.map((r) => (
              <li
                key={r.id}
                className="flex items-center justify-between px-5 py-3 text-sm"
              >
                <span className="text-neutral-700 dark:text-neutral-300">
                  {historyLabel(r.attendance_date)}
                </span>
                <span
                  className={
                    r.status === "PRESENT"
                      ? "font-medium text-emerald-600 dark:text-emerald-400"
                      : "font-medium text-red-600 dark:text-red-400"
                  }
                >
                  {r.status === "PRESENT" ? "✅ Present" : "❌ Absent"}
                </span>
              </li>
            ))}
          </ul>
        )}

        {showCalendar && (
          <div className="border-t border-neutral-100 p-5 dark:border-neutral-800">
            <AttendanceCalendar
              recordsByDate={recordsByDate}
              busyDate={busyDate}
              onEnsureMonth={ensureMonth}
              onSet={setStatus}
              onClear={clearDay}
            />
          </div>
        )}
      </Card>
    </div>
  );
}

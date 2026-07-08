import Link from "next/link";
import { notFound } from "next/navigation";

import { createClient } from "@/lib/supabase/server";
import { getSubject, getSubjectRecords } from "@/services/attendance";
import { SubjectDetail } from "@/features/attendance/SubjectDetail";
import type { AttendanceRecord, SubjectAttendance } from "@/types/attendance";

export default async function SubjectAttendancePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session?.access_token) notFound();
  const token = session.access_token;

  let subject: SubjectAttendance;
  try {
    subject = await getSubject(id, token);
  } catch {
    // Not found or not owned — the backend scopes to the user.
    notFound();
  }

  // Recent records seed the history list and the initial calendar month.
  let initialRecords: AttendanceRecord[] = [];
  try {
    initialRecords = await getSubjectRecords(id, { limit: 60 }, token);
  } catch {
    initialRecords = [];
  }

  return (
    <div className="space-y-6">
      <Link
        href="/attendance"
        className="inline-flex items-center gap-1 text-sm text-neutral-500 transition hover:text-neutral-900 dark:hover:text-neutral-200"
      >
        ← Attendance
      </Link>

      <SubjectDetail
        subjectId={id}
        initialSubject={subject}
        initialRecords={initialRecords}
      />
    </div>
  );
}

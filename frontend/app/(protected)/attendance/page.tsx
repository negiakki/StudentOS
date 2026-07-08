import Link from "next/link";

import { AttendanceSetup } from "@/features/attendance/AttendanceSetup";
import { createClient } from "@/lib/supabase/server";
import { getSubjects } from "@/services/attendance";
import type { SubjectAttendance } from "@/types/attendance";

export default async function AttendancePage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  let initialSubjects: SubjectAttendance[] = [];
  if (session?.access_token) {
    try {
      initialSubjects = await getSubjects(session.access_token);
    } catch {
      // Backend unreachable or none yet — start empty.
      initialSubjects = [];
    }
  }

  return (
    <div className="space-y-6">
      <Link
        href="/dashboard"
        className="inline-flex items-center gap-1 text-sm text-neutral-500 transition hover:text-neutral-900 dark:hover:text-neutral-200"
      >
        ← Dashboard
      </Link>
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
          Attendance
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Add your semester subjects and keep their attended / total counts up to
          date. We&apos;ll track your percentage and safe skips.
        </p>
      </div>

      <AttendanceSetup initialSubjects={initialSubjects} />
    </div>
  );
}

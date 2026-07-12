import Link from "next/link";

import { AssignmentsManager } from "@/features/assignments/AssignmentsManager";
import { createClient } from "@/lib/supabase/server";
import { getAssignments } from "@/services/assignments";
import { getSubjects } from "@/services/attendance";
import type { Assignment } from "@/types/assignment";
import type { SubjectAttendance } from "@/types/attendance";

export default async function AssignmentsPage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  let initialAssignments: Assignment[] = [];
  let subjects: SubjectAttendance[] = [];
  if (session?.access_token) {
    const [assignmentsRes, subjectsRes] = await Promise.allSettled([
      getAssignments(session.access_token),
      getSubjects(session.access_token),
    ]);
    if (assignmentsRes.status === "fulfilled") initialAssignments = assignmentsRes.value;
    if (subjectsRes.status === "fulfilled") subjects = subjectsRes.value;
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
          Assignments
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Track your coursework by due date. Mark it complete once you&apos;re
          done, or edit it as things change.
        </p>
      </div>

      <AssignmentsManager initialAssignments={initialAssignments} subjects={subjects} />
    </div>
  );
}

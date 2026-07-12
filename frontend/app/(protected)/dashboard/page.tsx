import { AssignmentsCard } from "@/features/dashboard/AssignmentsCard";
import { AttendanceOverview } from "@/features/dashboard/AttendanceOverview";
import { Greeting } from "@/features/dashboard/Greeting";
import { MyTimetableCard } from "@/features/dashboard/MyTimetableCard";
import { QuickActions } from "@/features/dashboard/QuickActions";
import { createClient } from "@/lib/supabase/server";
import { getAssignmentDashboard } from "@/services/assignments";
import { getAttendanceOverview } from "@/services/attendance";
import { getTimetableFile } from "@/services/timetable";
import { getProfile } from "@/services/user";
import type { AssignmentDashboard } from "@/types/assignment";
import type { AttendanceOverview as Overview } from "@/types/attendance";
import type { TimetableFile } from "@/types/timetable";
import type { UserProfile } from "@/types/user";

/** Prefer the profile's name; fall back to the email local-part, then a default. */
function firstName(profile: UserProfile | null, email: string | undefined): string {
  const full = profile?.full_name?.trim();
  if (full) return full.split(/\s+/)[0];
  const local = email?.split("@")[0];
  return local && local.length > 0 ? local : "there";
}

export default async function DashboardPage() {
  const supabase = await createClient();
  const [{ data: userData }, { data: sessionData }] = await Promise.all([
    supabase.auth.getUser(),
    supabase.auth.getSession(),
  ]);

  const token = sessionData.session?.access_token;

  // Fetch the dashboard's data in parallel; a failure in one area must not blank
  // the whole page, so each falls back to an empty/null state.
  let profile: UserProfile | null = null;
  let overview: Overview | null = null;
  let timetable: TimetableFile | null = null;
  let assignmentDashboard: AssignmentDashboard | null = null;

  if (token) {
    const [profileRes, overviewRes, timetableRes, assignmentsRes] =
      await Promise.allSettled([
        getProfile(token),
        getAttendanceOverview(token),
        getTimetableFile(token),
        getAssignmentDashboard(token),
      ]);
    if (profileRes.status === "fulfilled") profile = profileRes.value;
    if (overviewRes.status === "fulfilled") overview = overviewRes.value;
    if (timetableRes.status === "fulfilled") timetable = timetableRes.value.file;
    if (assignmentsRes.status === "fulfilled") assignmentDashboard = assignmentsRes.value;
  }

  const name = firstName(profile, userData.user?.email);

  return (
    <div className="space-y-6">
      <Greeting name={name} />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <AttendanceOverview overview={overview} />
          <MyTimetableCard file={timetable} />
        </div>
        <div className="space-y-6">
          <QuickActions />
          <AssignmentsCard dashboard={assignmentDashboard} />
        </div>
      </div>
    </div>
  );
}

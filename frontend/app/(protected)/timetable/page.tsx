import { TimetableManager } from "@/features/timetable/TimetableManager";
import { getTimetable } from "@/services/timetable";
import { createClient } from "@/lib/supabase/server";
import type { TimetableOut } from "@/types/timetable";

export default async function TimetablePage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  // The protected layout already guarantees a user; guard the token defensively.
  let initial: TimetableOut = { subjects: [] };
  if (session?.access_token) {
    try {
      initial = await getTimetable(session.access_token);
    } catch {
      // Backend unreachable or no timetable yet — start from an empty state.
      initial = { subjects: [] };
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
          Timetable
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Upload your class schedule and confirm the detected classes.
        </p>
      </div>

      <TimetableManager initial={initial} />
    </div>
  );
}

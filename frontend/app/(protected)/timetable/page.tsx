import { TimetableUpload } from "@/features/timetable/TimetableUpload";
import { getTimetableFile } from "@/services/timetable";
import { createClient } from "@/lib/supabase/server";
import type { TimetableFile } from "@/types/timetable";

export default async function TimetablePage() {
  const supabase = await createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  // The protected layout already guarantees a user; guard the token defensively.
  let initialFile: TimetableFile | null = null;
  if (session?.access_token) {
    try {
      const state = await getTimetableFile(session.access_token);
      initialFile = state.file;
    } catch {
      // Backend unreachable or nothing uploaded yet — start empty.
      initialFile = null;
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
          Timetable
        </h1>
        <p className="mt-1 text-sm text-neutral-500">
          Upload your class schedule. You can replace or delete it anytime.
        </p>
      </div>

      <TimetableUpload initialFile={initialFile} />
    </div>
  );
}

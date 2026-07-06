/**
 * Renders the auth flow's feedback banner from query params.
 * `error` shows a red banner; known `message` keys show a friendly green banner.
 */

const MESSAGES: Record<string, string> = {
  "check-email":
    "Check your email for a confirmation link to continue.",
  "password-updated":
    "Your password has been updated. Please sign in with your new password.",
};

export function AuthMessage({
  error,
  message,
}: {
  error?: string;
  message?: string;
}) {
  if (error) {
    return (
      <p className="rounded-lg border border-red-300 bg-red-50 px-3 py-2 text-sm text-red-700 dark:border-red-900/50 dark:bg-red-950/40 dark:text-red-300">
        {error}
      </p>
    );
  }

  if (message) {
    return (
      <p className="rounded-lg border border-green-300 bg-green-50 px-3 py-2 text-sm text-green-700 dark:border-green-900/50 dark:bg-green-950/40 dark:text-green-300">
        {MESSAGES[message] ?? message}
      </p>
    );
  }

  return null;
}

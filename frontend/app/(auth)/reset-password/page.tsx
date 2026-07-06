import { AuthMessage } from "@/components/auth/AuthMessage";
import { inputClass, labelClass } from "@/components/auth/field-styles";
import { SubmitButton } from "@/components/auth/SubmitButton";

import { updatePassword } from "../actions";

/**
 * Reached from the password-recovery email link, after /auth/callback has
 * exchanged the recovery code for a session. The user sets a new password here.
 */
export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; message?: string }>;
}) {
  const { error, message } = await searchParams;

  return (
    <div className="space-y-5">
      <div className="space-y-1 text-center">
        <h1 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
          Set a new password
        </h1>
        <p className="text-sm text-neutral-500">Choose a new password for your account.</p>
      </div>

      <AuthMessage error={error} message={message} />

      <form action={updatePassword} className="space-y-4">
        <div>
          <label htmlFor="password" className={labelClass}>
            New password
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="new-password"
            required
            minLength={6}
            className={inputClass}
          />
          <p className="mt-1 text-xs text-neutral-400">At least 6 characters.</p>
        </div>
        <SubmitButton pendingText="Updating…">Update password</SubmitButton>
      </form>
    </div>
  );
}

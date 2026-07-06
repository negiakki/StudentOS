import Link from "next/link";

import { AuthMessage } from "@/components/auth/AuthMessage";
import { inputClass, labelClass } from "@/components/auth/field-styles";
import { SubmitButton } from "@/components/auth/SubmitButton";

import { forgotPassword } from "../actions";

export default async function ForgotPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; message?: string }>;
}) {
  const { error, message } = await searchParams;

  return (
    <div className="space-y-5">
      <div className="space-y-1 text-center">
        <h1 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
          Reset your password
        </h1>
        <p className="text-sm text-neutral-500">
          Enter your email and we&apos;ll send you a reset link.
        </p>
      </div>

      <AuthMessage error={error} message={message} />

      <form action={forgotPassword} className="space-y-4">
        <div>
          <label htmlFor="email" className={labelClass}>
            Email
          </label>
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            required
            className={inputClass}
          />
        </div>
        <SubmitButton pendingText="Sending…">Send reset link</SubmitButton>
      </form>

      <p className="text-center text-sm text-neutral-500">
        <Link
          href="/login"
          className="font-medium text-neutral-900 hover:underline dark:text-neutral-100"
        >
          Back to sign in
        </Link>
      </p>
    </div>
  );
}

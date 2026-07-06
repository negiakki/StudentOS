import Link from "next/link";

import { AuthMessage } from "@/components/auth/AuthMessage";
import { inputClass, labelClass } from "@/components/auth/field-styles";
import { SubmitButton } from "@/components/auth/SubmitButton";

import { signInWithGoogle, signup } from "../actions";

export default async function SignupPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; message?: string }>;
}) {
  const { error, message } = await searchParams;

  return (
    <div className="space-y-5">
      <div className="space-y-1 text-center">
        <h1 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
          Create your account
        </h1>
        <p className="text-sm text-neutral-500">Meet Coco and get organized</p>
      </div>

      <AuthMessage error={error} message={message} />

      <form action={signInWithGoogle}>
        <SubmitButton variant="secondary" pendingText="Redirecting…">
          Continue with Google
        </SubmitButton>
      </form>

      <div className="flex items-center gap-3">
        <span className="h-px flex-1 bg-neutral-200 dark:bg-neutral-800" />
        <span className="text-xs text-neutral-400">or</span>
        <span className="h-px flex-1 bg-neutral-200 dark:bg-neutral-800" />
      </div>

      <form action={signup} className="space-y-4">
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
        <div>
          <label htmlFor="password" className={labelClass}>
            Password
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
        <SubmitButton pendingText="Creating account…">Create account</SubmitButton>
      </form>

      <p className="text-center text-sm text-neutral-500">
        Already have an account?{" "}
        <Link
          href="/login"
          className="font-medium text-neutral-900 hover:underline dark:text-neutral-100"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}

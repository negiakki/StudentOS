"use client";

import { useFormStatus } from "react-dom";

type Props = {
  children: React.ReactNode;
  variant?: "primary" | "secondary";
  pendingText?: string;
};

/**
 * Submit button that disables itself and shows a pending label while the
 * enclosing form's server action runs (via useFormStatus).
 */
export function SubmitButton({ children, variant = "primary", pendingText }: Props) {
  const { pending } = useFormStatus();

  const base =
    "w-full rounded-lg px-4 py-2.5 text-sm font-medium transition disabled:opacity-60 disabled:cursor-not-allowed";
  const styles =
    variant === "primary"
      ? "bg-neutral-900 text-white hover:bg-neutral-800 dark:bg-white dark:text-neutral-900 dark:hover:bg-neutral-200"
      : "border border-neutral-300 bg-white text-neutral-900 hover:bg-neutral-50 dark:border-neutral-700 dark:bg-transparent dark:text-neutral-100 dark:hover:bg-neutral-900";

  return (
    <button type="submit" disabled={pending} className={`${base} ${styles}`}>
      {pending ? (pendingText ?? "Please wait…") : children}
    </button>
  );
}

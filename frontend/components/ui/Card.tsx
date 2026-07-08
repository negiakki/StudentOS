/**
 * Card — the shared surface for dashboard sections. Keeps spacing, borders,
 * radius, and dark-mode consistent across every widget.
 */

import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={`rounded-2xl border border-neutral-200 bg-white shadow-sm dark:border-neutral-800 dark:bg-neutral-900 ${className}`}
    >
      {children}
    </section>
  );
}

/** Optional header row: a title (and subtitle) on the left, an action on the right. */
export function CardHeader({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between gap-3 border-b border-neutral-100 px-5 py-4 dark:border-neutral-800">
      <div>
        <h2 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
          {title}
        </h2>
        {subtitle && (
          <p className="mt-0.5 text-xs text-neutral-500">{subtitle}</p>
        )}
      </div>
      {action}
    </div>
  );
}

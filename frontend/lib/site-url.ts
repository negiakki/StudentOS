import { headers } from "next/headers";

/**
 * Absolute site origin, used to build auth redirect URLs (OAuth, email links).
 * Prefers the incoming request's origin so it works across localhost, preview,
 * and production without reconfiguration; falls back to NEXT_PUBLIC_SITE_URL.
 */
export async function getSiteURL(): Promise<string> {
  const h = await headers();

  const origin = h.get("origin");
  if (origin) return origin;

  const host = h.get("x-forwarded-host") ?? h.get("host");
  if (host) {
    const proto = h.get("x-forwarded-proto") ?? "http";
    return `${proto}://${host}`;
  }

  return process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
}

/**
 * Session refresh + route protection, run from the root middleware on every
 * request. This is what makes sessions *persistent*: it refreshes the Supabase
 * token and writes the rotated cookies onto the response.
 *
 * Follows the official @supabase/ssr pattern:
 *  - do NOT run code between createServerClient and getUser()
 *  - use getUser() (verifies the token with the auth server), not getSession()
 *  - when redirecting, copy the refreshed cookies onto the redirect response
 */

import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

// Pages that require an authenticated user (PRD §16). Prefix match.
const PROTECTED_PREFIXES = [
  "/dashboard",
  "/timetable",
  "/attendance",
  "/assignments",
  "/todo",
  "/settings",
  "/coco",
];

// Auth pages a signed-in user should be bounced away from.
// `/reset-password` is intentionally excluded: a user arrives there with a
// valid recovery session precisely to set a new password.
const AUTH_ONLY_PATHS = ["/login", "/signup", "/forgot-password"];

export async function updateSession(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request });

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll() {
          return request.cookies.getAll();
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) =>
            request.cookies.set(name, value),
          );
          supabaseResponse = NextResponse.next({ request });
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options),
          );
        },
      },
    },
  );

  // IMPORTANT: no logic between client creation and getUser().
  const {
    data: { user },
  } = await supabase.auth.getUser();

  const path = request.nextUrl.pathname;
  const isProtected = PROTECTED_PREFIXES.some((p) => path.startsWith(p));
  const isAuthOnly = AUTH_ONLY_PATHS.includes(path);

  // Unauthenticated user hitting a protected page → send to login.
  if (!user && isProtected) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("redirectedFrom", path);
    return redirectWithCookies(url, supabaseResponse);
  }

  // Authenticated user hitting an auth page → send to dashboard.
  if (user && isAuthOnly) {
    const url = request.nextUrl.clone();
    url.pathname = "/dashboard";
    url.search = "";
    return redirectWithCookies(url, supabaseResponse);
  }

  return supabaseResponse;
}

/** Redirect while preserving any refreshed auth cookies. */
function redirectWithCookies(url: URL, from: NextResponse): NextResponse {
  const response = NextResponse.redirect(url);
  from.cookies.getAll().forEach((cookie) => response.cookies.set(cookie));
  return response;
}

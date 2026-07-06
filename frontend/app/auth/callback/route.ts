import { NextResponse } from "next/server";

import { createClient } from "@/lib/supabase/server";

/**
 * OAuth + email-link callback (PKCE code flow).
 *
 * Google sign-in, email confirmation, and password-recovery links all redirect
 * here with a `?code=`. We exchange it for a session (cookies set via the server
 * client) and forward to `next`.
 */
export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/dashboard";

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  return NextResponse.redirect(
    `${origin}/login?error=${encodeURIComponent("Sign-in link is invalid or has expired.")}`,
  );
}

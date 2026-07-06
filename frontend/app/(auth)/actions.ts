"use server";

/**
 * Authentication server actions.
 *
 * Sign-up / sign-in / password reset are performed directly against Supabase Auth
 * (the backend never sees credentials). Each action redirects on completion,
 * carrying an `error` or `message` query param the page renders. `redirect()`
 * throws internally, so it must be called outside try/catch.
 */

import { revalidatePath } from "next/cache";
import { redirect } from "next/navigation";

import { getSiteURL } from "@/lib/site-url";
import { createClient } from "@/lib/supabase/server";

function str(formData: FormData, key: string): string {
  return String(formData.get(key) ?? "").trim();
}

export async function login(formData: FormData) {
  const email = str(formData, "email");
  const password = str(formData, "password");
  const redirectedFrom = str(formData, "redirectedFrom");

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });

  if (error) {
    redirect(`/login?error=${encodeURIComponent(error.message)}`);
  }

  revalidatePath("/", "layout");
  redirect(redirectedFrom || "/dashboard");
}

export async function signup(formData: FormData) {
  const email = str(formData, "email");
  const password = str(formData, "password");

  const supabase = await createClient();
  const siteUrl = await getSiteURL();

  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: { emailRedirectTo: `${siteUrl}/auth/callback?next=/dashboard` },
  });

  if (error) {
    redirect(`/signup?error=${encodeURIComponent(error.message)}`);
  }

  // If email confirmation is disabled, Supabase returns a live session and the
  // user is already signed in. Otherwise, they must confirm via email first.
  if (data.session) {
    revalidatePath("/", "layout");
    redirect("/dashboard");
  }

  redirect("/signup?message=check-email");
}

export async function signInWithGoogle() {
  const supabase = await createClient();
  const siteUrl = await getSiteURL();

  const { data, error } = await supabase.auth.signInWithOAuth({
    provider: "google",
    options: { redirectTo: `${siteUrl}/auth/callback?next=/dashboard` },
  });

  if (error) {
    redirect(`/login?error=${encodeURIComponent(error.message)}`);
  }

  if (data.url) {
    redirect(data.url);
  }
}

export async function forgotPassword(formData: FormData) {
  const email = str(formData, "email");

  const supabase = await createClient();
  const siteUrl = await getSiteURL();

  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${siteUrl}/auth/callback?next=/reset-password`,
  });

  if (error) {
    redirect(`/forgot-password?error=${encodeURIComponent(error.message)}`);
  }

  redirect("/forgot-password?message=check-email");
}

export async function updatePassword(formData: FormData) {
  const password = str(formData, "password");

  // Requires the recovery session established by /auth/callback.
  const supabase = await createClient();
  const { error } = await supabase.auth.updateUser({ password });

  if (error) {
    redirect(`/reset-password?error=${encodeURIComponent(error.message)}`);
  }

  revalidatePath("/", "layout");
  redirect("/login?message=password-updated");
}

export async function signOut() {
  const supabase = await createClient();
  await supabase.auth.signOut();
  revalidatePath("/", "layout");
  redirect("/login");
}

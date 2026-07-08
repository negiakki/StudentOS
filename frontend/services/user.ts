/**
 * User profile API service. Built on lib/api.ts.
 * `/users/me` creates the StudentOS profile on first call, so it is safe to read.
 */

import { apiFetch } from "@/lib/api";
import type { UserProfile } from "@/types/user";

/** The current user's profile (created on first sign-in). */
export async function getProfile(accessToken: string): Promise<UserProfile> {
  return apiFetch<UserProfile>("/users/me", { accessToken });
}

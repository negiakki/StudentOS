/** User profile, mirroring the backend UserProfile schema. */
export interface UserProfile {
  id: string;
  email: string;
  full_name: string | null;
  college: string | null;
  degree: string | null;
  onboarding_completed: boolean;
  created_at: string;
  updated_at: string;
}

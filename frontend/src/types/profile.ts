export interface ProfileResponse {
  user_id: string;
  experience_level: string | null;
  decision_style: string | null;
  onboarding_completed: boolean;
  preferred_depth: string;
  top_assets: string[] | null;
  top_categories: string[] | null;
  updated_at: string;
}

export interface ActivityResponse {
  user_id: string;
  activity_data: Record<string, unknown>;
  updated_at: string;
}

export interface IceBreakingRequest {
  experience_level: "beginner" | "intermediate" | "expert";
  decision_style: "feeling" | "logic" | "balanced";
}

export interface PageVisitRequest {
  page_id: string;
}

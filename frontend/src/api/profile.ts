import apiClient from "./client";
import type {
  ActivityResponse,
  IceBreakingRequest,
  PageVisitRequest,
  ProfileResponse,
} from "../types/profile";

export async function getProfile(): Promise<ProfileResponse> {
  const { data } = await apiClient.get<ProfileResponse>("/v1/profile");
  return data;
}

export async function submitIceBreaking(
  body: IceBreakingRequest,
): Promise<ProfileResponse> {
  const { data } = await apiClient.post<ProfileResponse>(
    "/v1/profile/ice-breaking",
    body,
  );
  return data;
}

export async function getActivity(): Promise<ActivityResponse> {
  const { data } = await apiClient.get<ActivityResponse>(
    "/v1/profile/activity",
  );
  return data;
}

export async function recordPageVisit(
  body: PageVisitRequest,
): Promise<ActivityResponse> {
  const { data } = await apiClient.post<ActivityResponse>(
    "/v1/profile/activity/page-visit",
    body,
  );
  return data;
}

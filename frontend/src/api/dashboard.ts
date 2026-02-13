import apiClient from "./client";
import type { DashboardSummaryResponse } from "../types/api";

export async function fetchDashboardSummary(): Promise<DashboardSummaryResponse> {
  const { data } = await apiClient.get<DashboardSummaryResponse>(
    "/v1/dashboard/summary",
  );
  return data;
}

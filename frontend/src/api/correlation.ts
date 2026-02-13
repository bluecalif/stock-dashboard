import apiClient from "./client";
import type { CorrelationResponse } from "../types/api";

interface CorrelationParams {
  asset_ids?: string;
  start_date?: string;
  end_date?: string;
  window?: number;
}

export async function fetchCorrelation(
  params: CorrelationParams = {},
): Promise<CorrelationResponse> {
  const { data } = await apiClient.get<CorrelationResponse>(
    "/v1/correlation",
    { params },
  );
  return data;
}

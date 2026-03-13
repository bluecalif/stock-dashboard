import apiClient from "./client";
import type { CorrelationResponse, CorrelationAnalysisResponse } from "../types/api";

interface CorrelationParams {
  asset_ids?: string;
  start_date?: string;
  end_date?: string;
  window?: number;
}

interface CorrelationAnalysisParams extends CorrelationParams {
  threshold?: number;
  top_n?: number;
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

export async function fetchCorrelationAnalysis(
  params: CorrelationAnalysisParams = {},
): Promise<CorrelationAnalysisResponse> {
  const { data } = await apiClient.get<CorrelationAnalysisResponse>(
    "/v1/correlation/analysis",
    { params },
  );
  return data;
}

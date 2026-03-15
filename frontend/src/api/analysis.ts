import apiClient from "./client";
import type {
  SignalAccuracyResponse,
  IndicatorComparisonResponse,
} from "../types/api";

interface SignalAccuracyParams {
  asset_id: string;
  strategy_id: string;
  forward_days?: number;
}

interface IndicatorComparisonParams {
  asset_id: string;
  forward_days?: number;
}

export async function fetchSignalAccuracy(
  params: SignalAccuracyParams,
): Promise<SignalAccuracyResponse> {
  const { data } = await apiClient.get<SignalAccuracyResponse>(
    "/v1/analysis/signal-accuracy",
    { params },
  );
  return data;
}

export async function fetchIndicatorComparison(
  params: IndicatorComparisonParams,
): Promise<IndicatorComparisonResponse> {
  const { data } = await apiClient.get<IndicatorComparisonResponse>(
    "/v1/analysis/indicator-comparison",
    { params },
  );
  return data;
}

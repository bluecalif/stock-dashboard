import apiClient from "./client";
import type {
  SignalAccuracyResponse,
  IndicatorComparisonResponse,
  IndicatorSignalListResponse,
  IndicatorComparisonResponseV2,
} from "../types/api";

// ---------------------------------------------------------------------------
// Strategy-based (Phase D 하위호환)
// ---------------------------------------------------------------------------

interface SignalAccuracyByStrategyParams {
  asset_id: string;
  strategy_id: string;
  forward_days?: number;
  include_details?: boolean;
}

export async function fetchSignalAccuracy(
  params: SignalAccuracyByStrategyParams,
): Promise<SignalAccuracyResponse> {
  const { data } = await apiClient.get<SignalAccuracyResponse>(
    "/v1/analysis/signal-accuracy",
    { params },
  );
  return data;
}

interface IndicatorComparisonParams {
  asset_id: string;
  forward_days?: number;
  mode?: "indicator" | "strategy";
}

export async function fetchIndicatorComparison(
  params: IndicatorComparisonParams,
): Promise<IndicatorComparisonResponse> {
  const { data } = await apiClient.get<IndicatorComparisonResponse>(
    "/v1/analysis/indicator-comparison",
    { params: { ...params, mode: "strategy" } },
  );
  return data;
}

// ---------------------------------------------------------------------------
// Indicator-based (DR.1~DR.4)
// ---------------------------------------------------------------------------

interface IndicatorSignalParams {
  asset_id: string;
  indicator_id: string;
  start_date?: string;
  end_date?: string;
}

export async function fetchIndicatorSignals(
  params: IndicatorSignalParams,
): Promise<IndicatorSignalListResponse> {
  const { data } = await apiClient.get<IndicatorSignalListResponse>(
    "/v1/analysis/indicator-signals",
    { params },
  );
  return data;
}

interface IndicatorAccuracyParams {
  asset_id: string;
  indicator_id: string;
  forward_days?: number;
  include_details?: boolean;
}

export async function fetchIndicatorAccuracy(
  params: IndicatorAccuracyParams,
): Promise<SignalAccuracyResponse> {
  const { data } = await apiClient.get<SignalAccuracyResponse>(
    "/v1/analysis/signal-accuracy",
    { params },
  );
  return data;
}

export async function fetchIndicatorComparisonV2(
  params: { asset_id: string; forward_days?: number },
): Promise<IndicatorComparisonResponseV2> {
  const { data } = await apiClient.get<IndicatorComparisonResponseV2>(
    "/v1/analysis/indicator-comparison",
    { params: { ...params, mode: "indicator" } },
  );
  return data;
}

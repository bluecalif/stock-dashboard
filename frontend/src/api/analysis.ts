import apiClient from "./client";
import type {
  SignalAccuracyResponse,
  IndicatorSignalListResponse,
  IndicatorComparisonResponseV2,
  StrategyBacktestRequest,
  StrategyBacktestResponse,
} from "../types/api";

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
  start_date?: string;
  end_date?: string;
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

// ---------------------------------------------------------------------------
// Strategy Backtest (E.4)
// ---------------------------------------------------------------------------

export async function fetchStrategyBacktest(
  params: StrategyBacktestRequest,
): Promise<StrategyBacktestResponse> {
  const { data } = await apiClient.post<StrategyBacktestResponse>(
    "/v1/analysis/strategy-backtest",
    params,
  );
  return data;
}

export async function fetchIndicatorComparisonV2(
  params: { asset_id: string; forward_days?: number; start_date?: string; end_date?: string },
): Promise<IndicatorComparisonResponseV2> {
  const { data } = await apiClient.get<IndicatorComparisonResponseV2>(
    "/v1/analysis/indicator-comparison",
    { params: { ...params, mode: "indicator" } },
  );
  return data;
}

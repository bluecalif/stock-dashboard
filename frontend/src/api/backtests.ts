import apiClient from "./client";
import type {
  BacktestRunRequest,
  BacktestRunResponse,
  EquityCurveResponse,
  TradeLogResponse,
} from "../types/api";

interface BacktestListParams {
  strategy_id?: string;
  asset_id?: string;
  limit?: number;
  offset?: number;
}

export async function fetchBacktests(
  params: BacktestListParams = {},
): Promise<BacktestRunResponse[]> {
  const { data } = await apiClient.get<BacktestRunResponse[]>(
    "/v1/backtests",
    { params },
  );
  return data;
}

export async function fetchBacktestDetail(
  runId: string,
): Promise<BacktestRunResponse> {
  const { data } = await apiClient.get<BacktestRunResponse>(
    `/v1/backtests/${runId}`,
  );
  return data;
}

export async function fetchEquity(
  runId: string,
): Promise<EquityCurveResponse[]> {
  const { data } = await apiClient.get<EquityCurveResponse[]>(
    `/v1/backtests/${runId}/equity`,
  );
  return data;
}

export async function fetchTrades(
  runId: string,
): Promise<TradeLogResponse[]> {
  const { data } = await apiClient.get<TradeLogResponse[]>(
    `/v1/backtests/${runId}/trades`,
  );
  return data;
}

export async function runBacktest(
  req: BacktestRunRequest,
): Promise<BacktestRunResponse> {
  const { data } = await apiClient.post<BacktestRunResponse>(
    "/v1/backtests/run",
    req,
  );
  return data;
}

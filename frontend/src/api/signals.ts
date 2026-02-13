import apiClient from "./client";
import type { SignalDailyResponse } from "../types/api";

interface SignalParams {
  asset_id?: string;
  strategy_id?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export async function fetchSignals(
  params: SignalParams = {},
): Promise<SignalDailyResponse[]> {
  const { data } = await apiClient.get<SignalDailyResponse[]>("/v1/signals", {
    params,
  });
  return data;
}

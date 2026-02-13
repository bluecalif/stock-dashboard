import apiClient from "./client";
import type { FactorDailyResponse } from "../types/api";

interface FactorParams {
  asset_id?: string;
  factor_name?: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export async function fetchFactors(
  params: FactorParams = {},
): Promise<FactorDailyResponse[]> {
  const { data } = await apiClient.get<FactorDailyResponse[]>("/v1/factors", {
    params,
  });
  return data;
}

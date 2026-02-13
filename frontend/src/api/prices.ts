import apiClient from "./client";
import type { PriceDailyResponse } from "../types/api";

interface PriceParams {
  asset_id: string;
  start_date?: string;
  end_date?: string;
  limit?: number;
  offset?: number;
}

export async function fetchPrices(
  params: PriceParams,
): Promise<PriceDailyResponse[]> {
  const { data } = await apiClient.get<PriceDailyResponse[]>(
    "/v1/prices/daily",
    { params },
  );
  return data;
}

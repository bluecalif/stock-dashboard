import apiClient from "./client";
import type { AssetResponse } from "../types/api";

export async function fetchAssets(
  isActive?: boolean,
): Promise<AssetResponse[]> {
  const params: Record<string, unknown> = {};
  if (isActive !== undefined) params.is_active = isActive;
  const { data } = await apiClient.get<AssetResponse[]>("/v1/assets", {
    params,
  });
  return data;
}

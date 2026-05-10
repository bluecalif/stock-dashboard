import apiClient from "./client";
import type {
  ReplayRequest,
  ReplayResponse,
  StrategyRequest,
  StrategyResponse,
  PortfolioRequest,
  PortfolioResponse,
} from "../types/api";

export async function fetchReplay(req: ReplayRequest): Promise<ReplayResponse> {
  const { data } = await apiClient.post<ReplayResponse>(
    "/v1/silver/simulate/replay",
    req,
  );
  return data;
}

export async function fetchStrategy(req: StrategyRequest): Promise<StrategyResponse> {
  const { data } = await apiClient.post<StrategyResponse>(
    "/v1/silver/simulate/strategy",
    req,
  );
  return data;
}

export async function fetchPortfolio(req: PortfolioRequest): Promise<PortfolioResponse> {
  const { data } = await apiClient.post<PortfolioResponse>(
    "/v1/silver/simulate/portfolio",
    req,
  );
  return data;
}

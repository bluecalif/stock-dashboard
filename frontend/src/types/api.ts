// Backend Pydantic 스키마 1:1 매칭 TypeScript 인터페이스

// --- Common ---
export interface ErrorResponse {
  detail: string;
  error_code: string;
}

// --- Asset ---
export interface AssetResponse {
  asset_id: string;
  name: string;
  category: string;
  is_active: boolean;
}

// --- Price ---
export interface PriceDailyResponse {
  asset_id: string;
  date: string; // ISO date "YYYY-MM-DD"
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source: string;
}

// --- Factor ---
export interface FactorDailyResponse {
  asset_id: string;
  date: string;
  factor_name: string;
  version: string;
  value: number;
}

// --- Signal ---
export interface SignalDailyResponse {
  id: number;
  asset_id: string;
  date: string;
  strategy_id: string;
  signal: number;
  score: number | null;
  action: string | null;
  meta_json: Record<string, unknown> | null;
}

// --- Backtest ---
export interface BacktestRunRequest {
  strategy_id: string;
  asset_id: string;
  start_date?: string | null;
  end_date?: string | null;
  initial_cash?: number;
  commission_pct?: number;
}

export interface BacktestRunResponse {
  run_id: string; // UUID
  strategy_id: string;
  asset_id: string;
  status: string;
  config_json: Record<string, unknown>;
  metrics_json: Record<string, unknown> | null;
  started_at: string; // ISO datetime
  ended_at: string | null;
}

export interface EquityCurveResponse {
  run_id: string;
  date: string;
  equity: number;
  drawdown: number;
}

export interface TradeLogResponse {
  id: number;
  run_id: string;
  asset_id: string;
  entry_date: string;
  entry_price: number;
  exit_date: string | null;
  exit_price: number | null;
  side: string;
  shares: number;
  pnl: number | null;
  cost: number | null;
}

// --- Dashboard ---
export interface AssetSummary {
  asset_id: string;
  name: string;
  latest_price: number | null;
  price_change_pct: number | null;
  latest_signal: Record<string, string> | null;
}

export interface DashboardSummaryResponse {
  assets: AssetSummary[];
  recent_backtests: BacktestRunResponse[];
  updated_at: string;
}

// --- Correlation ---
export interface CorrelationPeriod {
  start: string;
  end: string;
  window: number;
}

export interface CorrelationResponse {
  asset_ids: string[];
  matrix: number[][];
  period: CorrelationPeriod;
}

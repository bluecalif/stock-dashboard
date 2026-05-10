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
  asset_names: Record<string, string>;
}

export interface CorrelationGroup {
  group_id: number;
  asset_ids: string[];
  avg_correlation: number;
}

export interface AssetPair {
  asset_a: string;
  asset_b: string;
  correlation: number;
}

export interface CorrelationAnalysisResponse {
  groups: CorrelationGroup[];
  top_pairs: AssetPair[];
  period: CorrelationPeriod;
  asset_names: Record<string, string>;
}

// --- Spread ---
export interface ConvergenceEvent {
  date: string;
  z_score: number;
  direction: "convergence" | "divergence";
}

export interface NormalizedPrices {
  asset_a: number[];
  asset_b: number[];
}

// --- Analysis ---
export interface SignalAccuracyResponse {
  asset_id: string;
  strategy_id: string;
  forward_days: number;
  total_signals: number;
  evaluated_signals: number;
  buy_count: number;
  buy_success_count: number;
  buy_success_rate: number | null;
  avg_return_after_buy: number | null;
  sell_count: number;
  sell_success_count: number;
  sell_success_rate: number | null;
  avg_return_after_sell: number | null;
  insufficient_data: boolean;
}

export interface IndicatorComparisonRow {
  strategy_id: string;
  rank: number;
  buy_success_rate: number | null;
  sell_success_rate: number | null;
  avg_return_after_buy: number | null;
  avg_return_after_sell: number | null;
  evaluated_signals: number;
  insufficient_data: boolean;
}

export interface IndicatorComparisonResponse {
  asset_id: string;
  forward_days: number;
  strategies: IndicatorComparisonRow[];
  total_strategies: number;
}

// --- Indicator Signals (DR.1) ---
export interface IndicatorSignalItem {
  date: string;
  signal: number; // 1 (buy), -1 (sell), 0 (warning)
  label: string;
  value: number;
  entry_price: number;
}

export interface IndicatorSignalListResponse {
  asset_id: string;
  indicator_id: string;
  signals: IndicatorSignalItem[];
  total_signals: number;
}

// --- Indicator Comparison V2 (DR.3) ---
export interface IndicatorComparisonResponseV2 {
  asset_id: string;
  forward_days: number;
  indicators: IndicatorComparisonRow[];
  total_indicators: number;
}

// --- Strategy Backtest (E.4) ---
export interface StrategyBacktestRequest {
  asset_id: string;
  strategy_name: "momentum" | "contrarian" | "risk_aversion";
  period?: "6M" | "1Y" | "2Y" | "3Y";
  initial_cash?: number;
}

export interface EquityCurveItem {
  date: string;
  equity: number;
  drawdown: number;
  bh_equity: number | null;
}

export interface TradeItem {
  entry_date: string;
  exit_date: string | null;
  entry_price: number;
  exit_price: number | null;
  pnl: number | null;
  pnl_pct: number | null;
  holding_days: number;
  narrative: string;
  is_best: boolean;
  is_worst: boolean;
}

export interface AnnualPerformanceItem {
  year: number;
  return_pct: number;
  pnl_amount: number;
  mdd: number;
  num_trades: number;
  win_rate: number;
  is_favorable: boolean;
  is_partial_year: boolean;
  trading_days: number;
}

export interface MetricsItem {
  total_return: number;
  cagr: number;
  mdd: number;
  volatility: number;
  sharpe: number;
  sortino: number;
  calmar: number;
  win_rate: number;
  num_trades: number;
  avg_trade_pnl: number;
  turnover: number;
  bh_total_return: number | null;
  bh_cagr: number | null;
  excess_return: number | null;
}

export interface StrategyBacktestResponse {
  asset_id: string;
  strategy_name: string;
  strategy_label: string;
  period: string;
  initial_cash: number;
  metrics: MetricsItem;
  equity_curve: EquityCurveItem[];
  trades: TradeItem[];
  annual_performance: AnnualPerformanceItem[];
  summary_narrative: string;
  loss_avoided: number | null;
}

export interface SpreadResponse {
  asset_a: string;
  asset_b: string;
  dates: string[];
  spread_values: number[];
  z_scores: number[];
  mean: number;
  std: number;
  current_z_score: number;
  convergence_events: ConvergenceEvent[];
  asset_names: Record<string, string>;
  normalized_prices: NormalizedPrices | null;
}

// ── Silver Simulation (Phase 2 API, 마스터플랜 §3) ──────────────────────────

export interface EquityPoint {
  date: string;       // "YYYY-MM-DD"
  krw_value: number;
  local_value: number;
  shares: number;
}

export interface SimKpi {
  final_asset_krw: number;
  total_return: number;       // 0.2839 = +28.39%
  annualized_return: number;  // 0.1440 = +14.40%
  yearly_worst_mdd: number;   // -0.2624 = -26.24%
  total_deposit_krw: number;
}

// Tab A — replay
export interface ReplayRequest {
  asset_code: string;
  monthly_amount: number;
  period_years: 3 | 5 | 10;
  base_currency?: "KRW";
}

export interface ReplayResponse {
  asset_code: string;
  curve: EquityPoint[];
  kpi: SimKpi;
}

// Tab B — strategy
export interface StrategyRequest {
  asset_code: string;
  strategy: "A" | "B";
  monthly_amount: number;
  period_years: 3 | 5 | 10;
}

export interface StrategyResponse {
  asset_code: string;
  strategy: string;
  curve: EquityPoint[];
  kpi: SimKpi;
  event_count: number;
}

// Tab C — portfolio
export interface PortfolioRequest {
  preset_key: string;
  monthly_amount: number;
  period_years: 3 | 5 | 10;
}

export interface PortfolioResponse {
  preset_key: string;
  preset_name: string;
  curve: EquityPoint[];
  kpi: SimKpi;
}

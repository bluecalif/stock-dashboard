"""분석 API 스키마 — 성공률 / 예측력 비교 / 전략 백테스트."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Signal Accuracy (D.2)
# ---------------------------------------------------------------------------

class SignalAccuracyResponse(BaseModel):
    """매수/매도 성공률 응답."""

    asset_id: str
    strategy_id: str
    forward_days: int
    total_signals: int
    evaluated_signals: int

    buy_count: int = 0
    buy_success_count: int = 0
    buy_success_rate: float | None = None
    avg_return_after_buy: float | None = None

    sell_count: int = 0
    sell_success_count: int = 0
    sell_success_rate: float | None = None
    avg_return_after_sell: float | None = None

    insufficient_data: bool = False


# ---------------------------------------------------------------------------
# Indicator Comparison (D.3)
# ---------------------------------------------------------------------------

class IndicatorComparisonResponse(BaseModel):
    """전략별 예측력 비교 행."""

    strategy_id: str
    rank: int
    buy_success_rate: float | None = None
    sell_success_rate: float | None = None
    avg_return_after_buy: float | None = None
    avg_return_after_sell: float | None = None
    evaluated_signals: int = 0
    insufficient_data: bool = False


class IndicatorComparisonListResponse(BaseModel):
    """예측력 비교 전체 응답."""

    asset_id: str
    forward_days: int
    strategies: list[IndicatorComparisonResponse]
    total_strategies: int = Field(description="비교 전략 수")


# ---------------------------------------------------------------------------
# DR.1: Indicator Signals
# ---------------------------------------------------------------------------

class IndicatorSignalItem(BaseModel):
    """지표 시그널 항목."""

    date: str
    signal: int = Field(description="1 (buy), -1 (sell), 0 (warning)")
    label: str
    value: float
    entry_price: float


class IndicatorSignalListResponse(BaseModel):
    """지표 시그널 목록 응답."""

    asset_id: str
    indicator_id: str
    signals: list[IndicatorSignalItem]
    total_signals: int


# ---------------------------------------------------------------------------
# DR.3: Indicator Comparison (RSI vs MACD)
# ---------------------------------------------------------------------------

class IndicatorComparisonListResponseV2(BaseModel):
    """지표 비교 응답 (RSI vs MACD)."""

    asset_id: str
    forward_days: int
    indicators: list[IndicatorComparisonResponse]
    total_indicators: int = Field(description="비교 지표 수")


# ---------------------------------------------------------------------------
# E.4: Strategy Backtest
# ---------------------------------------------------------------------------

class StrategyBacktestRequest(BaseModel):
    """전략 백테스트 요청."""

    asset_id: str = Field(description="자산 ID (예: 005930)")
    strategy_name: Literal["momentum", "contrarian", "risk_aversion"] = Field(
        description="전략 이름"
    )
    period: Literal["6M", "1Y", "2Y", "3Y"] = Field(
        default="2Y", description="기간 프리셋"
    )
    initial_cash: float = Field(
        default=100_000_000, gt=0, description="초기 투자금 (원)"
    )


class EquityCurveItem(BaseModel):
    """에쿼티 커브 데이터 포인트."""

    date: str
    equity: float
    drawdown: float
    bh_equity: float | None = None


class TradeItem(BaseModel):
    """거래 기록 + 내러티브."""

    entry_date: str
    exit_date: str | None = None
    entry_price: float
    exit_price: float | None = None
    pnl: float | None = None
    pnl_pct: float | None = None
    holding_days: int = 0
    narrative: str = ""
    is_best: bool = False
    is_worst: bool = False


class AnnualPerformanceItem(BaseModel):
    """연간 성과 데이터."""

    year: int
    return_pct: float
    pnl_amount: float
    mdd: float
    num_trades: int
    win_rate: float
    is_favorable: bool
    is_partial_year: bool = False
    trading_days: int = 0


class MetricsItem(BaseModel):
    """성과 지표."""

    total_return: float
    cagr: float
    mdd: float
    volatility: float
    sharpe: float
    sortino: float
    calmar: float
    win_rate: float
    num_trades: int
    avg_trade_pnl: float
    turnover: float
    bh_total_return: float | None = None
    bh_cagr: float | None = None
    excess_return: float | None = None


class StrategyBacktestResponse(BaseModel):
    """전략 백테스트 응답."""

    asset_id: str
    strategy_name: str
    strategy_label: str
    period: str
    initial_cash: float
    metrics: MetricsItem
    equity_curve: list[EquityCurveItem]
    trades: list[TradeItem]
    annual_performance: list[AnnualPerformanceItem]
    summary_narrative: str
    loss_avoided: float | None = None

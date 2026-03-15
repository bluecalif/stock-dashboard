"""분석 API 스키마 — 성공률 / 예측력 비교."""

from __future__ import annotations

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

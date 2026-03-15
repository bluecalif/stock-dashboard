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

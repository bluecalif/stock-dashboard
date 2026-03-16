"""Indicator comparison service — rank strategies/indicators by prediction accuracy.

D.3: Compare buy/sell success rates across strategies and rank them.
DR.3: Compare individual indicators (RSI vs MACD) by accuracy.
DI.5: start_date/end_date support for period sync with signals tab.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass

from sqlalchemy.orm import Session

from api.services.analysis.signal_accuracy_service import (
    SignalAccuracyResult,
    compute_accuracy_all_strategies,
    compute_indicator_accuracy,
)

DEFAULT_STRATEGY_IDS = ["momentum", "trend", "mean_reversion"]
DEFAULT_INDICATOR_IDS = ["rsi_14", "macd"]


@dataclass
class IndicatorComparisonRow:
    """One row in the indicator comparison ranking table."""

    strategy_id: str
    rank: int
    buy_success_rate: float | None
    sell_success_rate: float | None
    avg_return_after_buy: float | None
    avg_return_after_sell: float | None
    evaluated_signals: int
    insufficient_data: bool


def _sort_key(result: SignalAccuracyResult) -> float:
    """Compute a composite score for ranking.

    Average of available success rates. Strategies with no rate get -1
    so they sort to the bottom.
    """
    rates = [
        r for r in (result.buy_success_rate, result.sell_success_rate)
        if r is not None
    ]
    if not rates:
        return -1.0
    return sum(rates) / len(rates)


def compare_indicator_accuracy(
    db: Session,
    asset_id: str,
    strategy_ids: list[str] | None = None,
    *,
    forward_days: int = 5,
) -> list[IndicatorComparisonRow]:
    """Compare prediction accuracy across strategies and rank by success rate.

    Args:
        db: SQLAlchemy session.
        asset_id: Target asset (e.g. "005930").
        strategy_ids: Strategies to compare. Defaults to all 3.
        forward_days: Look-ahead period for return calculation.

    Returns:
        List of IndicatorComparisonRow sorted by rank (1 = best).
    """
    if strategy_ids is None:
        strategy_ids = DEFAULT_STRATEGY_IDS

    results = compute_accuracy_all_strategies(
        db, asset_id, strategy_ids, forward_days=forward_days,
    )

    # Sort by composite score descending (best first)
    sorted_results = sorted(results, key=_sort_key, reverse=True)

    return [
        IndicatorComparisonRow(
            strategy_id=r.strategy_id,
            rank=i + 1,
            buy_success_rate=r.buy_success_rate,
            sell_success_rate=r.sell_success_rate,
            avg_return_after_buy=r.avg_return_after_buy,
            avg_return_after_sell=r.avg_return_after_sell,
            evaluated_signals=r.evaluated_signals,
            insufficient_data=r.insufficient_data,
        )
        for i, r in enumerate(sorted_results)
    ]


# ---------------------------------------------------------------------------
# DR.3: Indicator-based comparison (RSI vs MACD)
# ---------------------------------------------------------------------------

def compare_indicators(
    db: Session,
    asset_id: str,
    indicator_ids: list[str] | None = None,
    *,
    forward_days: int = 5,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    min_gap_days: int = 3,
) -> list[IndicatorComparisonRow]:
    """Compare prediction accuracy across individual indicators.

    Uses on-the-fly indicator signals (DR.1) instead of signal_daily.
    ATR is excluded by default (no buy/sell signals).

    Args:
        db: SQLAlchemy session.
        asset_id: Target asset (e.g. "005930").
        indicator_ids: Indicators to compare. Defaults to ["rsi_14", "macd"].
        forward_days: Look-ahead period for return calculation.
        start_date: Optional filter start (DI.5).
        end_date: Optional filter end (DI.5).
        min_gap_days: Minimum signal gap (DI.2).

    Returns:
        List of IndicatorComparisonRow sorted by rank (1 = best).
    """
    if indicator_ids is None:
        indicator_ids = DEFAULT_INDICATOR_IDS

    results = [
        compute_indicator_accuracy(
            db, asset_id, iid,
            forward_days=forward_days,
            start_date=start_date,
            end_date=end_date,
            min_gap_days=min_gap_days,
        )
        for iid in indicator_ids
    ]

    sorted_results = sorted(results, key=_sort_key, reverse=True)

    return [
        IndicatorComparisonRow(
            strategy_id=r.strategy_id,  # contains indicator_id
            rank=i + 1,
            buy_success_rate=r.buy_success_rate,
            sell_success_rate=r.sell_success_rate,
            avg_return_after_buy=r.avg_return_after_buy,
            avg_return_after_sell=r.avg_return_after_sell,
            evaluated_signals=r.evaluated_signals,
            insufficient_data=r.insufficient_data,
        )
        for i, r in enumerate(sorted_results)
    ]

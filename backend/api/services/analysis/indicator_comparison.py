"""Indicator comparison service — rank strategies by prediction accuracy.

D.3: Compare buy/sell success rates across strategies and rank them.
Reuses D.2's compute_accuracy_all_strategies().
"""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from api.services.analysis.signal_accuracy_service import (
    SignalAccuracyResult,
    compute_accuracy_all_strategies,
)

DEFAULT_STRATEGY_IDS = ["momentum", "trend", "mean_reversion"]


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

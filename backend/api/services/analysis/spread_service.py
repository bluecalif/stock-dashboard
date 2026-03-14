"""Spread analysis — normalized price ratio spread + z-score detection."""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy.orm import Session

from api.repositories import price_repo


@dataclass
class ConvergenceEvent:
    """A point where spread crosses a z-score threshold."""

    date: datetime.date
    z_score: float
    direction: str  # "convergence" or "divergence"


@dataclass
class SpreadResult:
    """Result of spread analysis between two assets."""

    asset_a: str
    asset_b: str
    dates: list[datetime.date]
    spread_values: list[float]
    z_scores: list[float]
    mean: float
    std: float
    current_z_score: float
    convergence_events: list[ConvergenceEvent] = field(default_factory=list)
    norm_a_values: list[float] = field(default_factory=list)
    norm_b_values: list[float] = field(default_factory=list)


def _build_close_series(
    db: Session,
    asset_id: str,
    start_date: datetime.date | None,
    end_date: datetime.date | None,
) -> pd.Series:
    """Fetch prices and build a close price series indexed by date."""
    prices = price_repo.get_prices(
        db, asset_id, start_date=start_date, end_date=end_date, limit=5000, offset=0
    )
    if not prices:
        return pd.Series(dtype=float)
    return pd.Series(
        {p.date: float(p.close) for p in prices},
        name=asset_id,
    ).sort_index()


def compute_spread(
    db: Session,
    asset_a: str,
    asset_b: str,
    *,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    z_threshold: float = 2.0,
) -> SpreadResult:
    """Compute normalized price ratio spread between two assets.

    Spread = (P_a / P_a[0]) / (P_b / P_b[0]) — ratio of normalized prices.
    Z-score = (spread - mean) / std over the window.

    Convergence events: points where |z-score| crosses z_threshold.
    """
    series_a = _build_close_series(db, asset_a, start_date, end_date)
    series_b = _build_close_series(db, asset_b, start_date, end_date)

    if series_a.empty or series_b.empty:
        raise ValueError(f"Insufficient price data for {asset_a} or {asset_b}")

    # Align on common dates
    df = pd.DataFrame({"a": series_a, "b": series_b}).dropna()
    if len(df) < 5:
        raise ValueError("Insufficient overlapping data points (need >= 5)")

    # Normalize to first value
    norm_a = df["a"] / df["a"].iloc[0]
    norm_b = df["b"] / df["b"].iloc[0]

    # Spread = ratio of normalized prices
    spread = norm_a / norm_b

    mean = float(spread.mean())
    std = float(spread.std())
    if std == 0:
        std = 1e-10  # avoid division by zero

    z_scores = ((spread - mean) / std).tolist()
    spread_values = spread.tolist()
    dates = [d for d in df.index]

    # Detect convergence/divergence events
    events: list[ConvergenceEvent] = []
    for i in range(1, len(z_scores)):
        prev_z = z_scores[i - 1]
        curr_z = z_scores[i]

        # Crossing into extreme zone (divergence)
        if abs(prev_z) < z_threshold <= abs(curr_z):
            events.append(ConvergenceEvent(
                date=dates[i],
                z_score=round(curr_z, 4),
                direction="divergence",
            ))
        # Crossing back from extreme zone (convergence)
        elif abs(prev_z) >= z_threshold > abs(curr_z):
            events.append(ConvergenceEvent(
                date=dates[i],
                z_score=round(curr_z, 4),
                direction="convergence",
            ))

    current_z = z_scores[-1] if z_scores else 0.0

    return SpreadResult(
        asset_a=asset_a,
        asset_b=asset_b,
        dates=dates,
        spread_values=[round(v, 6) for v in spread_values],
        z_scores=[round(z, 4) for z in z_scores],
        mean=round(mean, 6),
        std=round(std, 6),
        current_z_score=round(current_z, 4),
        convergence_events=events,
        norm_a_values=[round(v * 100, 4) for v in norm_a.tolist()],
        norm_b_values=[round(v * 100, 4) for v in norm_b.tolist()],
    )

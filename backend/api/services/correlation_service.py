"""Correlation service — on-the-fly pandas computation."""

from __future__ import annotations

import datetime

import pandas as pd
from sqlalchemy.orm import Session

from api.repositories import asset_repo, price_repo
from api.schemas.correlation import CorrelationPeriod, CorrelationResponse


def compute_correlation(
    db: Session,
    *,
    asset_ids: list[str] | None = None,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    window: int = 60,
) -> CorrelationResponse:
    """Compute return correlation matrix for given assets.

    Args:
        db: SQLAlchemy session.
        asset_ids: List of asset IDs. If None, use all active assets.
        start_date: Start date for price data.
        end_date: End date for price data.
        window: Number of recent trading days to use (default 60).

    Returns:
        CorrelationResponse with asset_ids, NxN matrix, and period info.

    Raises:
        ValueError: If fewer than 2 assets have data.
    """
    # Resolve asset IDs
    if not asset_ids:
        assets = asset_repo.get_all(db, is_active=True)
        asset_ids = [a.asset_id for a in assets]

    if len(asset_ids) < 2:
        raise ValueError("At least 2 assets required for correlation")

    # Fetch prices and build close price DataFrame
    frames: dict[str, pd.Series] = {}
    for aid in asset_ids:
        prices = price_repo.get_prices(
            db,
            aid,
            start_date=start_date,
            end_date=end_date,
            limit=5000,
            offset=0,
        )
        if prices:
            series = pd.Series(
                {p.date: p.close for p in prices},
                name=aid,
            )
            frames[aid] = series

    if len(frames) < 2:
        raise ValueError("Insufficient price data: need at least 2 assets with data")

    # Build DataFrame, sort by date, take last `window` rows
    df = pd.DataFrame(frames).sort_index()
    df = df.tail(window)

    # Compute returns and correlation
    returns = df.pct_change().dropna()
    if len(returns) < 2:
        raise ValueError("Insufficient data points for correlation calculation")

    corr = returns.corr()

    # Build response
    used_ids = list(corr.columns)
    matrix = corr.values.tolist()
    # Round values
    matrix = [[round(v, 4) if pd.notna(v) else 0.0 for v in row] for row in matrix]

    actual_start = df.index.min()
    actual_end = df.index.max()

    return CorrelationResponse(
        asset_ids=used_ids,
        matrix=matrix,
        period=CorrelationPeriod(
            start=actual_start,
            end=actual_end,
            window=len(df),
        ),
    )

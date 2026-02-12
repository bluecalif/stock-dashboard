"""Dashboard summary service — aggregates asset/price/signal/backtest data."""

from __future__ import annotations

import datetime

from sqlalchemy.orm import Session

from api.repositories import asset_repo, backtest_repo, price_repo, signal_repo
from api.schemas.backtest import BacktestRunResponse
from api.schemas.dashboard import AssetSummary, DashboardSummaryResponse


def get_dashboard_summary(db: Session) -> DashboardSummaryResponse:
    """Build dashboard summary: per-asset info + recent backtests.

    For each active asset:
      - latest price (close)
      - price change % vs previous day
      - latest signal per strategy

    Plus: 5 most recent backtest runs.
    """
    assets = asset_repo.get_all(db, is_active=True)

    summaries: list[AssetSummary] = []
    for asset in assets:
        # Latest price + change %
        latest_price = None
        price_change_pct = None
        prices = price_repo.get_prices(db, asset.asset_id, limit=2, offset=0)
        if prices:
            latest_price = prices[0].close
            if len(prices) >= 2:
                prev = prices[1].close
                if prev != 0:
                    price_change_pct = round((latest_price - prev) / prev * 100, 2)

        # Latest signals — one per strategy
        latest_signal = _get_latest_signals(db, asset.asset_id)

        summaries.append(
            AssetSummary(
                asset_id=asset.asset_id,
                name=asset.name,
                latest_price=latest_price,
                price_change_pct=price_change_pct,
                latest_signal=latest_signal if latest_signal else None,
            )
        )

    # Recent backtests (top 5)
    recent_runs = backtest_repo.get_runs(db, limit=5, offset=0)
    recent_backtests = [BacktestRunResponse.model_validate(r) for r in recent_runs]

    return DashboardSummaryResponse(
        assets=summaries,
        recent_backtests=recent_backtests,
        updated_at=datetime.datetime.now(tz=datetime.timezone.utc),
    )


def _get_latest_signals(db: Session, asset_id: str) -> dict | None:
    """Get the latest signal action for each strategy."""
    strategy_ids = ["momentum", "trend", "mean_reversion"]
    result = {}
    for sid in strategy_ids:
        sig = signal_repo.get_latest_signal(db, asset_id, strategy_id=sid)
        if sig and sig.action:
            result[sid] = sig.action
    return result or None

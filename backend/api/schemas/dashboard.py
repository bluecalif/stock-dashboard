"""대시보드 스키마."""

from __future__ import annotations

import datetime

from pydantic import BaseModel

from .backtest import BacktestRunResponse


class AssetSummary(BaseModel):
    asset_id: str
    name: str
    latest_price: float | None = None
    price_change_pct: float | None = None
    latest_signal: dict | None = None  # {strategy_id: action}


class DashboardSummaryResponse(BaseModel):
    assets: list[AssetSummary]
    recent_backtests: list[BacktestRunResponse]
    updated_at: datetime.datetime

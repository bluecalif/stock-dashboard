"""백테스트 스키마."""

from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BacktestRunRequest(BaseModel):
    strategy_id: str
    asset_id: str
    start_date: datetime.date | None = None
    end_date: datetime.date | None = None
    initial_cash: float = 10_000_000
    commission_pct: float = 0.001


class BacktestRunResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: UUID
    strategy_id: str
    asset_id: str
    status: str
    config_json: dict
    metrics_json: dict | None = None
    started_at: datetime.datetime
    ended_at: datetime.datetime | None = None


class EquityCurveResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    run_id: UUID
    date: datetime.date
    equity: float
    drawdown: float


class TradeLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_id: UUID
    asset_id: str
    entry_date: datetime.date
    entry_price: float
    exit_date: datetime.date | None = None
    exit_price: float | None = None
    side: str
    shares: float
    pnl: float | None = None
    cost: float | None = None

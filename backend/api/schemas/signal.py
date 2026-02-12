"""시그널 스키마."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict


class SignalDailyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    asset_id: str
    date: datetime.date
    strategy_id: str
    signal: int
    score: float | None = None
    action: str | None = None
    meta_json: dict | None = None

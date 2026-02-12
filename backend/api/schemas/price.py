"""가격 스키마."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict


class PriceDailyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: str
    date: datetime.date
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str

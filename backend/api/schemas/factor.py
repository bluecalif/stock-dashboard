"""팩터 스키마."""

from __future__ import annotations

import datetime

from pydantic import BaseModel, ConfigDict


class FactorDailyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: str
    date: datetime.date
    factor_name: str
    version: str
    value: float

"""시그널 스키마."""

from __future__ import annotations

import datetime
import math

from pydantic import BaseModel, ConfigDict, field_validator


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

    @field_validator("score", mode="before")
    @classmethod
    def nan_to_none(cls, v: float | None) -> float | None:
        if v is not None and isinstance(v, float) and math.isnan(v):
            return None
        return v

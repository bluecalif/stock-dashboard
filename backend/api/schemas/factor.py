"""팩터 스키마."""

from __future__ import annotations

import datetime
import math

from pydantic import BaseModel, ConfigDict, field_validator


class FactorDailyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: str
    date: datetime.date
    factor_name: str
    version: str
    value: float | None = None

    @field_validator("value", mode="before")
    @classmethod
    def nan_to_none(cls, v: float | None) -> float | None:
        if v is not None and isinstance(v, float) and math.isnan(v):
            return None
        return v

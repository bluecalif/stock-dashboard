"""상관행렬 스키마."""

from __future__ import annotations

import datetime

from pydantic import BaseModel


class CorrelationPeriod(BaseModel):
    start: datetime.date
    end: datetime.date
    window: int


class CorrelationResponse(BaseModel):
    asset_ids: list[str]
    matrix: list[list[float]]
    period: CorrelationPeriod

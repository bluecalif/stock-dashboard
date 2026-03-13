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


# --- Analysis (grouping / top pairs) ---

class CorrelationGroupSchema(BaseModel):
    group_id: int
    asset_ids: list[str]
    avg_correlation: float


class AssetPairSchema(BaseModel):
    asset_a: str
    asset_b: str
    correlation: float


class CorrelationAnalysisResponse(BaseModel):
    groups: list[CorrelationGroupSchema]
    top_pairs: list[AssetPairSchema]
    period: CorrelationPeriod

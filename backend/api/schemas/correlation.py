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
    asset_names: dict[str, str] = {}


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
    asset_names: dict[str, str] = {}


# --- Spread analysis ---

class ConvergenceEventSchema(BaseModel):
    date: datetime.date
    z_score: float
    direction: str  # "convergence" or "divergence"


class NormalizedPrices(BaseModel):
    asset_a: list[float]
    asset_b: list[float]


class SpreadResponse(BaseModel):
    asset_a: str
    asset_b: str
    dates: list[datetime.date]
    spread_values: list[float]
    z_scores: list[float]
    mean: float
    std: float
    current_z_score: float
    convergence_events: list[ConvergenceEventSchema]
    asset_names: dict[str, str] = {}
    normalized_prices: NormalizedPrices | None = None

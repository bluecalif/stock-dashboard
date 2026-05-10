"""Simulation API Pydantic schemas (Silver gen, 마스터플랜 §3)."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


# ── 공통 ─────────────────────────────────────────────────────────────────────


class EquityPointResponse(BaseModel):
    date: str
    krw_value: float
    local_value: float
    shares: float


class KpiResponse(BaseModel):
    final_asset_krw: float
    total_return: float
    annualized_return: float
    yearly_worst_mdd: float
    total_deposit_krw: int


# ── Tab A: replay ─────────────────────────────────────────────────────────────


class SimulateReplayRequest(BaseModel):
    asset_code: str = Field(..., description="자산 코드 (QQQ / KS200 / WBI / JEPI 등)")
    monthly_amount: int = Field(..., ge=100_000, le=10_000_000, description="월 적립금 (KRW)")
    period_years: Literal[3, 5, 10] = Field(10, description="시뮬레이션 기간 (연)")
    base_currency: Literal["KRW"] = Field("KRW", description="표시 통화")


class SimulateReplayResponse(BaseModel):
    asset_code: str
    curve: list[EquityPointResponse]
    kpi: KpiResponse


# ── Tab B: strategy ───────────────────────────────────────────────────────────


class SimulateStrategyRequest(BaseModel):
    asset_code: str = Field(..., description="자산 코드 (QQQ / SPY / KS200)")
    strategy: Literal["A", "B"] = Field(..., description="전략 종류")
    monthly_amount: int = Field(..., ge=100_000, le=10_000_000)
    period_years: Literal[3, 5, 10] = Field(10)


class SimulateStrategyResponse(BaseModel):
    asset_code: str
    strategy: str
    curve: list[EquityPointResponse]
    kpi: KpiResponse
    event_count: int = Field(0, description="SELL/BUY 이벤트 수")


# ── Tab C: portfolio ──────────────────────────────────────────────────────────


class SimulatePortfolioRequest(BaseModel):
    preset_key: str = Field(..., description="preset 키 (QQQ_TLT_BTC 등)")
    monthly_amount: int = Field(..., ge=100_000, le=10_000_000)
    period_years: Literal[3, 5, 10] = Field(10)


class SimulatePortfolioResponse(BaseModel):
    preset_key: str
    preset_name: str
    curve: list[EquityPointResponse]
    kpi: KpiResponse

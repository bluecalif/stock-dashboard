"""Silver gen simulation tools — Agentic chat용 (A-004: simulation_service 직접 호출)."""

from __future__ import annotations

import json
import logging

from langchain_core.tools import tool

from api.schemas.simulation import (
    SimulatePortfolioRequest,
    SimulateReplayRequest,
    SimulateStrategyRequest,
)
from api.services import simulation_service
from db.session import SessionLocal

logger = logging.getLogger(__name__)

PRESET_IDS = ["QQQ_TLT_BTC", "KS200_TLT_BTC", "TECH_TLT_BTC", "SEC_SKH_TLT_BTC"]
TAB_A_ASSETS = ["QQQ", "SPY", "KS200", "SCHD", "JEPI", "WBI"]
TAB_B_ASSETS = ["QQQ", "SPY", "KS200"]


@tool
def simulation_replay(
    asset_code: str,
    monthly_amount: int = 1_000_000,
    period_years: int = 10,
) -> str:
    """Tab A 적립식 단순 replay — 단일 자산 누적 자산가치 + KPI 산출.

    Args:
        asset_code: 자산 코드 (QQQ / SPY / KS200 / SCHD / JEPI / WBI)
        monthly_amount: 월 적립금 (원 단위, 기본 100만)
        period_years: 기간 (3 / 5 / 10년, 기본 10)
    """
    if asset_code not in TAB_A_ASSETS:
        return json.dumps({"error": f"허용 자산: {TAB_A_ASSETS}"}, ensure_ascii=False)

    db = SessionLocal()
    try:
        req = SimulateReplayRequest(
            asset_code=asset_code,
            monthly_amount=monthly_amount,
            period_years=period_years,
        )
        result = simulation_service.simulate_replay(db, req)
        return json.dumps(
            {
                "asset_code": result.asset_code,
                "kpi": {
                    "final_asset_krw": result.kpi.final_asset_krw,
                    "total_return": result.kpi.total_return,
                    "annualized_return": result.kpi.annualized_return,
                    "yearly_worst_mdd": result.kpi.yearly_worst_mdd,
                },
                "curve_length": len(result.curve),
            },
            ensure_ascii=False,
        )
    except Exception as e:
        logger.exception("simulation_replay tool failed")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        db.close()


@tool
def simulation_strategy(
    asset_code: str,
    strategy: str = "A",
    monthly_amount: int = 1_000_000,
    period_years: int = 10,
) -> str:
    """Tab B 자산 vs 전략 비교 — 단순 적립 vs 전략 A/B 성과 비교.

    Args:
        asset_code: 비교 자산 코드 (QQQ / SPY / KS200)
        strategy: "A" (고가매도+저가재매수) 또는 "B" (70/30 대기)
        monthly_amount: 월 적립금 (원 단위, 기본 100만)
        period_years: 기간 (3 / 5 / 10년, 기본 10)
    """
    if asset_code not in TAB_B_ASSETS:
        return json.dumps({"error": f"Tab B 허용 자산: {TAB_B_ASSETS}"}, ensure_ascii=False)
    if strategy not in ("A", "B"):
        return json.dumps({"error": "strategy는 'A' 또는 'B'"}, ensure_ascii=False)

    db = SessionLocal()
    try:
        req = SimulateStrategyRequest(
            asset_code=asset_code,
            strategy=strategy,
            monthly_amount=monthly_amount,
            period_years=period_years,
        )
        result = simulation_service.simulate_strategy(db, req)
        return json.dumps(
            {
                "asset_code": result.asset_code,
                "strategy": result.strategy,
                "kpi": {
                    "final_asset_krw": result.kpi.final_asset_krw,
                    "total_return": result.kpi.total_return,
                    "annualized_return": result.kpi.annualized_return,
                    "yearly_worst_mdd": result.kpi.yearly_worst_mdd,
                },
                "event_count": result.event_count,
                "curve_length": len(result.curve),
            },
            ensure_ascii=False,
        )
    except Exception as e:
        logger.exception("simulation_strategy tool failed")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        db.close()


@tool
def simulation_portfolio(
    preset_key: str,
    monthly_amount: int = 1_000_000,
    period_years: int = 10,
) -> str:
    """Tab C 포트폴리오 적립식 — 고정 비중 60/20/20 포트폴리오 성과.

    Args:
        preset_key: 포트폴리오 preset 키 (QQQ_TLT_BTC / KS200_TLT_BTC / TECH_TLT_BTC / SEC_SKH_TLT_BTC)
        monthly_amount: 월 적립금 (원 단위, 기본 100만)
        period_years: 기간 (3 / 5 / 10년, 기본 10)
    """
    if preset_key not in PRESET_IDS:
        return json.dumps({"error": f"허용 preset: {PRESET_IDS}"}, ensure_ascii=False)

    db = SessionLocal()
    try:
        req = SimulatePortfolioRequest(
            preset_key=preset_key,
            monthly_amount=monthly_amount,
            period_years=period_years,
        )
        result = simulation_service.simulate_portfolio(db, req)
        return json.dumps(
            {
                "preset_key": result.preset_key,
                "preset_name": result.preset_name,
                "kpi": {
                    "final_asset_krw": result.kpi.final_asset_krw,
                    "total_return": result.kpi.total_return,
                    "annualized_return": result.kpi.annualized_return,
                    "yearly_worst_mdd": result.kpi.yearly_worst_mdd,
                },
                "curve_length": len(result.curve),
            },
            ensure_ascii=False,
        )
    except Exception as e:
        logger.exception("simulation_portfolio tool failed")
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        db.close()

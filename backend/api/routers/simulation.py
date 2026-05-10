"""Simulation endpoints — Silver gen Tab A/B/C (마스터플랜 §3, §5.3)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.simulation import (
    SimulatePortfolioRequest,
    SimulatePortfolioResponse,
    SimulateReplayRequest,
    SimulateReplayResponse,
    SimulateStrategyRequest,
    SimulateStrategyResponse,
)
from api.services import simulation_service

router = APIRouter(prefix="/v1/silver/simulate", tags=["simulation"])


@router.post("/replay", response_model=SimulateReplayResponse)
def simulate_replay(
    req: SimulateReplayRequest,
    db: Session = Depends(get_db),
) -> SimulateReplayResponse:
    """Tab A — 단일 자산 적립식 replay."""
    try:
        return simulation_service.simulate_replay(db, req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategy", response_model=SimulateStrategyResponse)
def simulate_strategy(
    req: SimulateStrategyRequest,
    db: Session = Depends(get_db),
) -> SimulateStrategyResponse:
    """Tab B — 자산 vs 전략 (Strategy A: 고가매도/저가재매수, Strategy B: 70/30 대기)."""
    try:
        return simulation_service.simulate_strategy(db, req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio", response_model=SimulatePortfolioResponse)
def simulate_portfolio(
    req: SimulatePortfolioRequest,
    db: Session = Depends(get_db),
) -> SimulatePortfolioResponse:
    """Tab C — 고정 비중 포트폴리오 적립식 (연 리밸런싱)."""
    try:
        return simulation_service.simulate_portfolio(db, req)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

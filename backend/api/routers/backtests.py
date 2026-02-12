"""Backtest endpoints."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.repositories import backtest_repo
from api.schemas.backtest import (
    BacktestRunRequest,
    BacktestRunResponse,
    EquityCurveResponse,
    TradeLogResponse,
)
from api.schemas.common import PaginationParams
from api.services.backtest_service import run_backtest_on_demand

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["backtests"])


@router.post("/backtests/run", response_model=BacktestRunResponse, status_code=201)
def run_backtest_endpoint(
    request: BacktestRunRequest,
    db: Session = Depends(get_db),
) -> BacktestRunResponse:
    """Execute an on-demand backtest."""
    try:
        return run_backtest_on_demand(request, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error("Backtest execution failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/backtests", response_model=list[BacktestRunResponse])
def list_backtests(
    strategy_id: str | None = Query(default=None, description="전략 ID"),
    asset_id: str | None = Query(default=None, description="자산 ID"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> list[BacktestRunResponse]:
    """Return backtest runs with optional filters and pagination."""
    rows = backtest_repo.get_runs(
        db,
        strategy_id=strategy_id,
        asset_id=asset_id,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [BacktestRunResponse.model_validate(r) for r in rows]


@router.get("/backtests/{run_id}", response_model=BacktestRunResponse)
def get_backtest(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> BacktestRunResponse:
    """Return a single backtest run by ID."""
    row = backtest_repo.get_run_by_id(db, run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    return BacktestRunResponse.model_validate(row)


@router.get("/backtests/{run_id}/equity", response_model=list[EquityCurveResponse])
def get_backtest_equity(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> list[EquityCurveResponse]:
    """Return equity curve for a backtest run."""
    run = backtest_repo.get_run_by_id(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    rows = backtest_repo.get_equity_curve(db, run_id)
    return [EquityCurveResponse.model_validate(r) for r in rows]


@router.get("/backtests/{run_id}/trades", response_model=list[TradeLogResponse])
def get_backtest_trades(
    run_id: UUID,
    db: Session = Depends(get_db),
) -> list[TradeLogResponse]:
    """Return trade log for a backtest run."""
    run = backtest_repo.get_run_by_id(db, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Backtest run not found")
    rows = backtest_repo.get_trades(db, run_id)
    return [TradeLogResponse.model_validate(r) for r in rows]

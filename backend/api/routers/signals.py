"""Signal daily endpoints."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.repositories import signal_repo
from api.schemas.common import PaginationParams
from api.schemas.signal import SignalDailyResponse

router = APIRouter(prefix="/v1", tags=["signals"])


@router.get("/signals", response_model=list[SignalDailyResponse])
def list_signals(
    asset_id: str | None = Query(default=None, description="자산 ID"),
    strategy_id: str | None = Query(default=None, description="전략 ID"),
    start_date: datetime.date | None = Query(default=None, description="시작일 (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(default=None, description="종료일 (YYYY-MM-DD)"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> list[SignalDailyResponse]:
    """Return signal records with optional filters and pagination."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")
    rows = signal_repo.get_signals(
        db,
        asset_id=asset_id,
        strategy_id=strategy_id,
        start_date=start_date,
        end_date=end_date,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [SignalDailyResponse.model_validate(r) for r in rows]

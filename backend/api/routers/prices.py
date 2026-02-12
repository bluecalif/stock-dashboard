"""Price daily endpoints."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.repositories import price_repo
from api.schemas.common import PaginationParams
from api.schemas.price import PriceDailyResponse

router = APIRouter(prefix="/v1", tags=["prices"])


@router.get("/prices/daily", response_model=list[PriceDailyResponse])
def list_prices(
    asset_id: str = Query(..., description="자산 ID"),
    start_date: datetime.date | None = Query(default=None, description="시작일 (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(default=None, description="종료일 (YYYY-MM-DD)"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> list[PriceDailyResponse]:
    """Return daily prices for an asset with date filter and pagination."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")
    rows = price_repo.get_prices(
        db,
        asset_id,
        start_date=start_date,
        end_date=end_date,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [PriceDailyResponse.model_validate(r) for r in rows]

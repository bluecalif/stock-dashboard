"""Factor daily endpoints."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.repositories import factor_repo
from api.schemas.common import PaginationParams
from api.schemas.factor import FactorDailyResponse

router = APIRouter(prefix="/v1", tags=["factors"])


@router.get("/factors", response_model=list[FactorDailyResponse])
def list_factors(
    asset_id: str | None = Query(default=None, description="자산 ID"),
    factor_name: str | None = Query(default=None, description="팩터 이름"),
    start_date: datetime.date | None = Query(default=None, description="시작일 (YYYY-MM-DD)"),
    end_date: datetime.date | None = Query(default=None, description="종료일 (YYYY-MM-DD)"),
    pagination: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> list[FactorDailyResponse]:
    """Return factor records with optional filters and pagination."""
    if start_date and end_date and start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be <= end_date")
    rows = factor_repo.get_factors(
        db,
        asset_id=asset_id,
        factor_name=factor_name,
        start_date=start_date,
        end_date=end_date,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    return [FactorDailyResponse.model_validate(r) for r in rows]

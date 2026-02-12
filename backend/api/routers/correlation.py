"""Correlation endpoints."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.correlation import CorrelationResponse
from api.services.correlation_service import compute_correlation

router = APIRouter(prefix="/v1", tags=["correlation"])


@router.get("/correlation", response_model=CorrelationResponse)
def get_correlation(
    asset_ids: str | None = Query(
        default=None,
        description="콤마 구분 자산 ID (예: KS200,005930,BTC). 미지정 시 전체 active 자산",
    ),
    start_date: datetime.date | None = Query(default=None, description="시작일"),
    end_date: datetime.date | None = Query(default=None, description="종료일"),
    window: int = Query(default=60, ge=5, le=500, description="수익률 윈도우 (거래일)"),
    db: Session = Depends(get_db),
) -> CorrelationResponse:
    """Return correlation matrix of asset returns."""
    parsed_ids = None
    if asset_ids:
        parsed_ids = [aid.strip() for aid in asset_ids.split(",") if aid.strip()]

    try:
        return compute_correlation(
            db,
            asset_ids=parsed_ids,
            start_date=start_date,
            end_date=end_date,
            window=window,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

"""FX endpoints — USD/KRW 환율 조회 (Silver gen, 마스터플랜 §2.3, §5.3)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.services import fx_service

router = APIRouter(prefix="/v1/fx", tags=["fx"])


class FxRateResponse(BaseModel):
    date: str
    usd_krw_close: float


@router.get("/usd-krw", response_model=list[FxRateResponse])
def get_usd_krw(
    start: date = Query(..., description="시작일 (YYYY-MM-DD)"),
    end: date = Query(..., description="종료일 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
) -> list[FxRateResponse]:
    """USD/KRW 환율 시계열 조회 (calendar-day forward-fill 포함)."""
    if start > end:
        raise HTTPException(status_code=400, detail="start must be <= end")
    rows = fx_service.get_usd_krw(db, start, end)
    return [FxRateResponse(**row) for row in rows]

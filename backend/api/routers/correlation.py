"""Correlation endpoints."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.correlation import (
    CorrelationAnalysisResponse,
    CorrelationResponse,
)
from api.services.analysis.correlation_analysis import (
    find_correlation_groups,
    find_top_pairs,
)
from api.services.correlation_service import compute_correlation

router = APIRouter(prefix="/v1", tags=["correlation"])


def _parse_asset_ids(asset_ids: str | None) -> list[str] | None:
    if not asset_ids:
        return None
    return [aid.strip() for aid in asset_ids.split(",") if aid.strip()]


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
    try:
        return compute_correlation(
            db,
            asset_ids=_parse_asset_ids(asset_ids),
            start_date=start_date,
            end_date=end_date,
            window=window,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/correlation/analysis", response_model=CorrelationAnalysisResponse)
def get_correlation_analysis(
    asset_ids: str | None = Query(default=None, description="콤마 구분 자산 ID"),
    start_date: datetime.date | None = Query(default=None, description="시작일"),
    end_date: datetime.date | None = Query(default=None, description="종료일"),
    window: int = Query(default=60, ge=5, le=500, description="수익률 윈도우 (거래일)"),
    threshold: float = Query(default=0.7, ge=0.0, le=1.0, description="그룹핑 임계값"),
    top_n: int = Query(default=10, ge=1, le=50, description="상위 N 쌍"),
    db: Session = Depends(get_db),
) -> CorrelationAnalysisResponse:
    """Return correlation groups + top pairs analysis."""
    try:
        corr = compute_correlation(
            db,
            asset_ids=_parse_asset_ids(asset_ids),
            start_date=start_date,
            end_date=end_date,
            window=window,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    groups = find_correlation_groups(corr.matrix, corr.asset_ids, threshold)
    top_pairs = find_top_pairs(corr.matrix, corr.asset_ids, top_n)

    return CorrelationAnalysisResponse(
        groups=[
            {"group_id": g.group_id, "asset_ids": g.asset_ids, "avg_correlation": g.avg_correlation}
            for g in groups
        ],
        top_pairs=[
            {"asset_a": p.asset_a, "asset_b": p.asset_b, "correlation": p.correlation}
            for p in top_pairs
        ],
        period=corr.period,
    )

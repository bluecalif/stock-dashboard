"""Analysis endpoints — signal accuracy & indicator comparison."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.analysis import (
    IndicatorComparisonListResponse,
    IndicatorComparisonResponse,
    SignalAccuracyResponse,
)
from api.services.analysis.indicator_comparison import compare_indicator_accuracy
from api.services.analysis.signal_accuracy_service import compute_signal_accuracy

router = APIRouter(prefix="/v1/analysis", tags=["analysis"])


@router.get("/signal-accuracy", response_model=SignalAccuracyResponse)
def get_signal_accuracy(
    asset_id: str = Query(description="자산 ID (예: 005930)"),
    strategy_id: str = Query(description="전략 ID (예: momentum)"),
    forward_days: int = Query(default=5, ge=1, le=60, description="예측 기간 (일)"),
    db: Session = Depends(get_db),
) -> SignalAccuracyResponse:
    """특정 자산+전략의 매수/매도 성공률 조회."""
    result = compute_signal_accuracy(
        db, asset_id, strategy_id, forward_days=forward_days,
    )
    return SignalAccuracyResponse(
        asset_id=result.asset_id,
        strategy_id=result.strategy_id,
        forward_days=result.forward_days,
        total_signals=result.total_signals,
        evaluated_signals=result.evaluated_signals,
        buy_count=result.buy_count,
        buy_success_count=result.buy_success_count,
        buy_success_rate=result.buy_success_rate,
        avg_return_after_buy=result.avg_return_after_buy,
        sell_count=result.sell_count,
        sell_success_count=result.sell_success_count,
        sell_success_rate=result.sell_success_rate,
        avg_return_after_sell=result.avg_return_after_sell,
        insufficient_data=result.insufficient_data,
    )


@router.get(
    "/indicator-comparison",
    response_model=IndicatorComparisonListResponse,
)
def get_indicator_comparison(
    asset_id: str = Query(description="자산 ID (예: 005930)"),
    forward_days: int = Query(default=5, ge=1, le=60, description="예측 기간 (일)"),
    db: Session = Depends(get_db),
) -> IndicatorComparisonListResponse:
    """3개 전략 예측력 비교 — 승률 순위 정렬."""
    rows = compare_indicator_accuracy(
        db, asset_id, forward_days=forward_days,
    )
    return IndicatorComparisonListResponse(
        asset_id=asset_id,
        forward_days=forward_days,
        strategies=[
            IndicatorComparisonResponse(
                strategy_id=r.strategy_id,
                rank=r.rank,
                buy_success_rate=r.buy_success_rate,
                sell_success_rate=r.sell_success_rate,
                avg_return_after_buy=r.avg_return_after_buy,
                avg_return_after_sell=r.avg_return_after_sell,
                evaluated_signals=r.evaluated_signals,
                insufficient_data=r.insufficient_data,
            )
            for r in rows
        ],
        total_strategies=len(rows),
    )

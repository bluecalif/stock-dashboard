"""Analysis endpoints — signal accuracy & indicator comparison."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.analysis import (
    IndicatorComparisonListResponse,
    IndicatorComparisonListResponseV2,
    IndicatorComparisonResponse,
    IndicatorSignalItem,
    IndicatorSignalListResponse,
    SignalAccuracyResponse,
)
from api.services.analysis.indicator_comparison import (
    compare_indicator_accuracy,
    compare_indicators,
)
from api.services.analysis.indicator_signal_service import (
    VALID_INDICATOR_IDS,
    generate_indicator_signals,
)
from api.services.analysis.signal_accuracy_service import (
    compute_indicator_accuracy as compute_indicator_acc,
)
from api.services.analysis.signal_accuracy_service import (
    compute_signal_accuracy,
)

router = APIRouter(prefix="/v1/analysis", tags=["analysis"])


@router.get("/signal-accuracy", response_model=SignalAccuracyResponse)
def get_signal_accuracy(
    asset_id: str = Query(description="자산 ID (예: 005930)"),
    strategy_id: str | None = Query(default=None, description="전략 ID (예: momentum)"),
    indicator_id: str | None = Query(default=None, description="지표 ID (예: rsi_14, macd)"),
    forward_days: int = Query(default=5, ge=1, le=60, description="예측 기간 (일)"),
    include_details: bool = Query(default=False, description="거래 상세 포함 여부"),
    db: Session = Depends(get_db),
) -> SignalAccuracyResponse:
    """매수/매도 성공률 조회 — strategy_id 또는 indicator_id 중 하나 필수."""
    if not strategy_id and not indicator_id:
        raise HTTPException(
            status_code=422,
            detail="strategy_id 또는 indicator_id 중 하나를 지정해야 합니다.",
        )

    if indicator_id:
        if indicator_id not in VALID_INDICATOR_IDS:
            raise HTTPException(
                status_code=422,
                detail=f"지원하지 않는 indicator_id: {indicator_id}. "
                       f"지원: {VALID_INDICATOR_IDS}",
            )
        result = compute_indicator_acc(
            db, asset_id, indicator_id,
            forward_days=forward_days,
            include_details=include_details,
        )
    else:
        result = compute_signal_accuracy(
            db, asset_id, strategy_id,
            forward_days=forward_days,
            include_details=include_details,
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


@router.get("/indicator-signals", response_model=IndicatorSignalListResponse)
def get_indicator_signals(
    asset_id: str = Query(description="자산 ID (예: 005930)"),
    indicator_id: str = Query(description="지표 ID (rsi_14, macd, atr_vol)"),
    start_date: datetime.date | None = Query(default=None, description="시작 날짜"),
    end_date: datetime.date | None = Query(default=None, description="종료 날짜"),
    db: Session = Depends(get_db),
) -> IndicatorSignalListResponse:
    """지표별 on-the-fly 시그널 목록 조회."""
    if indicator_id not in VALID_INDICATOR_IDS:
        raise HTTPException(
            status_code=422,
            detail=f"지원하지 않는 indicator_id: {indicator_id}. "
                   f"지원: {VALID_INDICATOR_IDS}",
        )

    signals = generate_indicator_signals(
        db, asset_id, indicator_id,
        start_date=start_date, end_date=end_date,
    )

    return IndicatorSignalListResponse(
        asset_id=asset_id,
        indicator_id=indicator_id,
        signals=[
            IndicatorSignalItem(
                date=s.date.isoformat(),
                signal=s.signal,
                label=s.label,
                value=round(s.value, 4),
                entry_price=round(s.entry_price, 2),
            )
            for s in signals
        ],
        total_signals=len(signals),
    )


@router.get("/indicator-comparison")
def get_indicator_comparison(
    asset_id: str = Query(description="자산 ID (예: 005930)"),
    forward_days: int = Query(default=5, ge=1, le=60, description="예측 기간 (일)"),
    mode: str = Query(default="indicator", description="비교 모드: indicator 또는 strategy"),
    db: Session = Depends(get_db),
) -> IndicatorComparisonListResponseV2 | IndicatorComparisonListResponse:
    """지표 또는 전략 예측력 비교 — 승률 순위 정렬."""
    if mode == "strategy":
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

    # Default: indicator mode (RSI vs MACD)
    rows = compare_indicators(
        db, asset_id, forward_days=forward_days,
    )
    return IndicatorComparisonListResponseV2(
        asset_id=asset_id,
        forward_days=forward_days,
        indicators=[
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
        total_indicators=len(rows),
    )

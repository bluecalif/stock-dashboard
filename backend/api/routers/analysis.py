"""Analysis endpoints — signal accuracy, indicator comparison, strategy backtest."""

from __future__ import annotations

import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.analysis import (
    AnnualPerformanceItem,
    EquityCurveItem,
    IndicatorComparisonListResponse,
    IndicatorComparisonListResponseV2,
    IndicatorComparisonResponse,
    IndicatorSignalItem,
    IndicatorSignalListResponse,
    MetricsItem,
    SignalAccuracyResponse,
    StrategyBacktestRequest,
    StrategyBacktestResponse,
    TradeItem,
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
    start_date: datetime.date | None = Query(default=None, description="시작 날짜"),
    end_date: datetime.date | None = Query(default=None, description="종료 날짜"),
    min_gap_days: int = Query(default=3, ge=0, description="시그널 최소 간격 (거래일, 0=비활성)"),
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
            start_date=start_date,
            end_date=end_date,
            include_details=include_details,
            min_gap_days=min_gap_days,
        )
    else:
        result = compute_signal_accuracy(
            db, asset_id, strategy_id,
            forward_days=forward_days,
            start_date=start_date,
            end_date=end_date,
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
    min_gap_days: int = Query(default=3, ge=0, description="시그널 최소 간격 (거래일, 0=비활성)"),
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
        min_gap_days=min_gap_days,
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
    start_date: datetime.date | None = Query(default=None, description="시작 날짜"),
    end_date: datetime.date | None = Query(default=None, description="종료 날짜"),
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
        db, asset_id,
        forward_days=forward_days,
        start_date=start_date,
        end_date=end_date,
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


# ---------------------------------------------------------------------------
# E.4: Strategy Backtest
# ---------------------------------------------------------------------------

@router.post("/strategy-backtest", response_model=StrategyBacktestResponse)
def post_strategy_backtest(
    body: StrategyBacktestRequest,
    db: Session = Depends(get_db),
) -> StrategyBacktestResponse:
    """전략 백테스트 실행 — on-the-fly 결과 반환.

    지표 시그널 기반 백테스트를 실행하고 에쿼티 커브, 거래 내역,
    연간 성과, 내러티브를 포함한 결과를 반환합니다.
    """
    from api.services.analysis.annual_performance_service import (
        compute_annual_performance,
    )
    from api.services.analysis.storytelling_service import (
        generate_strategy_summary,
        generate_trade_narratives,
    )
    from api.services.analysis.strategy_backtest_service import (
        STRATEGY_INDICATOR_MAP,
        run_strategy_backtest,
    )
    from research_engine.metrics import metrics_to_dict

    if body.asset_id not in {
        "KS200", "005930", "000660", "SOXL", "BTC", "GC=F", "SI=F",
    }:
        raise HTTPException(
            status_code=422,
            detail=f"지원하지 않는 asset_id: {body.asset_id}",
        )

    if body.strategy_name not in STRATEGY_INDICATOR_MAP:
        raise HTTPException(
            status_code=422,
            detail=f"지원하지 않는 strategy_name: {body.strategy_name}",
        )

    try:
        result = run_strategy_backtest(
            db, body.asset_id, body.strategy_name,
            period=body.period,
            initial_cash=body.initial_cash,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    # 연간 성과
    annual_perf = compute_annual_performance(
        result.backtest_result, initial_cash=body.initial_cash,
    )

    # 내러티브
    trade_narratives = generate_trade_narratives(
        result.backtest_result.trades, body.strategy_name,
        loss_avoided=result.loss_avoided,
    )

    # 전략 요약
    summary = generate_strategy_summary(
        body.strategy_name,
        total_return=result.metrics.total_return,
        num_trades=result.metrics.num_trades,
        win_rate=result.metrics.win_rate,
        annual_performances=annual_perf,
        loss_avoided=result.loss_avoided,
    )

    # 에쿼티 커브 + B&H 에쿼티 병합
    eq = result.backtest_result.equity_curve
    bh = result.backtest_result.buy_hold_equity
    bh_map: dict[str, float] = {}
    if not bh.empty:
        for _, row in bh.iterrows():
            d_key = str(row["date"].date()) if hasattr(row["date"], "date") else str(row["date"])
            bh_map[d_key] = float(row["equity"])

    equity_items: list[EquityCurveItem] = []
    for _, row in eq.iterrows():
        d = str(row["date"].date()) if hasattr(row["date"], "date") else str(row["date"])
        equity_items.append(EquityCurveItem(
            date=d,
            equity=round(float(row["equity"]), 0),
            drawdown=round(float(row["drawdown"]), 6),
            bh_equity=round(bh_map.get(d, 0), 0) if bh_map else None,
        ))

    # 거래 내역 + 내러티브 매핑
    trade_items: list[TradeItem] = []
    for tn in trade_narratives:
        trade_items.append(TradeItem(
            entry_date=str(tn.entry_date),
            exit_date=str(tn.exit_date) if tn.exit_date else None,
            entry_price=tn.entry_price,
            exit_price=tn.exit_price,
            pnl=round(tn.pnl, 0) if tn.pnl is not None else None,
            pnl_pct=tn.pnl_pct,
            holding_days=tn.holding_days,
            narrative=tn.narrative,
            is_best=tn.is_best,
            is_worst=tn.is_worst,
        ))

    # 메트릭스
    m = metrics_to_dict(result.metrics)

    # 연간 성과
    annual_items = [
        AnnualPerformanceItem(
            year=p.year,
            return_pct=p.return_pct,
            pnl_amount=p.pnl_amount,
            mdd=p.mdd,
            num_trades=p.num_trades,
            win_rate=p.win_rate,
            is_favorable=p.is_favorable,
            is_partial_year=p.is_partial_year,
            trading_days=p.trading_days,
        )
        for p in annual_perf
    ]

    return StrategyBacktestResponse(
        asset_id=result.asset_id,
        strategy_name=result.strategy_name,
        strategy_label=result.strategy_label,
        period=result.period,
        initial_cash=result.initial_cash,
        metrics=MetricsItem(**m),
        equity_curve=equity_items,
        trades=trade_items,
        annual_performance=annual_items,
        summary_narrative=summary,
        loss_avoided=result.loss_avoided,
    )

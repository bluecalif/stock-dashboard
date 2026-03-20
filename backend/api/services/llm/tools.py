"""LangChain Tools — DB 조회 도구 (DI 밖이므로 별도 세션 사용)."""

from __future__ import annotations

import json
from datetime import date

from langchain_core.tools import tool

from api.repositories import backtest_repo, factor_repo, price_repo, signal_repo
from api.services.analysis.correlation_analysis import (
    analyze_correlation as _analyze_corr,
)
from api.services.analysis.indicator_analysis import (
    FACTOR_DISPLAY_NAMES,
    interpret_multiple,
)
from api.services.analysis.indicator_comparison import compare_indicator_accuracy
from api.services.analysis.interpretation_rules import (
    interpret_correlation,
    interpret_spread_zscore,
)
from api.services.analysis.signal_accuracy_service import (
    compute_indicator_accuracy,
    compute_signal_accuracy,
)
from api.services.analysis.spread_service import compute_spread
from api.services.correlation_service import compute_correlation
from db.session import SessionLocal


def _get_db():
    """Tool용 DB 세션 컨텍스트."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _serialize_rows(rows: list, fields: list[str]) -> str:
    """ORM 객체 리스트를 JSON 문자열로 변환."""
    data = []
    for r in rows:
        item = {}
        for f in fields:
            val = getattr(r, f, None)
            if isinstance(val, date):
                val = val.isoformat()
            item[f] = val
        data.append(item)
    return json.dumps(data, ensure_ascii=False)


@tool
def get_prices(asset_id: str, days: int = 30) -> str:
    """자산의 최근 N일 OHLCV 조회. asset_id: KS200, 005930, 000660, SOXL, BTC/KRW, GC=F, SI=F"""
    db = next(_get_db())
    try:
        rows = price_repo.get_prices(db, asset_id, limit=days)
        return _serialize_rows(rows, ["date", "open", "high", "low", "close", "volume"])
    finally:
        db.close()


@tool
def get_factors(asset_id: str, factor_name: str | None = None, days: int = 30) -> str:
    """자산의 팩터 데이터 조회. factor_name 예시: return_1d, volatility_20d, rsi_14 등."""
    db = next(_get_db())
    try:
        rows = factor_repo.get_factors(
            db, asset_id=asset_id, factor_name=factor_name, limit=days,
        )
        return _serialize_rows(rows, ["date", "asset_id", "factor_name", "value"])
    finally:
        db.close()


@tool
def get_correlation(asset_ids: list[str] | None = None, days: int = 60) -> str:
    """자산 간 수익률 상관행렬 계산. asset_ids 미지정 시 전체 활성 자산."""
    db = next(_get_db())
    try:
        result = compute_correlation(db, asset_ids=asset_ids, window=days)
        return json.dumps(
            {
                "asset_ids": result.asset_ids,
                "matrix": result.matrix,
                "period": {
                    "start": result.period.start.isoformat(),
                    "end": result.period.end.isoformat(),
                    "window": result.period.window,
                },
            },
            ensure_ascii=False,
        )
    finally:
        db.close()


@tool
def get_signals(asset_id: str, strategy_id: str | None = None, days: int = 30) -> str:
    """자산의 매매 시그널 조회. strategy_id 예시: momentum, trend, mean_reversion."""
    db = next(_get_db())
    try:
        rows = signal_repo.get_signals(
            db, asset_id=asset_id, strategy_id=strategy_id, limit=days,
        )
        return _serialize_rows(
            rows, ["date", "asset_id", "strategy_id", "signal", "score"],
        )
    finally:
        db.close()


@tool
def list_backtests(strategy_id: str | None = None, asset_id: str | None = None) -> str:
    """백테스트 실행 목록 조회."""
    db = next(_get_db())
    try:
        rows = backtest_repo.get_runs(
            db, strategy_id=strategy_id, asset_id=asset_id, limit=20,
        )
        data = []
        for r in rows:
            data.append({
                "run_id": str(r.run_id),
                "strategy_id": r.strategy_id,
                "asset_id": r.asset_id,
                "started_at": r.started_at.isoformat() if r.started_at else None,
                "total_return": r.total_return,
                "sharpe_ratio": r.sharpe_ratio,
                "max_drawdown": r.max_drawdown,
            })
        return json.dumps(data, ensure_ascii=False)
    finally:
        db.close()


@tool
def analyze_correlation_tool(
    asset_ids: list[str] | None = None,
    days: int = 60,
    threshold: float = 0.7,
    target_id: str | None = None,
) -> str:
    """상관도 심층 분석: 자산 그룹핑(Union-Find), 상관도 높은 쌍 TOP-5, 유사자산 추천.
    threshold: 그룹핑 기준 상관계수 (기본 0.7).
    target_id: 유사자산 추천 대상 (예: KS200)."""
    db = next(_get_db())
    try:
        corr = compute_correlation(db, asset_ids=asset_ids, window=days)
        result = _analyze_corr(
            corr.matrix,
            corr.asset_ids,
            threshold=threshold,
            top_n=5,
            target_id=target_id,
            similar_n=3,
        )
        groups = [
            {
                "group_id": g.group_id,
                "asset_ids": g.asset_ids,
                "avg_correlation": g.avg_correlation,
                "interpretation": interpret_correlation(g.avg_correlation).label,
            }
            for g in result.groups
        ]
        top_pairs = [
            {
                "asset_a": p.asset_a,
                "asset_b": p.asset_b,
                "correlation": p.correlation,
                "interpretation": interpret_correlation(p.correlation).label,
            }
            for p in result.top_pairs
        ]
        similar = [
            {
                "asset_id": s.asset_id,
                "correlation": s.correlation,
                "interpretation": interpret_correlation(s.correlation).label,
            }
            for s in result.similar
        ]
        return json.dumps(
            {
                "groups": groups,
                "top_pairs": top_pairs,
                "similar": similar,
                "period": {
                    "start": corr.period.start.isoformat(),
                    "end": corr.period.end.isoformat(),
                    "window": corr.period.window,
                },
            },
            ensure_ascii=False,
        )
    finally:
        db.close()


@tool
def get_spread(asset_a: str, asset_b: str, days: int = 60) -> str:
    """두 자산 간 스프레드 분석: 정규화 가격 비율 + z-score + 수렴/발산 이벤트.
    asset_a, asset_b: 자산 ID (예: KS200, 005930). days: 분석 기간."""
    db = next(_get_db())
    try:
        from datetime import timedelta

        end = date.today()
        start = end - timedelta(days=days)
        result = compute_spread(db, asset_a, asset_b, start_date=start, end_date=end)

        z_interp = interpret_spread_zscore(result.current_z_score)
        events = [
            {
                "date": e.date.isoformat(),
                "z_score": e.z_score,
                "direction": e.direction,
            }
            for e in result.convergence_events
        ]
        return json.dumps(
            {
                "asset_a": result.asset_a,
                "asset_b": result.asset_b,
                "current_z_score": result.current_z_score,
                "z_score_interpretation": z_interp.label,
                "z_score_description": z_interp.description,
                "mean": result.mean,
                "std": result.std,
                "data_points": len(result.dates),
                "convergence_events": events[-10:],  # 최근 10개만
            },
            ensure_ascii=False,
        )
    finally:
        db.close()


@tool
def analyze_indicators(asset_id: str, forward_days: int = 5) -> str:
    """자산의 지표 분석 종합: 현재 상태 해석(RSI/MACD/ATR/vol) + 매수매도 성공률 + 전략 예측력 비교.
    asset_id: KS200, 005930, 000660, SOXL, BTC/KRW, GC=F, SI=F.
    forward_days: 성공률 평가 기간 (기본 5일)."""
    db = next(_get_db())
    try:
        # 1. 현재 지표 상태 해석 — 최신 팩터 값 조회
        factor_names = ["rsi_14", "macd", "macd_signal", "vol_20", "atr_14"]
        latest: dict[str, float] = {}
        for fname in factor_names:
            rows = factor_repo.get_factors(
                db, asset_id=asset_id, factor_name=fname, limit=1,
            )
            if rows:
                latest[fname] = float(rows[0].value)

        # 최신 close 가격 (ATR/Price ratio 계산용)
        price_rows = price_repo.get_prices(db, asset_id, limit=1)
        close = float(price_rows[0].close) if price_rows else None

        # 단일값 해석용 dict
        single_values: dict[str, float] = {}
        if "rsi_14" in latest:
            single_values["rsi_14"] = latest["rsi_14"]
        if "vol_20" in latest:
            single_values["vol_20"] = latest["vol_20"]
        if "atr_14" in latest and close and close > 0:
            single_values["atr_pct"] = latest["atr_14"] / close

        states = interpret_multiple(
            single_values,
            macd=latest.get("macd"),
            macd_signal=latest.get("macd_signal"),
        )

        indicator_states = [
            {
                "factor": FACTOR_DISPLAY_NAMES.get(s.factor_name, s.factor_name),
                "value": round(s.value, 4),
                "label": s.label,
                "signal": s.signal,
                "description": s.description,
            }
            for s in states
        ]

        # 2-A. 지표별 성공률 (RSI, MACD) — 대시보드 그래프와 동일 데이터 소스
        indicator_ids = ["rsi_14", "macd"]
        indicator_accuracy = []
        for iid in indicator_ids:
            r = compute_indicator_accuracy(
                db, asset_id, iid, forward_days=forward_days,
            )
            entry: dict = {
                "indicator_id": iid,
                "buy_success_rate": r.buy_success_rate,
                "sell_success_rate": r.sell_success_rate,
                "avg_return_after_buy": r.avg_return_after_buy,
                "avg_return_after_sell": r.avg_return_after_sell,
                "evaluated_signals": r.evaluated_signals,
                "buy_count": r.buy_count,
                "sell_count": r.sell_count,
                "insufficient_data": r.insufficient_data,
            }
            notes = []
            if r.buy_success_rate is None and r.buy_count > 0:
                notes.append(
                    f"매수 신호 {r.buy_count}건으로 최소 기준(5건) 미달 → 매수 성공률 미산출"
                )
            if r.sell_success_rate is None and r.sell_count > 0:
                notes.append(
                    f"매도 신호 {r.sell_count}건으로 최소 기준(5건) 미달 → 매도 성공률 미산출"
                )
            if notes:
                entry["note"] = "; ".join(notes)
            indicator_accuracy.append(entry)

        # 2-B. 전략별 성공률 (3개 전략, 기존 유지)
        strategy_ids = ["momentum", "trend", "mean_reversion"]
        accuracy_results = []
        for sid in strategy_ids:
            r = compute_signal_accuracy(
                db, asset_id, sid, forward_days=forward_days,
            )
            entry: dict = {
                "strategy_id": sid,
                "buy_success_rate": r.buy_success_rate,
                "sell_success_rate": r.sell_success_rate,
                "avg_return_after_buy": r.avg_return_after_buy,
                "avg_return_after_sell": r.avg_return_after_sell,
                "evaluated_signals": r.evaluated_signals,
                "buy_count": r.buy_count,
                "sell_count": r.sell_count,
                "insufficient_data": r.insufficient_data,
            }
            # null인 항목에 사유 명시 → LLM이 "산출 불가"로 오해하지 않도록
            notes = []
            if r.buy_success_rate is None and r.buy_count > 0:
                notes.append(
                    f"매수 신호 {r.buy_count}건으로 최소 기준(5건) 미달 → 매수 성공률 미산출"
                )
            if r.sell_success_rate is None and r.sell_count > 0:
                notes.append(
                    f"매도 신호 {r.sell_count}건으로 최소 기준(5건) 미달 → 매도 성공률 미산출"
                )
            if notes:
                entry["note"] = "; ".join(notes)
            accuracy_results.append(entry)

        # 3. 전략 예측력 비교 (순위)
        comparison = compare_indicator_accuracy(
            db, asset_id, strategy_ids, forward_days=forward_days,
        )
        ranking = [
            {
                "rank": c.rank,
                "strategy_id": c.strategy_id,
                "buy_success_rate": c.buy_success_rate,
                "sell_success_rate": c.sell_success_rate,
                "insufficient_data": c.insufficient_data,
            }
            for c in comparison
        ]

        return json.dumps(
            {
                "asset_id": asset_id,
                "forward_days": forward_days,
                "indicator_states": indicator_states,
                "indicator_accuracy": indicator_accuracy,
                "signal_accuracy": accuracy_results,
                "strategy_ranking": ranking,
            },
            ensure_ascii=False,
        )
    finally:
        db.close()


@tool
def backtest_strategy(
    asset_id: str,
    strategy_name: str = "momentum",
    period: str = "2Y",
) -> str:
    """전략 백테스트 실행: 모멘텀(MACD), 역발상(RSI), 위험회피(ATR+vol).
    asset_id: KS200, 005930, 000660, SOXL, BTC, GC=F, SI=F.
    strategy_name: momentum, contrarian, risk_aversion.
    period: 6M, 1Y, 2Y, 3Y."""
    from api.services.analysis.annual_performance_service import (
        annual_performance_to_dicts,
        compute_annual_performance,
    )
    from api.services.analysis.storytelling_service import generate_strategy_summary
    from api.services.analysis.strategy_backtest_service import run_strategy_backtest
    from research_engine.metrics import metrics_to_dict

    db = next(_get_db())
    try:
        result = run_strategy_backtest(
            db, asset_id, strategy_name, period=period,
        )
        metrics = metrics_to_dict(result.metrics)
        annual = annual_performance_to_dicts(
            compute_annual_performance(result.backtest_result),
        )
        summary = generate_strategy_summary(
            strategy_name,
            total_return=result.metrics.total_return,
            num_trades=result.metrics.num_trades,
            win_rate=result.metrics.win_rate,
            annual_performances=compute_annual_performance(result.backtest_result),
            loss_avoided=result.loss_avoided,
        )
        return json.dumps(
            {
                "asset_id": result.asset_id,
                "strategy_name": result.strategy_name,
                "strategy_label": result.strategy_label,
                "period": result.period,
                "initial_cash": result.initial_cash,
                "metrics": metrics,
                "annual_performance": annual,
                "summary": summary,
                "num_trades": result.metrics.num_trades,
                "loss_avoided": result.loss_avoided,
            },
            ensure_ascii=False,
        )
    except ValueError as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        db.close()


all_tools = [
    get_prices,
    get_factors,
    get_correlation,
    get_signals,
    list_backtests,
    analyze_correlation_tool,
    get_spread,
    analyze_indicators,
    backtest_strategy,
]

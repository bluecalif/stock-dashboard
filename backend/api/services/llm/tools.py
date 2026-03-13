"""LangChain Tools — DB 조회 도구 (DI 밖이므로 별도 세션 사용)."""

from __future__ import annotations

import json
from datetime import date

from langchain_core.tools import tool

from api.repositories import backtest_repo, factor_repo, price_repo, signal_repo
from api.services.analysis.correlation_analysis import (
    analyze_correlation as _analyze_corr,
)
from api.services.analysis.interpretation_rules import (
    interpret_correlation,
    interpret_spread_zscore,
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


all_tools = [
    get_prices,
    get_factors,
    get_correlation,
    get_signals,
    list_backtests,
    analyze_correlation_tool,
    get_spread,
]

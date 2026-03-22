"""Tool Result Compressor — LLM 입력 토큰 최적화.

get_prices, get_factors, get_signals의 raw 365일 데이터를
통계 요약으로 압축하여 Reporter LLM 입력 토큰을 80%+ 감소.
이미 요약된 tool (analyze_indicators, analyze_correlation_tool,
get_spread, backtest_strategy)은 그대로 통과.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def compress_tool_results(tool_results: dict[str, Any]) -> dict[str, Any]:
    """각 tool 결과를 LLM에 필요한 최소 정보로 압축."""
    compressed: dict[str, Any] = {}
    for key, data in tool_results.items():
        fn = _COMPRESSORS.get(key)
        if fn is None:
            compressed[key] = data
            continue
        try:
            compressed[key] = fn(data)
        except Exception:
            logger.warning("Compressor failed for %s — passing raw", key, exc_info=True)
            compressed[key] = data
    return compressed


# ---------------------------------------------------------------------------
# Per-tool compressors
# ---------------------------------------------------------------------------

def _compress_prices(rows: list[dict]) -> dict:
    """365일 OHLCV → 최근 5일 상세 + 구간 통계."""
    if not rows:
        return {"error": "no data"}

    sorted_rows = sorted(rows, key=lambda x: str(x.get("date", "")), reverse=True)
    recent = sorted_rows[:5]

    closes = [float(r["close"]) for r in sorted_rows if r.get("close") is not None]
    volumes = [float(r["volume"]) for r in sorted_rows if r.get("volume") is not None]
    highs = [float(r["high"]) for r in sorted_rows if r.get("high") is not None]
    lows = [float(r["low"]) for r in sorted_rows if r.get("low") is not None]

    if not closes:
        return {"recent_5_days": recent, "total_days": len(rows)}

    result: dict[str, Any] = {
        "total_days": len(rows),
        "period": {
            "start": sorted_rows[-1].get("date"),
            "end": sorted_rows[0].get("date"),
        },
        "recent_5_days": recent,
        "close_stats": {
            "latest": closes[0],
            "min": min(closes),
            "max": max(closes),
            "avg_30d": _avg(closes[:30]),
            "avg_90d": _avg(closes[:90]),
        },
        "returns": {
            "5d": _pct_change(closes, 5),
            "20d": _pct_change(closes, 20),
            "60d": _pct_change(closes, 60),
            "250d": _pct_change(closes, 250),
        },
    }

    if highs:
        min_30d_high = min(highs[:30]) if len(highs) >= 30 else min(highs)
        result["high_stats"] = {"max": max(highs), "min_30d": min_30d_high}
    if lows:
        max_30d_low = max(lows[:30]) if len(lows) >= 30 else max(lows)
        result["low_stats"] = {"min": min(lows), "max_30d": max_30d_low}
    if volumes:
        result["volume_stats"] = {
            "avg_20d": _avg(volumes[:20]),
            "avg_60d": _avg(volumes[:60]),
            "latest": volumes[0],
        }

    return result


def _compress_factors(rows: list[dict]) -> dict:
    """365일 팩터 데이터 → 팩터별 최신값 + 30일 추세."""
    if not rows:
        return {"error": "no data"}

    # 팩터별로 그룹핑
    by_factor: dict[str, list[dict]] = {}
    for r in rows:
        fname = r.get("factor_name", "unknown")
        by_factor.setdefault(fname, []).append(r)

    summaries: dict[str, Any] = {}
    for fname, frows in by_factor.items():
        sorted_f = sorted(frows, key=lambda x: str(x.get("date", "")), reverse=True)
        values = [float(r["value"]) for r in sorted_f if r.get("value") is not None]
        if not values:
            continue

        summary: dict[str, Any] = {
            "latest_value": values[0],
            "latest_date": sorted_f[0].get("date"),
            "total_days": len(values),
        }

        if len(values) >= 5:
            summary["avg_5d"] = _avg(values[:5])
        if len(values) >= 30:
            summary["avg_30d"] = _avg(values[:30])
            summary["min_30d"] = min(values[:30])
            summary["max_30d"] = max(values[:30])
            # 추세: 최근 5일 평균 vs 30일 평균
            recent_avg = _avg(values[:5])
            month_avg = _avg(values[:30])
            if month_avg and month_avg != 0:
                trend_pct = (recent_avg - month_avg) / abs(month_avg) * 100
                summary["trend_vs_30d"] = round(trend_pct, 2)

        summaries[fname] = summary

    return {
        "asset_id": rows[0].get("asset_id"),
        "factor_count": len(summaries),
        "factors": summaries,
    }


def _compress_signals(rows: list[dict]) -> dict:
    """365일 시그널 → 최근 10개 + 매수/매도 통계."""
    if not rows:
        return {"error": "no data"}

    sorted_rows = sorted(rows, key=lambda x: str(x.get("date", "")), reverse=True)
    recent = sorted_rows[:10]

    # 매수/매도 통계
    buy_count = sum(1 for r in rows if r.get("signal") == "buy")
    sell_count = sum(1 for r in rows if r.get("signal") == "sell")
    hold_count = sum(1 for r in rows if r.get("signal") == "hold")

    # 전략별 그룹핑
    by_strategy: dict[str, dict] = {}
    for r in rows:
        sid = r.get("strategy_id", "unknown")
        if sid not in by_strategy:
            by_strategy[sid] = {"buy": 0, "sell": 0, "hold": 0, "latest_signal": None}
        sig = r.get("signal", "hold")
        by_strategy[sid][sig] = by_strategy[sid].get(sig, 0) + 1

    # 전략별 최신 시그널
    for r in sorted_rows:
        sid = r.get("strategy_id", "unknown")
        if sid in by_strategy and by_strategy[sid]["latest_signal"] is None:
            by_strategy[sid]["latest_signal"] = {
                "date": r.get("date"),
                "signal": r.get("signal"),
                "score": r.get("score"),
            }

    return {
        "total_signals": len(rows),
        "period": {
            "start": sorted_rows[-1].get("date") if sorted_rows else None,
            "end": sorted_rows[0].get("date") if sorted_rows else None,
        },
        "summary": {
            "buy_count": buy_count,
            "sell_count": sell_count,
            "hold_count": hold_count,
        },
        "by_strategy": by_strategy,
        "recent_10": recent,
    }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _avg(values: list[float]) -> float | None:
    """안전한 평균 계산."""
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _pct_change(values: list[float], n: int) -> float | None:
    """최신 대비 n일 전 수익률 (%)."""
    if len(values) <= n or values[n] == 0:
        return None
    return round((values[0] - values[n]) / values[n] * 100, 2)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

_COMPRESSORS: dict[str, Any] = {
    "get_prices": _compress_prices,
    "get_factors": _compress_factors,
    "get_signals": _compress_signals,
}

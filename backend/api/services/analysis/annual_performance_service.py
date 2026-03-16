"""Annual performance analysis — slice equity curve by year and compute per-year metrics.

Provides yearly breakdown of strategy performance including return, PnL,
MDD, trade count, win rate, and favorable/unfavorable classification.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from research_engine.backtest import BacktestResult, TradeRecord

logger = logging.getLogger(__name__)

# 연도별 분석에 필요한 최소 거래일 수 (6개월 ≈ 126일)
MIN_TRADING_DAYS_PER_YEAR = 60


@dataclass
class AnnualPerformance:
    """1년 단위 성과 분석 결과."""

    year: int
    return_pct: float  # 연간 수익률 (소수, e.g. 0.12 = 12%)
    pnl_amount: float  # 연간 손익 금액 (원)
    mdd: float  # 연간 최대 낙폭 (음수)
    num_trades: int  # 연간 거래 횟수 (청산 기준)
    win_rate: float  # 연간 승률 (0~1)
    is_favorable: bool  # 전략 적합 구간 여부
    is_partial_year: bool  # 부분 연도 (6개월 미만 데이터)
    trading_days: int  # 해당 연도 거래일 수


def compute_annual_performance(
    bt_result: BacktestResult,
    initial_cash: float = 100_000_000,
) -> list[AnnualPerformance]:
    """에쿼티 커브를 1년 단위로 슬라이싱하여 연도별 성과 분석.

    Args:
        bt_result: BacktestResult (equity_curve, trades 포함).
        initial_cash: 초기 투자금 (기본 1억원).

    Returns:
        연도별 AnnualPerformance 리스트 (오름차순).
    """
    eq = bt_result.equity_curve
    if eq.empty or len(eq) < 2:
        return []

    # 날짜 → datetime 변환
    eq_copy = eq.copy()
    eq_copy["date"] = pd.to_datetime(eq_copy["date"])
    eq_copy = eq_copy.sort_values("date")
    eq_copy["year"] = eq_copy["date"].dt.year

    years = sorted(eq_copy["year"].unique())
    results: list[AnnualPerformance] = []

    for year in years:
        year_data = eq_copy[eq_copy["year"] == year]
        trading_days = len(year_data)

        if trading_days < 2:
            continue

        # 연간 수익률: 연도 시작 에쿼티 → 연도 끝 에쿼티
        start_equity = year_data["equity"].iloc[0]
        end_equity = year_data["equity"].iloc[-1]

        if start_equity <= 0:
            continue

        return_pct = (end_equity / start_equity) - 1.0
        pnl_amount = end_equity - start_equity

        # 연간 MDD
        equities = year_data["equity"].values
        running_max = np.maximum.accumulate(equities)
        drawdowns = equities / running_max - 1.0
        mdd = float(drawdowns.min())

        # 연간 거래 통계
        year_trades = _get_year_trades(bt_result.trades, year)
        closed_trades = [t for t in year_trades if t.exit_date is not None]
        num_trades = len(closed_trades)
        wins = sum(1 for t in closed_trades if t.pnl is not None and t.pnl > 0)
        win_rate = wins / num_trades if num_trades > 0 else 0.0

        # 적합 구간 판별: 수익률 > 0 AND (거래 없거나 win_rate > 50%)
        is_favorable = bool(return_pct > 0 and (num_trades == 0 or win_rate > 0.5))

        is_partial = trading_days < MIN_TRADING_DAYS_PER_YEAR

        results.append(AnnualPerformance(
            year=year,
            return_pct=round(return_pct, 6),
            pnl_amount=round(pnl_amount, 0),
            mdd=round(mdd, 6),
            num_trades=num_trades,
            win_rate=round(win_rate, 4),
            is_favorable=is_favorable,
            is_partial_year=is_partial,
            trading_days=trading_days,
        ))

    return results


def _get_year_trades(trades: list[TradeRecord], year: int) -> list[TradeRecord]:
    """특정 연도에 청산된 거래 필터링."""
    return [
        t for t in trades
        if t.exit_date is not None and t.exit_date.year == year
    ]


def annual_performance_to_dicts(
    performances: list[AnnualPerformance],
) -> list[dict]:
    """AnnualPerformance 리스트 → JSON-friendly dict 리스트."""
    return [
        {
            "year": p.year,
            "return_pct": p.return_pct,
            "pnl_amount": p.pnl_amount,
            "mdd": p.mdd,
            "num_trades": p.num_trades,
            "win_rate": p.win_rate,
            "is_favorable": p.is_favorable,
            "is_partial_year": p.is_partial_year,
            "trading_days": p.trading_days,
        }
        for p in performances
    ]

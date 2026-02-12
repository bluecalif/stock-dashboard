"""Performance metrics for backtest results."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from research_engine.backtest import BacktestResult


@dataclass
class PerformanceMetrics:
    total_return: float  # 누적수익률 (소수)
    cagr: float  # 연환산 복리수익률
    mdd: float  # 최대 낙폭 (음수)
    volatility: float  # 연환산 변동성
    sharpe: float  # Sharpe ratio (무위험 수익률 0 가정)
    sortino: float  # Sortino ratio
    calmar: float  # Calmar ratio (CAGR / |MDD|)
    win_rate: float  # 승률 (0~1)
    num_trades: int  # 총 거래 횟수
    avg_trade_pnl: float  # 평균 거래 손익
    turnover: float  # 연환산 턴오버 (거래 횟수 / 연수)
    # Buy & Hold 비교
    bh_total_return: float | None
    bh_cagr: float | None
    excess_return: float | None  # CAGR - BH CAGR


TRADING_DAYS_PER_YEAR = 252


def compute_metrics(
    result: BacktestResult,
    risk_free_rate: float = 0.0,
) -> PerformanceMetrics:
    """Compute performance metrics from a BacktestResult.

    Args:
        result: BacktestResult from run_backtest or run_backtest_multi.
        risk_free_rate: Annualized risk-free rate (default 0).

    Returns:
        PerformanceMetrics dataclass.
    """
    eq = result.equity_curve
    if eq.empty or len(eq) < 2:
        return _empty_metrics()

    equities = eq["equity"].values
    n_days = len(equities)
    years = n_days / TRADING_DAYS_PER_YEAR

    # --- 누적수익률, CAGR ---
    total_return = equities[-1] / equities[0] - 1.0
    cagr = _cagr(equities[0], equities[-1], years)

    # --- MDD ---
    mdd = eq["drawdown"].min()

    # --- 일별 수익률 기반 지표 ---
    daily_returns = np.diff(equities) / equities[:-1]
    volatility = float(np.std(daily_returns, ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))

    # Sharpe
    daily_rf = risk_free_rate / TRADING_DAYS_PER_YEAR
    excess_daily = daily_returns - daily_rf
    sharpe = _safe_divide(
        float(np.mean(excess_daily)) * np.sqrt(TRADING_DAYS_PER_YEAR),
        float(np.std(excess_daily, ddof=1)),
    )

    # Sortino (하방 변동성만 사용)
    downside = excess_daily[excess_daily < 0]
    downside_std = float(np.std(downside, ddof=1)) if len(downside) > 1 else 0.0
    sortino = _safe_divide(
        float(np.mean(excess_daily)) * np.sqrt(TRADING_DAYS_PER_YEAR),
        downside_std,
    )

    # Calmar
    calmar = _safe_divide(cagr, abs(mdd))

    # --- 거래 통계 ---
    closed_trades = [t for t in result.trades if t.exit_date is not None]
    num_trades = len(closed_trades)
    wins = sum(1 for t in closed_trades if t.pnl is not None and t.pnl > 0)
    win_rate = wins / num_trades if num_trades > 0 else 0.0
    avg_pnl = (
        float(np.mean([t.pnl for t in closed_trades if t.pnl is not None]))
        if num_trades > 0
        else 0.0
    )
    turnover = num_trades / years if years > 0 else 0.0

    # --- Buy & Hold ---
    bh = result.buy_hold_equity
    bh_total_return = None
    bh_cagr_val = None
    excess_ret = None
    if not bh.empty and len(bh) >= 2:
        bh_eq = bh["equity"].values
        bh_total_return = bh_eq[-1] / bh_eq[0] - 1.0
        bh_cagr_val = _cagr(bh_eq[0], bh_eq[-1], years)
        excess_ret = cagr - bh_cagr_val

    return PerformanceMetrics(
        total_return=total_return,
        cagr=cagr,
        mdd=mdd,
        volatility=volatility,
        sharpe=sharpe,
        sortino=sortino,
        calmar=calmar,
        win_rate=win_rate,
        num_trades=num_trades,
        avg_trade_pnl=avg_pnl,
        turnover=turnover,
        bh_total_return=bh_total_return,
        bh_cagr=bh_cagr_val,
        excess_return=excess_ret,
    )


def metrics_to_dict(m: PerformanceMetrics) -> dict:
    """Convert PerformanceMetrics to a plain dict (JSON-friendly)."""
    return {
        "total_return": round(m.total_return, 6),
        "cagr": round(m.cagr, 6),
        "mdd": round(m.mdd, 6),
        "volatility": round(m.volatility, 6),
        "sharpe": round(m.sharpe, 4),
        "sortino": round(m.sortino, 4),
        "calmar": round(m.calmar, 4),
        "win_rate": round(m.win_rate, 4),
        "num_trades": m.num_trades,
        "avg_trade_pnl": round(m.avg_trade_pnl, 2),
        "turnover": round(m.turnover, 2),
        "bh_total_return": round(m.bh_total_return, 6) if m.bh_total_return is not None else None,
        "bh_cagr": round(m.bh_cagr, 6) if m.bh_cagr is not None else None,
        "excess_return": round(m.excess_return, 6) if m.excess_return is not None else None,
    }


# --- Helpers ---


def _cagr(start_val: float, end_val: float, years: float) -> float:
    if start_val <= 0 or years <= 0:
        return 0.0
    return (end_val / start_val) ** (1.0 / years) - 1.0


def _safe_divide(numerator: float, denominator: float) -> float:
    if denominator == 0.0 or np.isnan(denominator):
        return 0.0
    return numerator / denominator


def _empty_metrics() -> PerformanceMetrics:
    return PerformanceMetrics(
        total_return=0.0,
        cagr=0.0,
        mdd=0.0,
        volatility=0.0,
        sharpe=0.0,
        sortino=0.0,
        calmar=0.0,
        win_rate=0.0,
        num_trades=0,
        avg_trade_pnl=0.0,
        turnover=0.0,
        bh_total_return=None,
        bh_cagr=None,
        excess_return=None,
    )

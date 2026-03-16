"""Tests for annual_performance_service — yearly performance slicing."""

from datetime import date

import numpy as np
import pandas as pd

from api.services.analysis.annual_performance_service import (
    AnnualPerformance,
    _get_year_trades,
    annual_performance_to_dicts,
    compute_annual_performance,
)
from research_engine.backtest import BacktestConfig, BacktestResult, TradeRecord

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_equity_curve(
    start_date: date,
    n_days: int,
    start_equity: float = 100_000_000,
    daily_return: float = 0.001,
) -> pd.DataFrame:
    """Generate equity curve with constant daily return."""
    dates = pd.bdate_range(start=start_date, periods=n_days)
    equities = [start_equity]
    for _ in range(n_days - 1):
        equities.append(equities[-1] * (1 + daily_return))
    equities = np.array(equities[:n_days])
    running_max = np.maximum.accumulate(equities)
    drawdowns = equities / running_max - 1.0
    return pd.DataFrame({
        "date": dates[:n_days],
        "equity": equities,
        "drawdown": drawdowns,
    })


def _make_bt_result(
    equity_df: pd.DataFrame,
    trades: list[TradeRecord] | None = None,
) -> BacktestResult:
    return BacktestResult(
        strategy_id="test",
        asset_id="005930",
        config=BacktestConfig(initial_cash=100_000_000),
        equity_curve=equity_df,
        trades=trades or [],
        buy_hold_equity=pd.DataFrame(columns=["date", "equity"]),
    )


# ---------------------------------------------------------------------------
# compute_annual_performance
# ---------------------------------------------------------------------------

class TestComputeAnnualPerformance:
    def test_empty_equity_curve(self):
        bt = _make_bt_result(pd.DataFrame(columns=["date", "equity", "drawdown"]))
        assert compute_annual_performance(bt) == []

    def test_single_year(self):
        """1년 데이터 → 1개 AnnualPerformance."""
        eq = _make_equity_curve(date(2025, 1, 2), 250, daily_return=0.0005)
        bt = _make_bt_result(eq)
        result = compute_annual_performance(bt)

        assert len(result) == 1
        assert result[0].year == 2025
        assert result[0].return_pct > 0
        assert result[0].pnl_amount > 0
        assert result[0].mdd <= 0  # 상승만이면 0
        assert result[0].is_favorable is True  # 수익 > 0, 거래 0건
        assert result[0].is_partial_year is False
        assert result[0].trading_days == 250

    def test_two_years(self):
        """2년 걸친 데이터 → 2개 AnnualPerformance."""
        eq = _make_equity_curve(date(2024, 7, 1), 260, daily_return=0.0003)
        bt = _make_bt_result(eq)
        result = compute_annual_performance(bt)

        assert len(result) == 2
        years = [r.year for r in result]
        assert 2024 in years
        assert 2025 in years

    def test_negative_return_not_favorable(self):
        """손실 연도는 is_favorable=False."""
        eq = _make_equity_curve(date(2025, 1, 2), 250, daily_return=-0.001)
        bt = _make_bt_result(eq)
        result = compute_annual_performance(bt)

        assert len(result) == 1
        assert result[0].return_pct < 0
        assert result[0].is_favorable is False

    def test_partial_year_flagged(self):
        """60일 미만 데이터 → is_partial_year=True."""
        eq = _make_equity_curve(date(2025, 11, 1), 40, daily_return=0.001)
        bt = _make_bt_result(eq)
        result = compute_annual_performance(bt)

        assert len(result) == 1
        assert result[0].is_partial_year is True
        assert result[0].trading_days < 60

    def test_mdd_calculated(self):
        """하락 구간 있는 에쿼티 → MDD < 0."""
        dates = pd.bdate_range(start=date(2025, 1, 2), periods=20)
        # 상승 후 하락 패턴
        equities = list(range(100, 110)) + list(range(110, 100, -1))
        equities = [float(e) * 1_000_000 for e in equities]
        running_max = np.maximum.accumulate(equities)
        drawdowns = np.array(equities) / running_max - 1.0
        eq = pd.DataFrame({
            "date": dates,
            "equity": equities,
            "drawdown": drawdowns,
        })
        bt = _make_bt_result(eq)
        result = compute_annual_performance(bt)

        assert len(result) == 1
        assert result[0].mdd < 0

    def test_trades_counted_by_exit_year(self):
        """거래는 청산 연도 기준으로 집계."""
        eq = _make_equity_curve(date(2024, 7, 1), 400, daily_return=0.0005)
        trades = [
            TradeRecord(
                asset_id="005930",
                entry_date=date(2024, 10, 1),
                entry_price=50000,
                exit_date=date(2024, 12, 1),
                exit_price=55000,
                side="long", shares=100, pnl=500_000, cost=1000,
            ),
            TradeRecord(
                asset_id="005930",
                entry_date=date(2024, 12, 15),
                entry_price=54000,
                exit_date=date(2025, 2, 1),
                exit_price=52000,
                side="long", shares=100, pnl=-200_000, cost=1000,
            ),
            TradeRecord(
                asset_id="005930",
                entry_date=date(2025, 3, 1),
                entry_price=52000,
                exit_date=date(2025, 5, 1),
                exit_price=58000,
                side="long", shares=100, pnl=600_000, cost=1000,
            ),
        ]
        bt = _make_bt_result(eq, trades)
        result = compute_annual_performance(bt)

        y2024 = next(r for r in result if r.year == 2024)
        y2025 = next(r for r in result if r.year == 2025)

        assert y2024.num_trades == 1  # 2024 청산 1건
        assert y2024.win_rate == 1.0  # 1승 0패
        assert y2025.num_trades == 2  # 2025 청산 2건
        assert y2025.win_rate == 0.5  # 1승 1패

    def test_win_rate_affects_favorable(self):
        """승률 50% 이하 + 수익 → is_favorable=False."""
        eq = _make_equity_curve(date(2025, 1, 2), 250, daily_return=0.0001)
        trades = [
            TradeRecord(
                asset_id="005930", entry_date=date(2025, 2, 1),
                entry_price=50000, exit_date=date(2025, 3, 1),
                exit_price=48000, side="long", shares=100,
                pnl=-200_000, cost=1000,
            ),
            TradeRecord(
                asset_id="005930", entry_date=date(2025, 4, 1),
                entry_price=48000, exit_date=date(2025, 5, 1),
                exit_price=47000, side="long", shares=100,
                pnl=-100_000, cost=1000,
            ),
            TradeRecord(
                asset_id="005930", entry_date=date(2025, 6, 1),
                entry_price=47000, exit_date=date(2025, 7, 1),
                exit_price=55000, side="long", shares=100,
                pnl=800_000, cost=1000,
            ),
        ]
        bt = _make_bt_result(eq, trades)
        result = compute_annual_performance(bt)

        assert len(result) == 1
        # 수익률 > 0 이지만 승률 33% → not favorable
        assert result[0].win_rate < 0.5
        assert result[0].is_favorable is False


# ---------------------------------------------------------------------------
# _get_year_trades
# ---------------------------------------------------------------------------

class TestGetYearTrades:
    def test_filters_by_exit_year(self):
        trades = [
            TradeRecord("A", date(2024, 12, 1), 100, date(2025, 1, 15), 110,
                        "long", 10, 100, 1),
            TradeRecord("A", date(2025, 3, 1), 100, date(2025, 5, 1), 120,
                        "long", 10, 200, 1),
            TradeRecord("A", date(2025, 11, 1), 100, None, None,
                        "long", 10, None, 0),  # 미청산
        ]
        result = _get_year_trades(trades, 2025)
        assert len(result) == 2

    def test_empty_trades(self):
        assert _get_year_trades([], 2025) == []


# ---------------------------------------------------------------------------
# annual_performance_to_dicts
# ---------------------------------------------------------------------------

class TestAnnualPerformanceToDicts:
    def test_serialization(self):
        perf = AnnualPerformance(
            year=2025, return_pct=0.12, pnl_amount=12_000_000,
            mdd=-0.05, num_trades=5, win_rate=0.6,
            is_favorable=True, is_partial_year=False, trading_days=250,
        )
        result = annual_performance_to_dicts([perf])
        assert len(result) == 1
        d = result[0]
        assert d["year"] == 2025
        assert d["return_pct"] == 0.12
        assert d["pnl_amount"] == 12_000_000
        assert d["is_favorable"] is True
        assert d["is_partial_year"] is False

    def test_empty_list(self):
        assert annual_performance_to_dicts([]) == []

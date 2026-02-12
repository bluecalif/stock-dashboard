"""Tests for research_engine.metrics — performance metrics computation."""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from research_engine.backtest import BacktestConfig, BacktestResult, TradeRecord
from research_engine.metrics import _cagr, _safe_divide, compute_metrics, metrics_to_dict

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_equity_curve(equities: list[float], start_date: str = "2024-01-02") -> pd.DataFrame:
    """Create an equity curve DataFrame from a list of equity values."""
    dates = pd.bdate_range(start=start_date, periods=len(equities))
    running_max = np.maximum.accumulate(equities)
    drawdown = np.array(equities) / running_max - 1.0
    return pd.DataFrame({
        "date": dates.tolist(),
        "equity": equities,
        "drawdown": drawdown,
    })


def _make_buy_hold(equities: list[float], start_date: str = "2024-01-02") -> pd.DataFrame:
    dates = pd.bdate_range(start=start_date, periods=len(equities))
    return pd.DataFrame({"date": dates.tolist(), "equity": equities})


def _make_result(
    equities: list[float],
    trades: list[TradeRecord] | None = None,
    bh_equities: list[float] | None = None,
) -> BacktestResult:
    eq = _make_equity_curve(equities)
    bh = _make_buy_hold(bh_equities) if bh_equities else pd.DataFrame(columns=["date", "equity"])
    return BacktestResult(
        strategy_id="test_strat",
        asset_id="TEST",
        config=BacktestConfig(),
        equity_curve=eq,
        trades=trades or [],
        buy_hold_equity=bh,
    )


# ---------------------------------------------------------------------------
# Test: CAGR helper
# ---------------------------------------------------------------------------

class TestCAGR:
    def test_1year_10pct(self):
        """10M → 11M in 1 year → CAGR = 10%."""
        assert _cagr(10_000_000, 11_000_000, 1.0) == pytest.approx(0.1, rel=1e-6)

    def test_2years_21pct(self):
        """10M → 12.1M in 2 years → CAGR = 10%."""
        assert _cagr(10_000_000, 12_100_000, 2.0) == pytest.approx(0.1, rel=1e-4)

    def test_zero_years(self):
        assert _cagr(10_000_000, 11_000_000, 0.0) == 0.0

    def test_zero_start(self):
        assert _cagr(0, 11_000_000, 1.0) == 0.0


# ---------------------------------------------------------------------------
# Test: safe_divide helper
# ---------------------------------------------------------------------------

class TestSafeDivide:
    def test_normal(self):
        assert _safe_divide(10.0, 2.0) == 5.0

    def test_zero_denominator(self):
        assert _safe_divide(10.0, 0.0) == 0.0

    def test_nan_denominator(self):
        assert _safe_divide(10.0, float("nan")) == 0.0


# ---------------------------------------------------------------------------
# Test: compute_metrics with known values
# ---------------------------------------------------------------------------

class TestComputeMetrics:
    def test_flat_equity(self):
        """Flat equity → all returns/ratios zero."""
        equities = [10_000_000.0] * 252
        m = compute_metrics(_make_result(equities))
        assert m.total_return == pytest.approx(0.0)
        assert m.cagr == pytest.approx(0.0)
        assert m.mdd == pytest.approx(0.0)
        assert m.volatility == pytest.approx(0.0)
        assert m.sharpe == pytest.approx(0.0)

    def test_steady_growth_total_return(self):
        """Steady 0.1% daily growth over 252 days."""
        eq = [10_000_000.0]
        for _ in range(251):
            eq.append(eq[-1] * 1.001)
        m = compute_metrics(_make_result(eq))
        expected_total = eq[-1] / eq[0] - 1.0
        assert m.total_return == pytest.approx(expected_total, rel=1e-6)
        assert m.cagr > 0
        assert m.mdd == pytest.approx(0.0)  # no drawdown in steady growth
        assert m.volatility > 0
        assert m.sharpe > 0

    def test_drawdown_calculation(self):
        """Equity goes up then down → MDD captured."""
        equities = [100, 110, 120, 100, 90, 95]
        m = compute_metrics(_make_result(equities))
        # MDD = 90/120 - 1 = -0.25
        assert m.mdd == pytest.approx(-0.25, rel=1e-6)

    def test_cagr_one_year(self):
        """252 trading days = 1 year, 10M → 11M."""
        eq = np.linspace(10_000_000, 11_000_000, 252).tolist()
        m = compute_metrics(_make_result(eq))
        assert m.cagr == pytest.approx(0.1, rel=0.01)

    def test_trade_stats(self):
        """Win rate and avg PnL from trades."""
        trades = [
            TradeRecord(
                "A", date(2024, 1, 2), 100, date(2024, 1, 10), 110, "long", 10, 100.0, 2.0,
            ),
            TradeRecord(
                "A", date(2024, 1, 11), 110, date(2024, 1, 20), 105, "long", 10, -50.0, 2.0,
            ),
            TradeRecord(
                "A", date(2024, 1, 21), 105, date(2024, 1, 30), 115, "long", 10, 100.0, 2.0,
            ),
        ]
        eq = [10_000_000.0] * 252  # flat (trade stats independent of equity)
        m = compute_metrics(_make_result(eq, trades=trades))
        assert m.num_trades == 3
        assert m.win_rate == pytest.approx(2.0 / 3.0, rel=1e-6)
        assert m.avg_trade_pnl == pytest.approx(50.0, rel=1e-6)

    def test_open_trade_excluded_from_stats(self):
        """Open trade (exit_date=None) should not count in win_rate."""
        trades = [
            TradeRecord("A", date(2024, 1, 2), 100, date(2024, 1, 10), 110, "long", 10, 100.0, 2.0),
            TradeRecord("A", date(2024, 1, 11), 110, None, None, "long", 10, 50.0, 1.0),
        ]
        eq = [10_000_000.0] * 252
        m = compute_metrics(_make_result(eq, trades=trades))
        assert m.num_trades == 1  # only closed
        assert m.win_rate == pytest.approx(1.0)

    def test_buy_hold_comparison(self):
        """Excess return = strategy CAGR - BH CAGR."""
        eq_strat = np.linspace(10_000_000, 12_000_000, 252).tolist()
        eq_bh = np.linspace(10_000_000, 11_000_000, 252).tolist()
        m = compute_metrics(_make_result(eq_strat, bh_equities=eq_bh))
        assert m.bh_total_return is not None
        assert m.bh_cagr is not None
        assert m.excess_return is not None
        assert m.excess_return > 0  # strategy outperforms

    def test_sortino_only_downside(self):
        """Sortino should use only downside deviation."""
        # Mix of up and down days
        eq = [100.0, 105.0, 102.0, 108.0, 103.0, 110.0, 107.0, 112.0, 108.0, 115.0]
        m = compute_metrics(_make_result(eq))
        # Sortino should be >= Sharpe when there are positive returns
        # (downside vol <= total vol)
        assert m.sortino >= m.sharpe or m.sortino == pytest.approx(m.sharpe, abs=0.5)

    def test_calmar_ratio(self):
        """Calmar = CAGR / |MDD|."""
        equities = [100, 110, 120, 100, 90, 120, 130]
        m = compute_metrics(_make_result(equities))
        expected_calmar = m.cagr / abs(m.mdd)
        assert m.calmar == pytest.approx(expected_calmar, rel=1e-4)

    def test_turnover(self):
        """Turnover = num_trades / years."""
        trades = [
            TradeRecord("A", date(2024, 1, 2), 100, date(2024, 1, 10), 110, "long", 10, 100.0, 2.0),
        ] * 10
        eq = [10_000_000.0] * 252
        m = compute_metrics(_make_result(eq, trades=trades))
        assert m.turnover == pytest.approx(10.0, rel=0.01)

    def test_empty_result(self):
        """Empty equity curve → zero metrics."""
        result = BacktestResult(
            strategy_id="test",
            asset_id="TEST",
            config=BacktestConfig(),
            equity_curve=pd.DataFrame(columns=["date", "equity", "drawdown"]),
            trades=[],
            buy_hold_equity=pd.DataFrame(columns=["date", "equity"]),
        )
        m = compute_metrics(result)
        assert m.total_return == 0.0
        assert m.cagr == 0.0
        assert m.num_trades == 0


# ---------------------------------------------------------------------------
# Test: metrics_to_dict
# ---------------------------------------------------------------------------

class TestMetricsToDict:
    def test_roundtrip(self):
        eq = np.linspace(10_000_000, 11_000_000, 252).tolist()
        bh = np.linspace(10_000_000, 10_500_000, 252).tolist()
        m = compute_metrics(_make_result(eq, bh_equities=bh))
        d = metrics_to_dict(m)
        assert isinstance(d, dict)
        assert "cagr" in d
        assert "sharpe" in d
        assert "bh_cagr" in d
        assert d["num_trades"] == 0
        # All float values should be rounded
        assert isinstance(d["cagr"], float)

    def test_none_bh_fields(self):
        eq = [10_000_000.0] * 10
        m = compute_metrics(_make_result(eq))
        d = metrics_to_dict(m)
        assert d["bh_total_return"] is None
        assert d["bh_cagr"] is None
        assert d["excess_return"] is None

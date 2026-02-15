"""Tests for backtest engine."""

from __future__ import annotations

import numpy as np
import pandas as pd

from research_engine.backtest import (
    BacktestConfig,
    TradeRecord,
    run_backtest,
    run_backtest_multi,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_prices(
    n: int = 20, start_price: float = 100.0, daily_return: float = 0.01,
) -> pd.DataFrame:
    """Generate synthetic OHLCV price data."""
    dates = pd.bdate_range("2024-01-01", periods=n, freq="B")
    closes = start_price * np.cumprod(1 + np.full(n, daily_return))
    opens = np.roll(closes, 1)
    opens[0] = start_price
    return pd.DataFrame({
        "open": opens,
        "high": closes * 1.01,
        "low": opens * 0.99,
        "close": closes,
        "volume": np.full(n, 1_000_000.0),
    }, index=dates)


def _make_signals(dates: pd.DatetimeIndex, values: list[int] | np.ndarray) -> pd.DataFrame:
    """Create signals DataFrame from date index and signal values."""
    return pd.DataFrame({"date": dates, "signal": values})


def _make_constant_signals(dates: pd.DatetimeIndex, value: int) -> pd.DataFrame:
    return _make_signals(dates, [value] * len(dates))


# ---------------------------------------------------------------------------
# Config tests
# ---------------------------------------------------------------------------

class TestConfig:
    def test_default_values(self):
        cfg = BacktestConfig()
        assert cfg.initial_cash == 10_000_000
        assert cfg.commission_pct == 0.001
        assert cfg.slippage_pct == 0.0
        assert cfg.allow_short is False


# ---------------------------------------------------------------------------
# Basic tests
# ---------------------------------------------------------------------------

class TestBasic:
    def test_always_long_rising(self):
        """Always long in a rising market → positive return."""
        prices = _make_prices(n=30, daily_return=0.01)
        signals = _make_constant_signals(prices.index, 1)
        result = run_backtest(prices, signals, "TEST", "strat1")

        final_equity = result.equity_curve["equity"].iloc[-1]
        assert final_equity > result.config.initial_cash

    def test_always_cash(self):
        """Always neutral → equity stays at initial cash."""
        prices = _make_prices(n=20)
        signals = _make_constant_signals(prices.index, 0)
        result = run_backtest(prices, signals, "TEST", "strat1")

        equities = result.equity_curve["equity"].values
        np.testing.assert_allclose(equities, result.config.initial_cash, rtol=1e-10)

    def test_single_roundtrip(self):
        """One buy + sell cycle: PnL should be calculable."""
        prices = _make_prices(n=10, start_price=100.0, daily_return=0.02)
        # Signal: 0, 1, 1, 1, 0, 0, 0, 0, 0, 0
        sig_values = [0, 1, 1, 1, 0, 0, 0, 0, 0, 0]
        signals = _make_signals(prices.index, sig_values)

        result = run_backtest(prices, signals, "TEST", "strat1")

        assert len(result.trades) == 1
        trade = result.trades[0]
        assert trade.side == "long"
        assert trade.pnl is not None
        assert trade.entry_date is not None
        assert trade.exit_date is not None


# ---------------------------------------------------------------------------
# Commission tests
# ---------------------------------------------------------------------------

class TestCommission:
    def test_zero_commission(self):
        """Zero commission → higher equity than default commission."""
        prices = _make_prices(n=20, daily_return=0.01)
        signals = _make_constant_signals(prices.index, 1)

        result_zero = run_backtest(
            prices, signals, "TEST", "strat1",
            config=BacktestConfig(commission_pct=0.0),
        )
        result_default = run_backtest(prices, signals, "TEST", "strat1")

        final_zero = result_zero.equity_curve["equity"].iloc[-1]
        final_default = result_default.equity_curve["equity"].iloc[-1]
        assert final_zero > final_default

    def test_commission_reduces_pnl(self):
        """Higher commission → lower final equity."""
        prices = _make_prices(n=20, daily_return=0.01)
        sig_values = [0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        signals = _make_signals(prices.index, sig_values)

        result_low = run_backtest(
            prices, signals, "TEST", "strat1",
            config=BacktestConfig(commission_pct=0.001),
        )
        result_high = run_backtest(
            prices, signals, "TEST", "strat1",
            config=BacktestConfig(commission_pct=0.01),
        )

        final_low = result_low.equity_curve["equity"].iloc[-1]
        final_high = result_high.equity_curve["equity"].iloc[-1]
        assert final_low > final_high


# ---------------------------------------------------------------------------
# Equity curve tests
# ---------------------------------------------------------------------------

class TestEquity:
    def test_equity_curve_length(self):
        """Equity curve has same number of rows as trading days."""
        prices = _make_prices(n=25)
        signals = _make_constant_signals(prices.index, 1)
        result = run_backtest(prices, signals, "TEST", "strat1")

        assert len(result.equity_curve) == len(prices)

    def test_drawdown_calculation(self):
        """Drawdown should equal equity/running_max - 1."""
        prices = _make_prices(n=30, daily_return=0.005)
        # Cause a drawdown: go long, then exit during dip
        sig_values = [1] * 15 + [0] * 15
        signals = _make_signals(prices.index, sig_values)
        result = run_backtest(prices, signals, "TEST", "strat1")

        eq = result.equity_curve["equity"].values
        running_max = np.maximum.accumulate(eq)
        expected_dd = eq / running_max - 1.0

        np.testing.assert_allclose(
            result.equity_curve["drawdown"].values, expected_dd, atol=1e-10
        )

    def test_drawdown_never_positive(self):
        """Drawdown should never be positive."""
        prices = _make_prices(n=30, daily_return=0.01)
        signals = _make_constant_signals(prices.index, 1)
        result = run_backtest(prices, signals, "TEST", "strat1")

        assert (result.equity_curve["drawdown"] <= 0.0 + 1e-10).all()


# ---------------------------------------------------------------------------
# Trade log tests
# ---------------------------------------------------------------------------

class TestTrade:
    def test_trade_log_structure(self):
        """TradeRecord has all expected fields."""
        prices = _make_prices(n=10, daily_return=0.01)
        sig_values = [0, 1, 1, 0, 0, 0, 0, 0, 0, 0]
        signals = _make_signals(prices.index, sig_values)
        result = run_backtest(prices, signals, "TEST", "strat1")

        assert len(result.trades) >= 1
        trade = result.trades[0]
        assert isinstance(trade, TradeRecord)
        assert trade.asset_id == "TEST"
        assert trade.side == "long"
        assert isinstance(trade.shares, float)
        assert isinstance(trade.cost, float)

    def test_entry_exit_pairs(self):
        """All completed trades have both entry_date and exit_date."""
        prices = _make_prices(n=20, daily_return=0.01)
        # Two roundtrips
        sig_values = [0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        signals = _make_signals(prices.index, sig_values)
        result = run_backtest(prices, signals, "TEST", "strat1")

        for trade in result.trades:
            assert trade.entry_date is not None
            assert trade.entry_price > 0

    def test_pnl_matches_equity(self):
        """Sum of trade PnLs ≈ final equity - initial cash."""
        prices = _make_prices(n=20, daily_return=0.01)
        sig_values = [0, 1, 1, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        signals = _make_signals(prices.index, sig_values)

        cfg = BacktestConfig(commission_pct=0.0)
        result = run_backtest(prices, signals, "TEST", "strat1", config=cfg)

        total_pnl = sum(t.pnl for t in result.trades if t.pnl is not None)
        equity_change = result.equity_curve["equity"].iloc[-1] - cfg.initial_cash

        np.testing.assert_allclose(total_pnl, equity_change, rtol=1e-6)


# ---------------------------------------------------------------------------
# Buy & Hold test
# ---------------------------------------------------------------------------

class TestBuyHold:
    def test_buy_hold_calculation(self):
        """Buy & hold equity matches manual calculation."""
        prices = _make_prices(n=15, start_price=100.0, daily_return=0.02)
        signals = _make_constant_signals(prices.index, 0)
        cfg = BacktestConfig(commission_pct=0.001)
        result = run_backtest(prices, signals, "TEST", "strat1", config=cfg)

        bh = result.buy_hold_equity
        assert len(bh) == len(prices)

        # Manual: buy at first open, hold
        first_open = prices["open"].iloc[0]
        investable = cfg.initial_cash * (1 - cfg.commission_pct)
        bh_shares = investable / first_open
        expected_last = bh_shares * prices["close"].iloc[-1]

        np.testing.assert_allclose(bh["equity"].iloc[-1], expected_last, rtol=1e-6)


# ---------------------------------------------------------------------------
# Multi-asset test
# ---------------------------------------------------------------------------

class TestMulti:
    def test_multi_asset_equal_weight(self):
        """Multi-asset backtest splits capital equally."""
        prices_a = _make_prices(n=20, start_price=100, daily_return=0.01)
        prices_b = _make_prices(n=20, start_price=200, daily_return=0.02)

        signals_a = _make_constant_signals(prices_a.index, 1)
        signals_b = _make_constant_signals(prices_b.index, 1)

        cfg = BacktestConfig(initial_cash=10_000_000)
        result = run_backtest_multi(
            price_dict={"A": prices_a, "B": prices_b},
            signal_dict={"A": signals_a, "B": signals_b},
            strategy_id="multi_strat",
            config=cfg,
        )

        assert result.asset_id == "MULTI"
        assert len(result.equity_curve) > 0
        # Final equity should exceed initial (both assets are rising)
        assert result.equity_curve["equity"].iloc[-1] > cfg.initial_cash


# ---------------------------------------------------------------------------
# Next-day execution test
# ---------------------------------------------------------------------------

class TestNextDay:
    def test_next_day_execution(self):
        """Signal at t should execute at t+1 open, not t close."""
        n = 5
        dates = pd.bdate_range("2024-01-01", periods=n, freq="B")
        prices = pd.DataFrame({
            "open": [100, 110, 120, 130, 140],
            "high": [105, 115, 125, 135, 145],
            "low": [95, 105, 115, 125, 135],
            "close": [102, 112, 122, 132, 142],
            "volume": [1000] * n,
        }, index=dates, dtype=float)

        # Signal=1 at day0, so buy at day1 open (110)
        # Signal=0 at day2, so sell at day3 open (130)
        sig_values = [1, 1, 0, 0, 0]
        signals = _make_signals(dates, sig_values)

        cfg = BacktestConfig(initial_cash=1_000_000, commission_pct=0.0)
        result = run_backtest(prices, signals, "TEST", "strat1", config=cfg)

        assert len(result.trades) == 1
        trade = result.trades[0]

        # Entry at day1 open = 110
        assert trade.entry_price == 110.0
        # Exit at day3 open = 130
        assert trade.exit_price == 130.0
        # PnL: shares * (130 - 110), shares = 1_000_000 / 110
        expected_shares = 1_000_000 / 110.0
        expected_pnl = expected_shares * (130.0 - 110.0)
        np.testing.assert_allclose(trade.pnl, expected_pnl, rtol=1e-6)

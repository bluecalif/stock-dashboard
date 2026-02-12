"""Tests for strategy framework and all three strategies."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research_engine.strategies import STRATEGY_REGISTRY, get_strategy
from research_engine.strategies.base import SignalResult, Strategy, _empty_signal_df
from research_engine.strategies.mean_reversion import MeanReversionStrategy
from research_engine.strategies.momentum import MomentumStrategy
from research_engine.strategies.trend import TrendStrategy

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_dates(n: int = 100) -> pd.DatetimeIndex:
    return pd.bdate_range("2024-01-01", periods=n, freq="B")


def _make_factors_df(n: int = 100, **overrides) -> pd.DataFrame:
    """Generate a synthetic factors DataFrame."""
    dates = _make_dates(n)
    rng = np.random.default_rng(42)

    data = {
        "close": 100 + np.cumsum(rng.normal(0, 1, n)),
        "open": 100 + np.cumsum(rng.normal(0, 1, n)),
        "high": 105 + np.cumsum(rng.normal(0, 1, n)),
        "low": 95 + np.cumsum(rng.normal(0, 1, n)),
        "volume": rng.integers(1000, 10000, n).astype(float),
        "ret_1d": rng.normal(0, 0.02, n),
        "ret_5d": rng.normal(0, 0.05, n),
        "ret_20d": rng.normal(0, 0.10, n),
        "ret_63d": rng.normal(0.03, 0.15, n),
        "sma_20": 100 + np.cumsum(rng.normal(0, 0.5, n)),
        "sma_60": 100 + np.cumsum(rng.normal(0, 0.3, n)),
        "sma_120": 100 + np.cumsum(rng.normal(0, 0.2, n)),
        "ema_12": 100 + np.cumsum(rng.normal(0, 0.5, n)),
        "ema_26": 100 + np.cumsum(rng.normal(0, 0.4, n)),
        "macd": rng.normal(0, 1, n),
        "roc": rng.normal(0, 5, n),
        "rsi_14": rng.uniform(20, 80, n),
        "vol_20": rng.uniform(0.10, 0.35, n),
        "atr_14": rng.uniform(1, 5, n),
        "vol_zscore_20": rng.normal(0, 1, n),
    }
    data.update(overrides)
    return pd.DataFrame(data, index=dates)


# ---------------------------------------------------------------------------
# Strategy Registry
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_registry_has_three_strategies(self):
        assert len(STRATEGY_REGISTRY) == 3
        assert "momentum" in STRATEGY_REGISTRY
        assert "trend" in STRATEGY_REGISTRY
        assert "mean_reversion" in STRATEGY_REGISTRY

    def test_get_strategy_returns_instance(self):
        s = get_strategy("momentum")
        assert isinstance(s, MomentumStrategy)
        assert isinstance(s, Strategy)

    def test_get_strategy_with_params(self):
        s = get_strategy("momentum", ret_threshold=0.10)
        assert s.ret_threshold == 0.10

    def test_get_strategy_unknown_raises(self):
        with pytest.raises(KeyError, match="Unknown strategy"):
            get_strategy("unknown_strat")


# ---------------------------------------------------------------------------
# Base Strategy
# ---------------------------------------------------------------------------

class TestBaseStrategy:
    def test_empty_signal_df(self):
        df = _empty_signal_df()
        assert list(df.columns) == ["date", "signal", "score", "action", "meta_json"]
        assert len(df) == 0

    def test_signal_result_fields(self):
        df = _empty_signal_df()
        sr = SignalResult(
            asset_id="TEST", strategy_id="test", signals=df
        )
        assert sr.asset_id == "TEST"
        assert sr.n_entry == 0

    def test_generate_signals_returns_signal_result(self):
        strat = MomentumStrategy()
        factors = _make_factors_df()
        result = strat.generate_signals(factors, "TEST")
        assert isinstance(result, SignalResult)
        assert result.asset_id == "TEST"
        assert result.strategy_id == "momentum"

    def test_generate_signals_output_columns(self):
        strat = TrendStrategy()
        factors = _make_factors_df()
        result = strat.generate_signals(factors, "TEST")
        expected_cols = {"date", "signal", "score", "action", "meta_json"}
        assert set(result.signals.columns) == expected_cols

    def test_signal_values_are_valid(self):
        strat = MomentumStrategy()
        factors = _make_factors_df()
        result = strat.generate_signals(factors, "TEST")
        signals = result.signals["signal"]
        assert signals.isin([+1, 0, -1]).all()

    def test_action_labels_are_valid(self):
        strat = MomentumStrategy()
        factors = _make_factors_df()
        result = strat.generate_signals(factors, "TEST")
        actions = result.signals["action"]
        assert actions.isin(["entry", "exit", "hold"]).all()

    def test_entry_exit_counts_match_result(self):
        strat = MomentumStrategy()
        factors = _make_factors_df()
        result = strat.generate_signals(factors, "TEST")
        df = result.signals
        assert result.n_entry == (df["action"] == "entry").sum()
        assert result.n_exit == (df["action"] == "exit").sum()
        assert result.n_hold == (df["action"] == "hold").sum()


# ---------------------------------------------------------------------------
# Momentum Strategy
# ---------------------------------------------------------------------------

class TestMomentumStrategy:
    def test_strategy_id(self):
        s = MomentumStrategy()
        assert s.strategy_id == "momentum"

    def test_all_strong_momentum_gives_long(self):
        """When ret_63d is always high and vol is low, signal should be 1."""
        factors = _make_factors_df(
            ret_63d=np.full(100, 0.20),  # well above threshold
            vol_20=np.full(100, 0.15),    # well below cap
        )
        strat = MomentumStrategy(ret_threshold=0.05, vol_cap=0.40)
        result = strat.generate_signals(factors, "TEST")
        # After first entry, should stay long
        signals = result.signals["signal"]
        assert (signals == 1).sum() >= 95

    def test_high_vol_prevents_entry(self):
        """When volatility exceeds cap, no long position."""
        factors = _make_factors_df(
            ret_63d=np.full(100, 0.20),
            vol_20=np.full(100, 0.50),  # above cap
        )
        strat = MomentumStrategy(vol_cap=0.40)
        result = strat.generate_signals(factors, "TEST")
        signals = result.signals["signal"]
        assert (signals == 1).sum() == 0

    def test_weak_momentum_exits(self):
        """Momentum drops below exit threshold → exit."""
        ret = np.concatenate([
            np.full(30, 0.20),   # strong momentum → entry
            np.full(20, -0.10),  # weak → should exit
            np.full(50, 0.20),   # strong again → re-entry
        ])
        factors = _make_factors_df(
            ret_63d=ret,
            vol_20=np.full(100, 0.15),
        )
        strat = MomentumStrategy()
        result = strat.generate_signals(factors, "TEST")
        # Should have at least 2 entries (initial + re-entry)
        assert result.n_entry >= 2

    def test_missing_factors_returns_empty(self):
        factors = _make_factors_df().drop(columns=["ret_63d"])
        strat = MomentumStrategy()
        result = strat.generate_signals(factors, "TEST")
        assert len(result.signals) == 0

    def test_meta_contains_factor_values(self):
        factors = _make_factors_df(
            ret_63d=np.full(100, 0.20),
            vol_20=np.full(100, 0.15),
        )
        strat = MomentumStrategy()
        result = strat.generate_signals(factors, "TEST")
        # Find a row with meta
        non_null_meta = result.signals["meta_json"].dropna()
        if len(non_null_meta) > 0:
            meta = non_null_meta.iloc[0]
            assert "ret_63d" in meta
            assert "vol_20" in meta


# ---------------------------------------------------------------------------
# Trend Strategy
# ---------------------------------------------------------------------------

class TestTrendStrategy:
    def test_strategy_id(self):
        s = TrendStrategy()
        assert s.strategy_id == "trend"

    def test_golden_cross_gives_long(self):
        """When fast SMA > slow SMA, signal is 1."""
        factors = _make_factors_df(
            sma_20=np.full(100, 110.0),  # above slow
            sma_60=np.full(100, 100.0),
        )
        strat = TrendStrategy()
        result = strat.generate_signals(factors, "TEST")
        signals = result.signals["signal"]
        assert (signals == 1).all()

    def test_dead_cross_gives_neutral(self):
        """When fast SMA < slow SMA, signal is 0."""
        factors = _make_factors_df(
            sma_20=np.full(100, 90.0),   # below slow
            sma_60=np.full(100, 100.0),
        )
        strat = TrendStrategy()
        result = strat.generate_signals(factors, "TEST")
        signals = result.signals["signal"]
        assert (signals == 0).all()

    def test_crossover_generates_entry_exit(self):
        """Crossover from below to above generates entry, then exit on reverse."""
        sma_20 = np.concatenate([
            np.full(30, 90.0),   # below → neutral
            np.full(40, 110.0),  # above → long (entry)
            np.full(30, 90.0),   # below → neutral (exit)
        ])
        factors = _make_factors_df(
            sma_20=sma_20,
            sma_60=np.full(100, 100.0),
        )
        strat = TrendStrategy()
        result = strat.generate_signals(factors, "TEST")
        assert result.n_entry >= 1
        assert result.n_exit >= 1

    def test_custom_columns(self):
        """Can use different SMA columns."""
        factors = _make_factors_df(
            ema_12=np.full(100, 110.0),
            ema_26=np.full(100, 100.0),
        )
        strat = TrendStrategy(fast_col="ema_12", slow_col="ema_26")
        result = strat.generate_signals(factors, "TEST")
        assert (result.signals["signal"] == 1).all()

    def test_missing_factors_returns_empty(self):
        factors = _make_factors_df().drop(columns=["sma_20"])
        strat = TrendStrategy()
        result = strat.generate_signals(factors, "TEST")
        assert len(result.signals) == 0


# ---------------------------------------------------------------------------
# Mean Reversion Strategy
# ---------------------------------------------------------------------------

class TestMeanReversionStrategy:
    def test_strategy_id(self):
        s = MeanReversionStrategy()
        assert s.strategy_id == "mean_reversion"

    def test_oversold_recovery_gives_entry(self):
        """Price drops below -2σ then recovers → entry signal."""
        # Create price that drops sharply then recovers
        close = np.concatenate([
            np.full(40, 100.0),   # stable
            np.linspace(100, 80, 20),   # sharp drop
            np.linspace(80, 100, 40),   # recovery
        ])
        factors = _make_factors_df(close=close)
        strat = MeanReversionStrategy(lookback=20, entry_z=-1.5)
        result = strat.generate_signals(factors, "TEST")
        # Should have at least one entry during recovery
        assert result.n_entry >= 1

    def test_no_entry_when_stable(self):
        """Stable prices with no extreme z-scores → no entries."""
        # Perfectly constant price → std=0, z-score defaults to 0
        close = np.full(100, 100.0)
        factors = _make_factors_df(close=close)
        strat = MeanReversionStrategy(lookback=20, entry_z=-2.0)
        result = strat.generate_signals(factors, "TEST")
        assert result.n_entry == 0

    def test_stop_loss_exits(self):
        """Continued decline past stop-loss → exit."""
        close = np.concatenate([
            np.full(30, 100.0),
            np.linspace(100, 70, 30),  # steep drop
            np.linspace(70, 60, 40),   # continued decline
        ])
        factors = _make_factors_df(close=close)
        strat = MeanReversionStrategy(
            lookback=20, entry_z=-1.0, stop_z=-2.5
        )
        result = strat.generate_signals(factors, "TEST")
        # If entered, should have exited via stop loss
        if result.n_entry > 0:
            assert result.n_exit >= 1

    def test_missing_close_returns_empty(self):
        factors = _make_factors_df().drop(columns=["close"])
        strat = MeanReversionStrategy()
        result = strat.generate_signals(factors, "TEST")
        assert len(result.signals) == 0

    def test_signal_values_valid(self):
        factors = _make_factors_df()
        strat = MeanReversionStrategy()
        result = strat.generate_signals(factors, "TEST")
        assert result.signals["signal"].isin([0, 1, -1]).all()

    def test_meta_contains_zscore(self):
        close = np.concatenate([
            np.full(40, 100.0),
            np.linspace(100, 80, 20),
            np.linspace(80, 100, 40),
        ])
        factors = _make_factors_df(close=close)
        strat = MeanReversionStrategy(lookback=20, entry_z=-1.5)
        result = strat.generate_signals(factors, "TEST")
        non_null_meta = result.signals["meta_json"].dropna()
        if len(non_null_meta) > 0:
            meta = non_null_meta.iloc[0]
            assert "zscore" in meta

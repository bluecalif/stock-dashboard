"""Tests for research_engine.factors module."""

import numpy as np
import pandas as pd
import pytest

from research_engine.factors import (
    ALL_FACTOR_NAMES,
    compute_all_factors,
    compute_atr,
    compute_ema,
    compute_macd,
    compute_returns,
    compute_roc,
    compute_rsi,
    compute_sma,
    compute_volatility,
    compute_volume_zscore,
)


def _make_ohlcv(n=100, base_price=100.0, seed=42):
    """Generate deterministic OHLCV DataFrame for testing."""
    rng = np.random.RandomState(seed)
    dates = pd.bdate_range("2025-06-01", periods=n)
    returns = rng.normal(0.001, 0.02, n)
    close = base_price * np.cumprod(1 + returns)
    high = close * (1 + rng.uniform(0, 0.02, n))
    low = close * (1 - rng.uniform(0, 0.02, n))
    open_ = close * (1 + rng.uniform(-0.01, 0.01, n))
    volume = rng.randint(10000, 100000, n)

    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )


@pytest.fixture
def ohlcv():
    return _make_ohlcv(n=150)


# --- Returns ---


class TestComputeReturns:
    def test_output_columns(self, ohlcv):
        result = compute_returns(ohlcv)
        assert list(result.columns) == ["ret_1d", "ret_5d", "ret_20d", "ret_63d"]

    def test_ret_1d_calculation(self, ohlcv):
        result = compute_returns(ohlcv)
        expected = ohlcv["close"].pct_change(1)
        pd.testing.assert_series_equal(result["ret_1d"], expected, check_names=False)

    def test_ret_5d_calculation(self, ohlcv):
        result = compute_returns(ohlcv)
        expected = ohlcv["close"].pct_change(5)
        pd.testing.assert_series_equal(result["ret_5d"], expected, check_names=False)

    def test_nan_count_ret_63d(self, ohlcv):
        result = compute_returns(ohlcv)
        assert result["ret_63d"].isna().sum() == 63


# --- SMA ---


class TestComputeSma:
    def test_output_columns(self, ohlcv):
        result = compute_sma(ohlcv)
        assert list(result.columns) == ["sma_20", "sma_60", "sma_120"]

    def test_sma_20_value(self, ohlcv):
        result = compute_sma(ohlcv)
        expected = ohlcv["close"].rolling(20).mean()
        pd.testing.assert_series_equal(result["sma_20"], expected, check_names=False)

    def test_sma_120_nan_count(self, ohlcv):
        result = compute_sma(ohlcv)
        assert result["sma_120"].isna().sum() == 119


# --- EMA ---


class TestComputeEma:
    def test_output_columns(self, ohlcv):
        result = compute_ema(ohlcv)
        assert list(result.columns) == ["ema_12", "ema_26"]

    def test_ema_12_not_all_nan(self, ohlcv):
        result = compute_ema(ohlcv)
        assert result["ema_12"].notna().sum() > 0


# --- MACD ---


class TestComputeMacd:
    def test_macd_equals_ema_diff(self, ohlcv):
        macd = compute_macd(ohlcv)
        ema = compute_ema(ohlcv)
        expected = ema["ema_12"] - ema["ema_26"]
        pd.testing.assert_series_equal(macd["macd"], expected, check_names=False)


# --- ROC ---


class TestComputeRoc:
    def test_roc_calculation(self, ohlcv):
        result = compute_roc(ohlcv, period=12)
        close = ohlcv["close"]
        expected = (close / close.shift(12) - 1) * 100
        pd.testing.assert_series_equal(result["roc"], expected, check_names=False)

    def test_roc_nan_count(self, ohlcv):
        result = compute_roc(ohlcv)
        assert result["roc"].isna().sum() == 12


# --- RSI ---


class TestComputeRsi:
    def test_rsi_range(self, ohlcv):
        result = compute_rsi(ohlcv)
        valid = result["rsi_14"].dropna()
        assert (valid >= 0).all()
        assert (valid <= 100).all()

    def test_rsi_nan_for_initial_period(self, ohlcv):
        result = compute_rsi(ohlcv)
        # ewm(min_periods=14): first 13 rows are NaN (delta.where converts NaN→0)
        assert result["rsi_14"].isna().sum() >= 13

    def test_rsi_all_up(self):
        """All positive returns → RSI near 100."""
        df = pd.DataFrame(
            {"close": [100.0 + i for i in range(50)]},
            index=pd.bdate_range("2025-06-01", periods=50),
        )
        result = compute_rsi(df)
        valid = result["rsi_14"].dropna()
        assert valid.iloc[-1] > 90

    def test_rsi_all_down(self):
        """All negative returns → RSI near 0."""
        df = pd.DataFrame(
            {"close": [200.0 - i for i in range(50)]},
            index=pd.bdate_range("2025-06-01", periods=50),
        )
        result = compute_rsi(df)
        valid = result["rsi_14"].dropna()
        assert valid.iloc[-1] < 10


# --- Volatility ---


class TestComputeVolatility:
    def test_vol_20_positive(self, ohlcv):
        result = compute_volatility(ohlcv)
        valid = result["vol_20"].dropna()
        assert (valid >= 0).all()

    def test_vol_20_nan_count(self, ohlcv):
        result = compute_volatility(ohlcv)
        # 1 NaN from pct_change + 19 from rolling = 20
        assert result["vol_20"].isna().sum() == 20


# --- ATR ---


class TestComputeAtr:
    def test_atr_positive(self, ohlcv):
        result = compute_atr(ohlcv)
        valid = result["atr_14"].dropna()
        assert (valid >= 0).all()

    def test_atr_nan_initial(self, ohlcv):
        result = compute_atr(ohlcv)
        # shift(1) produces 1 NaN, but max(axis=1) skips NaN → tr has 0 NaN
        # ewm(min_periods=14): first 13 rows are NaN
        assert result["atr_14"].isna().sum() >= 13


# --- Volume Z-Score ---


class TestComputeVolumeZscore:
    def test_zscore_mean_near_zero(self, ohlcv):
        result = compute_volume_zscore(ohlcv)
        valid = result["vol_zscore_20"].dropna()
        assert abs(valid.mean()) < 1.0

    def test_zscore_nan_count(self, ohlcv):
        result = compute_volume_zscore(ohlcv)
        assert result["vol_zscore_20"].isna().sum() >= 19


# --- All Factors ---


class TestComputeAllFactors:
    def test_all_columns_present(self, ohlcv):
        result = compute_all_factors(ohlcv)
        assert set(result.columns) == set(ALL_FACTOR_NAMES)

    def test_correct_row_count(self, ohlcv):
        result = compute_all_factors(ohlcv)
        assert len(result) == len(ohlcv)

    def test_no_duplicate_columns(self, ohlcv):
        result = compute_all_factors(ohlcv)
        assert len(result.columns) == len(set(result.columns))

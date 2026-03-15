"""Tests for indicator_analysis — confirmed indicators (RSI, MACD, ATR/Price, vol_20)."""

import math

import pytest

from api.services.analysis.indicator_analysis import (
    FACTOR_DISPLAY_NAMES,
    INDICATOR_RULES,
    SUCCESS_RATE_FACTORS,
    IndicatorState,
    interpret_indicator_state,
    interpret_macd_histogram,
    interpret_multiple,
)

# ---------------------------------------------------------------------------
# RSI
# ---------------------------------------------------------------------------

class TestRSI:
    @pytest.mark.parametrize("value,expected_level,expected_signal", [
        (85,  "extreme_overbought", "sell"),
        (80,  "extreme_overbought", "sell"),
        (75,  "overbought",         "sell"),
        (70,  "overbought",         "sell"),
        (65,  "bullish",            "neutral"),
        (50,  "neutral",            "neutral"),
        (35,  "bearish",            "neutral"),
        (30,  "oversold",           "buy"),
        (25,  "oversold",           "buy"),
        (20,  "extreme_oversold",   "buy"),
        (15,  "extreme_oversold",   "buy"),
    ])
    def test_rsi_ranges(self, value, expected_level, expected_signal):
        result = interpret_indicator_state("rsi_14", value)
        assert result.level == expected_level
        assert result.signal == expected_signal
        assert result.factor_name == "rsi_14"
        assert result.value == value

    def test_rsi_has_description(self):
        result = interpret_indicator_state("rsi_14", 50)
        assert len(result.description) > 0
        assert len(result.label) > 0


# ---------------------------------------------------------------------------
# MACD histogram
# ---------------------------------------------------------------------------

class TestMACDHistogram:
    def test_golden_cross(self):
        result = interpret_macd_histogram(macd=500.0, macd_signal=300.0)
        assert result.level == "bullish_cross"
        assert result.signal == "buy"
        assert result.factor_name == "macd"
        assert result.value == 200.0  # histogram = 500 - 300
        assert "골든크로스" in result.label

    def test_dead_cross(self):
        result = interpret_macd_histogram(macd=-100.0, macd_signal=50.0)
        assert result.level == "bearish_cross"
        assert result.signal == "sell"
        assert result.value == -150.0
        assert "데드크로스" in result.label

    def test_exact_cross(self):
        result = interpret_macd_histogram(macd=100.0, macd_signal=100.0)
        assert result.level == "neutral"
        assert result.signal == "neutral"

    def test_description_contains_values(self):
        result = interpret_macd_histogram(macd=500.0, macd_signal=300.0)
        assert "500.00" in result.description
        assert "300.00" in result.description


# ---------------------------------------------------------------------------
# vol_20 (warning only)
# ---------------------------------------------------------------------------

class TestVol20:
    @pytest.mark.parametrize("value,expected_level,expected_signal", [
        (0.6,  "very_high_vol_warning", "sell"),
        (0.5,  "very_high_vol_warning", "sell"),
        (0.4,  "high_vol_warning",      "sell"),
        (0.3,  "high_vol_warning",      "sell"),
        (0.2,  "normal_vol",            "neutral"),
        (0.1,  "normal_vol",            "neutral"),
    ])
    def test_vol20_ranges(self, value, expected_level, expected_signal):
        result = interpret_indicator_state("vol_20", value)
        assert result.level == expected_level
        assert result.signal == expected_signal

    def test_high_vol_warns_sell(self):
        """High volatility must signal sell (market entry warning)."""
        result = interpret_indicator_state("vol_20", 0.55)
        assert result.signal == "sell"
        assert "경고" in result.label


# ---------------------------------------------------------------------------
# ATR/Price ratio (warning only)
# ---------------------------------------------------------------------------

class TestATRPct:
    @pytest.mark.parametrize("value,expected_level,expected_signal", [
        (0.05,  "high_vol_warning", "sell"),
        (0.03,  "high_vol_warning", "sell"),
        (0.02,  "normal_vol",       "neutral"),
        (0.005, "low_vol",          "neutral"),
    ])
    def test_atr_pct_ranges(self, value, expected_level, expected_signal):
        result = interpret_indicator_state("atr_pct", value)
        assert result.level == expected_level
        assert result.signal == expected_signal

    def test_high_atr_warns_sell(self):
        """High ATR/price ratio must signal sell (market entry warning)."""
        result = interpret_indicator_state("atr_pct", 0.04)
        assert result.signal == "sell"
        assert "경고" in result.label


# ---------------------------------------------------------------------------
# interpret_multiple
# ---------------------------------------------------------------------------

class TestInterpretMultiple:
    def test_single_value_indicators(self):
        results = interpret_multiple({"rsi_14": 75.0, "vol_20": 0.4})
        assert len(results) == 2
        names = {r.factor_name for r in results}
        assert names == {"rsi_14", "vol_20"}

    def test_with_macd(self):
        results = interpret_multiple(
            {"rsi_14": 50.0},
            macd=500.0,
            macd_signal=300.0,
        )
        assert len(results) == 2
        names = {r.factor_name for r in results}
        assert names == {"rsi_14", "macd"}

    def test_nan_skipped(self):
        results = interpret_multiple({"rsi_14": float("nan"), "vol_20": 0.2})
        assert len(results) == 1
        assert results[0].factor_name == "vol_20"

    def test_inf_skipped(self):
        results = interpret_multiple({"rsi_14": math.inf})
        assert len(results) == 0

    def test_unknown_factor_skipped(self):
        results = interpret_multiple({"unknown": 1.0, "rsi_14": 50.0})
        assert len(results) == 1
        assert results[0].factor_name == "rsi_14"

    def test_empty_input(self):
        results = interpret_multiple({})
        assert results == []

    def test_macd_nan_skipped(self):
        results = interpret_multiple({}, macd=float("nan"), macd_signal=100.0)
        assert len(results) == 0

    def test_macd_none_skipped(self):
        results = interpret_multiple({}, macd=None, macd_signal=None)
        assert len(results) == 0


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrors:
    def test_unknown_factor_raises(self):
        with pytest.raises(ValueError, match="Unknown factor"):
            interpret_indicator_state("nonexistent_factor", 50.0)

    def test_excluded_factor_raises(self):
        """ROC, ret_*, SMA, EMA should NOT be in INDICATOR_RULES."""
        for excluded in ["roc", "ret_1d", "sma_20", "ema_12", "vol_zscore_20"]:
            with pytest.raises(ValueError):
                interpret_indicator_state(excluded, 50.0)


# ---------------------------------------------------------------------------
# Registry & constants
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_indicator_rules_keys(self):
        assert set(INDICATOR_RULES.keys()) == {"rsi_14", "vol_20", "atr_pct"}

    def test_display_names_cover_all(self):
        """Display names must cover all INDICATOR_RULES + macd."""
        expected = set(INDICATOR_RULES.keys()) | {"macd"}
        assert expected == set(FACTOR_DISPLAY_NAMES.keys())

    def test_success_rate_factors(self):
        assert SUCCESS_RATE_FACTORS == ["rsi_14", "macd"]

    def test_indicator_state_fields(self):
        result = interpret_indicator_state("rsi_14", 65.0)
        assert isinstance(result, IndicatorState)
        assert result.factor_name == "rsi_14"
        assert result.value == 65.0
        assert result.signal in ("buy", "sell", "neutral")
        assert result.level != ""
        assert result.label != ""
        assert result.description != ""

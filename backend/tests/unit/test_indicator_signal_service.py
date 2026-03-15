"""Tests for indicator_signal_service — on-the-fly signal generation."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from api.services.analysis.indicator_signal_service import (
    VALID_INDICATOR_IDS,
    IndicatorSignal,
    _generate_atr_vol_signals,
    _generate_macd_signals,
    _generate_rsi_signals,
    generate_indicator_signals,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dates(n: int, start: date = date(2026, 1, 1)) -> list[date]:
    """Generate n consecutive dates."""
    return [date(start.year, start.month, start.day + i) for i in range(n)]


def _factors_from_list(
    dates: list[date], values: dict[str, list[float | None]]
) -> dict[date, dict[str, float]]:
    """Build factor series from parallel lists."""
    result: dict[date, dict[str, float]] = {}
    for i, d in enumerate(dates):
        fvals = {}
        for fname, vlist in values.items():
            if i < len(vlist) and vlist[i] is not None:
                fvals[fname] = vlist[i]
        if fvals:
            result[d] = fvals
    return result


def _prices_from_list(dates: list[date], closes: list[float]) -> dict[date, float]:
    return {d: c for d, c in zip(dates, closes)}


# ---------------------------------------------------------------------------
# RSI signal tests
# ---------------------------------------------------------------------------

class TestRSISignals:
    def test_oversold_entry(self):
        """RSI crossing below 30 → buy signal."""
        ds = _dates(3)
        factors = _factors_from_list(ds, {"rsi_14": [35.0, 30.0, 28.0]})
        prices = _prices_from_list(ds, [100, 99, 98])

        signals = _generate_rsi_signals(ds, factors, prices)

        assert len(signals) == 1
        assert signals[0].signal == 1
        assert signals[0].label == "RSI 과매도 진입"
        assert signals[0].date == ds[2]  # 30→28 crosses below 30

    def test_overbought_entry(self):
        """RSI crossing above 70 → sell signal."""
        ds = _dates(3)
        factors = _factors_from_list(ds, {"rsi_14": [65.0, 70.0, 72.0]})
        prices = _prices_from_list(ds, [100, 105, 110])

        signals = _generate_rsi_signals(ds, factors, prices)

        assert len(signals) == 1
        assert signals[0].signal == -1
        assert signals[0].label == "RSI 과매수 진입"
        assert signals[0].date == ds[2]  # 70→72 crosses above 70

    def test_no_crossover(self):
        """RSI stays in neutral zone → no signal."""
        ds = _dates(5)
        factors = _factors_from_list(ds, {"rsi_14": [45, 50, 55, 50, 48]})
        prices = _prices_from_list(ds, [100] * 5)

        signals = _generate_rsi_signals(ds, factors, prices)

        assert len(signals) == 0

    def test_multiple_crossovers(self):
        """RSI crosses 30 then 70 → one buy then one sell."""
        ds = _dates(6)
        factors = _factors_from_list(ds, {"rsi_14": [35, 28, 50, 65, 72, 60]})
        prices = _prices_from_list(ds, [100, 98, 102, 108, 112, 106])

        signals = _generate_rsi_signals(ds, factors, prices)

        assert len(signals) == 2
        assert signals[0].signal == 1   # buy (35→28)
        assert signals[1].signal == -1  # sell (65→72)

    def test_exact_boundary_no_signal(self):
        """RSI at exactly 30 → no crossover (need to go below)."""
        ds = _dates(3)
        factors = _factors_from_list(ds, {"rsi_14": [35, 30, 30]})
        prices = _prices_from_list(ds, [100] * 3)

        signals = _generate_rsi_signals(ds, factors, prices)

        assert len(signals) == 0  # 30 is not < 30

    def test_missing_price_skipped(self):
        """Missing price on crossover date → no signal."""
        ds = _dates(3)
        factors = _factors_from_list(ds, {"rsi_14": [35, 28, 25]})
        prices = _prices_from_list(ds[:1] + ds[2:], [100, 98])  # day 1 missing

        signals = _generate_rsi_signals(ds, factors, prices)

        # day 1 has no close → skip. day 2 has prev=28, close=98
        assert all(s.entry_price > 0 for s in signals)


# ---------------------------------------------------------------------------
# MACD signal tests
# ---------------------------------------------------------------------------

class TestMACDSignals:
    def test_golden_cross(self):
        """Histogram negative → positive → buy signal."""
        ds = _dates(3)
        factors = _factors_from_list(ds, {
            "macd": [-1.0, -0.5, 0.5],
            "macd_signal": [0.0, 0.0, 0.0],
        })
        prices = _prices_from_list(ds, [100, 101, 102])

        signals = _generate_macd_signals(ds, factors, prices)

        assert len(signals) == 1
        assert signals[0].signal == 1
        assert signals[0].label == "MACD 골든크로스"
        assert signals[0].date == ds[2]

    def test_dead_cross(self):
        """Histogram positive → negative → sell signal."""
        ds = _dates(3)
        factors = _factors_from_list(ds, {
            "macd": [1.0, 0.5, -0.5],
            "macd_signal": [0.0, 0.0, 0.0],
        })
        prices = _prices_from_list(ds, [100, 99, 98])

        signals = _generate_macd_signals(ds, factors, prices)

        assert len(signals) == 1
        assert signals[0].signal == -1
        assert signals[0].label == "MACD 데드크로스"
        assert signals[0].date == ds[2]

    def test_no_crossover(self):
        """Histogram stays positive → no signal."""
        ds = _dates(4)
        factors = _factors_from_list(ds, {
            "macd": [1.0, 1.5, 2.0, 1.8],
            "macd_signal": [0.0, 0.0, 0.0, 0.0],
        })
        prices = _prices_from_list(ds, [100] * 4)

        signals = _generate_macd_signals(ds, factors, prices)

        assert len(signals) == 0

    def test_missing_macd_signal_skipped(self):
        """Missing macd_signal → skip that day."""
        ds = _dates(3)
        factors = _factors_from_list(ds, {
            "macd": [-1.0, -0.5, 0.5],
            # macd_signal missing on day 1
            "macd_signal": [None, 0.0, 0.0],
        })
        prices = _prices_from_list(ds, [100, 101, 102])

        signals = _generate_macd_signals(ds, factors, prices)

        # day 0 skipped (no macd_signal), so day 1 has no prev_hist
        # day 2: prev_hist=-0.5, hist=0.5 → golden cross
        assert len(signals) == 1
        assert signals[0].signal == 1


# ---------------------------------------------------------------------------
# ATR+vol signal tests
# ---------------------------------------------------------------------------

class TestATRVolSignals:
    def test_high_vol_entry(self):
        """ATR/Price exceeds 3% → warning signal."""
        ds = _dates(3)
        # atr_14=2 with close=100 → 2% (normal), then atr_14=4 → 4% (high)
        factors = _factors_from_list(ds, {
            "atr_14": [2.0, 2.5, 4.0],
            "vol_20": [0.1, 0.1, 0.1],
        })
        prices = _prices_from_list(ds, [100, 100, 100])

        signals = _generate_atr_vol_signals(ds, factors, prices)

        assert len(signals) == 1
        assert signals[0].signal == 0
        assert "진입" in signals[0].label
        assert signals[0].date == ds[2]

    def test_high_vol_exit(self):
        """High vol → normal → exit warning."""
        ds = _dates(3)
        factors = _factors_from_list(ds, {
            "atr_14": [4.0, 4.0, 2.0],
            "vol_20": [0.1, 0.1, 0.1],
        })
        prices = _prices_from_list(ds, [100, 100, 100])

        signals = _generate_atr_vol_signals(ds, factors, prices)

        # day 0: was_high=False, is_high=True(4%) → entry signal
        # day 1: was_high=True, is_high=True → no signal
        # day 2: was_high=True, is_high=False(2%) → exit signal
        assert len(signals) == 2
        assert "진입" in signals[0].label
        assert "복귀" in signals[1].label

    def test_vol20_threshold(self):
        """vol_20 > 0.3 triggers high vol even with low ATR."""
        ds = _dates(3)
        factors = _factors_from_list(ds, {
            "atr_14": [1.0, 1.0, 1.0],  # 1% always
            "vol_20": [0.2, 0.2, 0.35],
        })
        prices = _prices_from_list(ds, [100, 100, 100])

        signals = _generate_atr_vol_signals(ds, factors, prices)

        assert len(signals) == 1
        assert signals[0].date == ds[2]

    def test_already_high_no_duplicate(self):
        """Staying in high vol zone → no repeated signals."""
        ds = _dates(4)
        factors = _factors_from_list(ds, {
            "atr_14": [4.0, 5.0, 6.0, 4.5],
            "vol_20": [0.1, 0.1, 0.1, 0.1],
        })
        prices = _prices_from_list(ds, [100] * 4)

        signals = _generate_atr_vol_signals(ds, factors, prices)

        # Only one entry signal on day 0
        assert len(signals) == 1
        assert "진입" in signals[0].label


# ---------------------------------------------------------------------------
# Integration: generate_indicator_signals
# ---------------------------------------------------------------------------

class TestGenerateIndicatorSignals:
    def test_invalid_indicator_id(self):
        db = MagicMock()
        with pytest.raises(ValueError, match="Unknown indicator_id"):
            generate_indicator_signals(db, "005930", "unknown_indicator")

    def test_valid_indicator_ids(self):
        assert "rsi_14" in VALID_INDICATOR_IDS
        assert "macd" in VALID_INDICATOR_IDS
        assert "atr_vol" in VALID_INDICATOR_IDS

    @patch("api.services.analysis.indicator_signal_service.price_repo")
    @patch("api.services.analysis.indicator_signal_service.factor_repo")
    def test_rsi_integration(self, mock_factor_repo, mock_price_repo):
        """Full integration: factor_repo → signal generation."""
        ds = _dates(5)
        db = MagicMock()

        # Mock factor_repo.get_factors
        rsi_rows = []
        rsi_values = [35.0, 31.0, 28.0, 25.0, 32.0]
        for i, d in enumerate(ds):
            row = MagicMock()
            row.date = d
            row.value = rsi_values[i]
            rsi_rows.append(row)

        mock_factor_repo.get_factors.return_value = rsi_rows

        # Mock price_repo.get_prices
        price_rows = []
        for d in ds:
            row = MagicMock()
            row.date = d
            row.close = 100.0
            price_rows.append(row)

        mock_price_repo.get_prices.return_value = price_rows

        signals = generate_indicator_signals(db, "005930", "rsi_14")

        assert len(signals) >= 1
        assert all(isinstance(s, IndicatorSignal) for s in signals)
        assert all(s.indicator_id == "rsi_14" for s in signals)

    @patch("api.services.analysis.indicator_signal_service.price_repo")
    @patch("api.services.analysis.indicator_signal_service.factor_repo")
    def test_empty_data(self, mock_factor_repo, mock_price_repo):
        """No factor data → empty signals."""
        db = MagicMock()
        mock_factor_repo.get_factors.return_value = []
        mock_price_repo.get_prices.return_value = []

        signals = generate_indicator_signals(db, "005930", "rsi_14")

        assert signals == []

"""Tests for signal_accuracy_service — buy/sell success rate computation."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from api.services.analysis.signal_accuracy_service import (
    MIN_SIGNAL_COUNT,
    SignalAccuracyResult,
    compute_accuracy_all_strategies,
    compute_indicator_accuracy,
    compute_signal_accuracy,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_signal(asset_id: str, d: date, strategy_id: str, signal: int):
    """Create a mock SignalDaily row."""
    m = MagicMock()
    m.asset_id = asset_id
    m.date = d
    m.strategy_id = strategy_id
    m.signal = signal
    return m


def _make_price_row(d: date, close: float):
    """Create a mock (date, close) tuple for price query."""
    return (d, close)


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


# ---------------------------------------------------------------------------
# Mocking helpers — patch db.query chains
# ---------------------------------------------------------------------------

def _setup_mock_db(mock_db, signals, price_rows):
    """Configure mock_db.query chains for signals and prices."""
    # Track calls to db.query to distinguish between SignalDaily and PriceDaily
    signal_chain = MagicMock()
    signal_chain.filter.return_value = signal_chain
    signal_chain.order_by.return_value = signal_chain
    signal_chain.all.return_value = signals

    price_chain = MagicMock()
    price_chain.filter.return_value = price_chain
    price_chain.order_by.return_value = price_chain
    price_chain.all.return_value = price_rows

    def _query_side(*args):
        from db.models import SignalDaily
        chain = MagicMock()
        if len(args) == 1 and args[0] is SignalDaily:
            chain.filter.return_value = signal_chain
        else:
            # PriceDaily column query: db.query(PriceDaily.date, PriceDaily.close)
            chain.filter.return_value = price_chain
        return chain

    mock_db.query.side_effect = _query_side


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestComputeSignalAccuracy:
    def test_no_signals_returns_insufficient(self, mock_db):
        """Zero signals → insufficient_data=True."""
        _setup_mock_db(mock_db, signals=[], price_rows=[])

        result = compute_signal_accuracy(mock_db, "005930", "momentum")

        assert result.total_signals == 0
        assert result.evaluated_signals == 0
        assert result.insufficient_data is True

    def test_no_prices_returns_insufficient(self, mock_db):
        """Signals exist but no price data → insufficient."""
        signals = [_make_signal("005930", date(2026, 1, 10), "momentum", 1)]
        _setup_mock_db(mock_db, signals=signals, price_rows=[])

        result = compute_signal_accuracy(mock_db, "005930", "momentum")

        assert result.total_signals == 1
        assert result.evaluated_signals == 0
        assert result.insufficient_data is True

    def test_buy_success_rate(self, mock_db):
        """Buy signals with rising prices → high success rate."""
        # 10 buy signals, prices rising steadily
        signals = []
        price_rows = []
        for i in range(20):
            d = date(2026, 1, 1 + i)
            price_rows.append(_make_price_row(d, 100.0 + i * 2.0))  # rising
            if i < 10:  # 10 buy signals on first 10 days
                signals.append(_make_signal("005930", d, "momentum", 1))

        _setup_mock_db(mock_db, signals=signals, price_rows=price_rows)

        result = compute_signal_accuracy(
            mock_db, "005930", "momentum", forward_days=5
        )

        assert result.buy_count == 10
        assert result.buy_success_rate == 1.0  # all rising
        assert result.avg_return_after_buy is not None
        assert result.avg_return_after_buy > 0
        assert result.insufficient_data is False

    def test_sell_success_rate(self, mock_db):
        """Sell signals with falling prices → high success rate."""
        signals = []
        price_rows = []
        for i in range(20):
            d = date(2026, 1, 1 + i)
            price_rows.append(_make_price_row(d, 200.0 - i * 3.0))  # falling
            if i < 10:
                signals.append(_make_signal("005930", d, "momentum", -1))

        _setup_mock_db(mock_db, signals=signals, price_rows=price_rows)

        result = compute_signal_accuracy(
            mock_db, "005930", "momentum", forward_days=5
        )

        assert result.sell_count == 10
        assert result.sell_success_rate == 1.0  # price fell after sell
        assert result.avg_return_after_sell is not None
        assert result.avg_return_after_sell < 0
        assert result.insufficient_data is False

    def test_mixed_signals(self, mock_db):
        """Mix of buy/sell with varying outcomes."""
        # Alternating buy and sell, prices zigzag
        signals = []
        price_rows = []
        for i in range(20):
            d = date(2026, 1, 1 + i)
            # zigzag: up on even, down on odd
            close = 100.0 + (5.0 if i % 2 == 0 else -5.0) + i * 0.1
            price_rows.append(_make_price_row(d, close))
            if i < 10:
                sig = 1 if i % 2 == 0 else -1
                signals.append(_make_signal("005930", d, "momentum", sig))

        _setup_mock_db(mock_db, signals=signals, price_rows=price_rows)

        result = compute_signal_accuracy(
            mock_db, "005930", "momentum", forward_days=5
        )

        assert result.buy_count + result.sell_count <= 10
        assert result.evaluated_signals == result.buy_count + result.sell_count

    def test_insufficient_buy_count(self, mock_db):
        """Fewer than MIN_SIGNAL_COUNT buy signals → rate is None."""
        signals = []
        price_rows = []
        for i in range(20):
            d = date(2026, 1, 1 + i)
            price_rows.append(_make_price_row(d, 100.0 + i))
            if i < MIN_SIGNAL_COUNT - 1:  # just under threshold
                signals.append(_make_signal("005930", d, "momentum", 1))

        _setup_mock_db(mock_db, signals=signals, price_rows=price_rows)

        result = compute_signal_accuracy(
            mock_db, "005930", "momentum", forward_days=5
        )

        assert result.buy_success_rate is None
        assert result.insufficient_data is True

    def test_forward_days_beyond_data(self, mock_db):
        """Signals near end of price data → excluded from evaluation."""
        signals = [_make_signal("005930", date(2026, 1, 18), "momentum", 1)]
        price_rows = [
            _make_price_row(date(2026, 1, i), 100.0 + i) for i in range(1, 21)
        ]

        _setup_mock_db(mock_db, signals=signals, price_rows=price_rows)

        # forward_days=5 but signal on day 18 with only 20 days of data
        result = compute_signal_accuracy(
            mock_db, "005930", "momentum", forward_days=5
        )

        # day 18 → idx=17, fwd_idx=22 → out of bounds (20 rows)
        assert result.evaluated_signals == 0

    def test_include_details(self, mock_db):
        """include_details=True populates per-signal detail list."""
        signals = []
        price_rows = []
        for i in range(20):
            d = date(2026, 1, 1 + i)
            price_rows.append(_make_price_row(d, 100.0 + i * 2.0))
            if i < 6:
                signals.append(_make_signal("005930", d, "momentum", 1))

        _setup_mock_db(mock_db, signals=signals, price_rows=price_rows)

        result = compute_signal_accuracy(
            mock_db, "005930", "momentum", forward_days=5,
            include_details=True,
        )

        assert len(result.details) > 0
        for detail in result.details:
            assert detail.signal == 1
            assert detail.forward_return > 0  # prices rising
            assert detail.success

    def test_zero_entry_price_skipped(self, mock_db):
        """Entry price of 0 → that signal is skipped."""
        signals = [_make_signal("005930", date(2026, 1, 1), "momentum", 1)]
        price_rows = [
            _make_price_row(date(2026, 1, 1), 0.0),  # zero price
            _make_price_row(date(2026, 1, 2), 100.0),
            _make_price_row(date(2026, 1, 3), 100.0),
            _make_price_row(date(2026, 1, 4), 100.0),
            _make_price_row(date(2026, 1, 5), 100.0),
            _make_price_row(date(2026, 1, 6), 100.0),
        ]

        _setup_mock_db(mock_db, signals=signals, price_rows=price_rows)

        result = compute_signal_accuracy(
            mock_db, "005930", "momentum", forward_days=5
        )

        assert result.evaluated_signals == 0


class TestComputeAccuracyAllStrategies:
    def test_multiple_strategies(self, mock_db):
        """Compute accuracy for 3 strategies at once."""
        price_rows = [
            _make_price_row(date(2026, 1, 1 + i), 100.0 + i)
            for i in range(20)
        ]

        # Each strategy gets different signals
        def _query_side(model):
            from db.models import SignalDaily
            chain = MagicMock()
            if model is SignalDaily:
                signal_chain = MagicMock()
                signal_chain.filter.return_value = signal_chain
                signal_chain.order_by.return_value = signal_chain
                signal_chain.all.return_value = []  # no signals for simplicity
                chain.filter.return_value = signal_chain
            else:
                price_chain = MagicMock()
                price_chain.filter.return_value = price_chain
                price_chain.order_by.return_value = price_chain
                price_chain.all.return_value = price_rows
                chain.filter.return_value = price_chain
            return chain

        mock_db.query.side_effect = _query_side

        results = compute_accuracy_all_strategies(
            mock_db, "005930", ["momentum", "trend", "mean_reversion"]
        )

        assert len(results) == 3
        assert all(isinstance(r, SignalAccuracyResult) for r in results)
        assert results[0].strategy_id == "momentum"
        assert results[1].strategy_id == "trend"
        assert results[2].strategy_id == "mean_reversion"


# ---------------------------------------------------------------------------
# DR.2: compute_indicator_accuracy tests
# ---------------------------------------------------------------------------

class TestComputeIndicatorAccuracy:
    @patch("api.services.analysis.signal_accuracy_service.generate_indicator_signals")
    def test_no_signals_returns_insufficient(self, mock_gen, mock_db):
        """No indicator signals → insufficient_data=True."""
        mock_gen.return_value = []

        result = compute_indicator_accuracy(mock_db, "005930", "rsi_14")

        assert result.total_signals == 0
        assert result.insufficient_data is True
        assert result.strategy_id == "rsi_14"

    @patch("api.services.analysis.signal_accuracy_service.generate_indicator_signals")
    def test_warning_signals_excluded(self, mock_gen, mock_db):
        """ATR warning signals (signal=0) → filtered out, insufficient."""
        from api.services.analysis.indicator_signal_service import IndicatorSignal
        mock_gen.return_value = [
            IndicatorSignal(
                date=date(2026, 1, 5), indicator_id="atr_vol",
                signal=0, label="고변동성 경고", value=0.04, entry_price=100,
            ),
        ]

        result = compute_indicator_accuracy(mock_db, "005930", "atr_vol")

        assert result.total_signals == 0
        assert result.insufficient_data is True

    @patch("api.services.analysis.signal_accuracy_service.generate_indicator_signals")
    def test_buy_signals_with_rising_prices(self, mock_gen, mock_db):
        """Buy signals + rising prices → high success rate."""
        from api.services.analysis.indicator_signal_service import IndicatorSignal

        # 10 buy signals
        sigs = []
        for i in range(10):
            sigs.append(IndicatorSignal(
                date=date(2026, 1, 1 + i), indicator_id="rsi_14",
                signal=1, label="RSI 과매도 진입", value=28.0,
                entry_price=100.0 + i * 2.0,
            ))
        mock_gen.return_value = sigs

        # Mock price query — 20 days of rising prices
        price_rows = [
            (date(2026, 1, 1 + i), 100.0 + i * 2.0) for i in range(20)
        ]
        price_chain = MagicMock()
        price_chain.filter.return_value = price_chain
        price_chain.order_by.return_value = price_chain
        price_chain.all.return_value = price_rows
        mock_db.query.return_value = price_chain

        result = compute_indicator_accuracy(
            mock_db, "005930", "rsi_14", forward_days=5, include_details=True,
        )

        assert result.strategy_id == "rsi_14"
        assert result.buy_count == 10
        assert result.buy_success_rate == 1.0
        assert result.insufficient_data is False
        assert len(result.details) > 0

    @patch("api.services.analysis.signal_accuracy_service.generate_indicator_signals")
    def test_no_price_data(self, mock_gen, mock_db):
        """Signals exist but no price data → insufficient."""
        from api.services.analysis.indicator_signal_service import IndicatorSignal
        mock_gen.return_value = [
            IndicatorSignal(
                date=date(2026, 1, 5), indicator_id="macd",
                signal=1, label="MACD 골든크로스", value=0.5, entry_price=100,
            ),
        ]

        price_chain = MagicMock()
        price_chain.filter.return_value = price_chain
        price_chain.order_by.return_value = price_chain
        price_chain.all.return_value = []
        mock_db.query.return_value = price_chain

        result = compute_indicator_accuracy(mock_db, "005930", "macd")

        assert result.total_signals == 1
        assert result.evaluated_signals == 0
        assert result.insufficient_data is True

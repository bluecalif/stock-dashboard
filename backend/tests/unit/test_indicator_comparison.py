"""Tests for indicator_comparison — strategy ranking by prediction accuracy."""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from api.services.analysis.indicator_comparison import (
    DEFAULT_STRATEGY_IDS,
    IndicatorComparisonRow,
    compare_indicator_accuracy,
)
from api.services.analysis.signal_accuracy_service import SignalAccuracyResult


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


def _make_accuracy(
    strategy_id: str,
    *,
    buy_rate: float | None = None,
    sell_rate: float | None = None,
    avg_buy: float | None = None,
    avg_sell: float | None = None,
    evaluated: int = 10,
    insufficient: bool = False,
) -> SignalAccuracyResult:
    """Create a SignalAccuracyResult for testing."""
    return SignalAccuracyResult(
        asset_id="005930",
        strategy_id=strategy_id,
        forward_days=5,
        total_signals=evaluated,
        evaluated_signals=evaluated,
        buy_success_rate=buy_rate,
        sell_success_rate=sell_rate,
        avg_return_after_buy=avg_buy,
        avg_return_after_sell=avg_sell,
        insufficient_data=insufficient,
    )


class TestCompareIndicatorAccuracy:
    @patch("api.services.analysis.indicator_comparison.compute_accuracy_all_strategies")
    def test_ranks_by_success_rate(self, mock_compute, mock_db):
        """Strategies ranked by average success rate descending."""
        mock_compute.return_value = [
            _make_accuracy("momentum", buy_rate=0.6, sell_rate=0.5),
            _make_accuracy("trend", buy_rate=0.8, sell_rate=0.7),
            _make_accuracy("mean_reversion", buy_rate=0.4, sell_rate=0.3),
        ]

        rows = compare_indicator_accuracy(mock_db, "005930")

        assert len(rows) == 3
        assert rows[0].strategy_id == "trend"
        assert rows[0].rank == 1
        assert rows[1].strategy_id == "momentum"
        assert rows[1].rank == 2
        assert rows[2].strategy_id == "mean_reversion"
        assert rows[2].rank == 3

    @patch("api.services.analysis.indicator_comparison.compute_accuracy_all_strategies")
    def test_insufficient_data_ranks_last(self, mock_compute, mock_db):
        """Strategies with insufficient data rank below those with data."""
        mock_compute.return_value = [
            _make_accuracy("momentum", buy_rate=0.5, sell_rate=0.5),
            _make_accuracy("trend", insufficient=True, evaluated=2),
            _make_accuracy("mean_reversion", buy_rate=0.7, sell_rate=0.6),
        ]

        rows = compare_indicator_accuracy(mock_db, "005930")

        assert rows[0].strategy_id == "mean_reversion"
        assert rows[0].rank == 1
        assert rows[1].strategy_id == "momentum"
        assert rows[1].rank == 2
        assert rows[2].strategy_id == "trend"
        assert rows[2].rank == 3
        assert rows[2].insufficient_data is True

    @patch("api.services.analysis.indicator_comparison.compute_accuracy_all_strategies")
    def test_all_insufficient(self, mock_compute, mock_db):
        """All strategies insufficient → still returns ranked list."""
        mock_compute.return_value = [
            _make_accuracy("momentum", insufficient=True, evaluated=0),
            _make_accuracy("trend", insufficient=True, evaluated=0),
            _make_accuracy("mean_reversion", insufficient=True, evaluated=0),
        ]

        rows = compare_indicator_accuracy(mock_db, "005930")

        assert len(rows) == 3
        assert all(r.insufficient_data for r in rows)
        assert [r.rank for r in rows] == [1, 2, 3]

    @patch("api.services.analysis.indicator_comparison.compute_accuracy_all_strategies")
    def test_partial_rates(self, mock_compute, mock_db):
        """Strategy with only buy_rate vs one with only sell_rate."""
        mock_compute.return_value = [
            _make_accuracy("momentum", buy_rate=0.6),     # avg = 0.6
            _make_accuracy("trend", sell_rate=0.8),        # avg = 0.8
            _make_accuracy("mean_reversion", buy_rate=0.5, sell_rate=0.5),  # avg = 0.5
        ]

        rows = compare_indicator_accuracy(mock_db, "005930")

        assert rows[0].strategy_id == "trend"
        assert rows[0].buy_success_rate is None
        assert rows[0].sell_success_rate == 0.8
        assert rows[1].strategy_id == "momentum"
        assert rows[2].strategy_id == "mean_reversion"

    @patch("api.services.analysis.indicator_comparison.compute_accuracy_all_strategies")
    def test_custom_strategy_ids(self, mock_compute, mock_db):
        """Custom strategy_ids passed through correctly."""
        mock_compute.return_value = [
            _make_accuracy("momentum", buy_rate=0.5),
            _make_accuracy("trend", buy_rate=0.6),
        ]

        rows = compare_indicator_accuracy(
            mock_db, "005930", ["momentum", "trend"]
        )

        mock_compute.assert_called_once_with(
            mock_db, "005930", ["momentum", "trend"], forward_days=5,
        )
        assert len(rows) == 2

    @patch("api.services.analysis.indicator_comparison.compute_accuracy_all_strategies")
    def test_custom_forward_days(self, mock_compute, mock_db):
        """Custom forward_days passed to compute_accuracy_all_strategies."""
        mock_compute.return_value = [
            _make_accuracy("momentum", buy_rate=0.5),
        ]

        compare_indicator_accuracy(
            mock_db, "005930", ["momentum"], forward_days=10,
        )

        mock_compute.assert_called_once_with(
            mock_db, "005930", ["momentum"], forward_days=10,
        )

    @patch("api.services.analysis.indicator_comparison.compute_accuracy_all_strategies")
    def test_default_strategy_ids(self, mock_compute, mock_db):
        """None strategy_ids → uses DEFAULT_STRATEGY_IDS."""
        mock_compute.return_value = [
            _make_accuracy(sid) for sid in DEFAULT_STRATEGY_IDS
        ]

        compare_indicator_accuracy(mock_db, "005930")

        mock_compute.assert_called_once_with(
            mock_db, "005930", DEFAULT_STRATEGY_IDS, forward_days=5,
        )

    @patch("api.services.analysis.indicator_comparison.compute_accuracy_all_strategies")
    def test_result_fields_populated(self, mock_compute, mock_db):
        """IndicatorComparisonRow fields populated from SignalAccuracyResult."""
        mock_compute.return_value = [
            _make_accuracy(
                "momentum",
                buy_rate=0.65,
                sell_rate=0.55,
                avg_buy=0.012,
                avg_sell=-0.008,
                evaluated=20,
            ),
        ]

        rows = compare_indicator_accuracy(mock_db, "005930", ["momentum"])

        row = rows[0]
        assert isinstance(row, IndicatorComparisonRow)
        assert row.strategy_id == "momentum"
        assert row.rank == 1
        assert row.buy_success_rate == 0.65
        assert row.sell_success_rate == 0.55
        assert row.avg_return_after_buy == 0.012
        assert row.avg_return_after_sell == -0.008
        assert row.evaluated_signals == 20
        assert row.insufficient_data is False

    @patch("api.services.analysis.indicator_comparison.compute_accuracy_all_strategies")
    def test_tie_preserves_input_order(self, mock_compute, mock_db):
        """Equal success rates → original order preserved (stable sort)."""
        mock_compute.return_value = [
            _make_accuracy("momentum", buy_rate=0.5, sell_rate=0.5),
            _make_accuracy("trend", buy_rate=0.5, sell_rate=0.5),
        ]

        rows = compare_indicator_accuracy(
            mock_db, "005930", ["momentum", "trend"]
        )

        assert rows[0].strategy_id == "momentum"
        assert rows[1].strategy_id == "trend"

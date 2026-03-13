"""Tests for spread_service — normalized price ratio spread + z-score."""

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from api.services.analysis.spread_service import compute_spread

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_prices(asset_id: str, base: float, n: int = 20, trend: float = 0.01):
    """Generate n mock price records with incrementing dates and close."""
    prices = []
    for i in range(n):
        m = MagicMock()
        m.asset_id = asset_id
        m.date = date(2026, 1, 1 + i)
        m.close = base * (1 + trend * i)
        prices.append(m)
    # Return DESC order (like price_repo)
    return list(reversed(prices))


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestComputeSpread:
    @patch("api.services.analysis.spread_service.price_repo")
    def test_basic_spread(self, mock_price, mock_db):
        """Two assets with same trend → spread ≈ 1.0, z-scores ≈ 0."""
        def _side(db, aid, **kw):
            if aid == "A":
                return _make_prices("A", 100.0, 20, trend=0.01)
            return _make_prices("B", 50.0, 20, trend=0.01)

        mock_price.get_prices.side_effect = _side

        result = compute_spread(mock_db, "A", "B")
        assert result.asset_a == "A"
        assert result.asset_b == "B"
        assert len(result.dates) == 20
        assert len(result.spread_values) == 20
        assert len(result.z_scores) == 20
        # Same trend → spread should be close to 1.0
        for v in result.spread_values:
            assert 0.9 < v < 1.1

    @patch("api.services.analysis.spread_service.price_repo")
    def test_diverging_assets(self, mock_price, mock_db):
        """Assets diverging → spread deviates from 1.0."""
        def _side(db, aid, **kw):
            if aid == "A":
                return _make_prices("A", 100.0, 30, trend=0.05)  # strong up
            return _make_prices("B", 100.0, 30, trend=-0.01)  # slight down

        mock_price.get_prices.side_effect = _side

        result = compute_spread(mock_db, "A", "B")
        # Last spread should be > 1 (A grew more)
        assert result.spread_values[-1] > 1.0
        assert result.std > 0

    @patch("api.services.analysis.spread_service.price_repo")
    def test_z_scores_normalized(self, mock_price, mock_db):
        """Z-scores should have mean ≈ 0."""
        def _side(db, aid, **kw):
            if aid == "A":
                return _make_prices("A", 100.0, 30, trend=0.02)
            return _make_prices("B", 200.0, 30, trend=0.01)

        mock_price.get_prices.side_effect = _side

        result = compute_spread(mock_db, "A", "B")
        avg_z = sum(result.z_scores) / len(result.z_scores)
        assert abs(avg_z) < 0.5  # z-scores centered near 0

    @patch("api.services.analysis.spread_service.price_repo")
    def test_convergence_events_detected(self, mock_price, mock_db):
        """Strong divergence should trigger events."""
        # Create asset B with a spike in the middle
        prices_a = []
        prices_b = []
        for i in range(30):
            ma = MagicMock()
            ma.asset_id = "A"
            ma.date = date(2026, 1, 1 + i)
            ma.close = 100.0 + i * 0.5
            prices_a.append(ma)

            mb = MagicMock()
            mb.asset_id = "B"
            mb.date = date(2026, 1, 1 + i)
            # B has a big spike at i=15
            if 14 <= i <= 16:
                mb.close = 100.0 + i * 0.5 + 50.0
            else:
                mb.close = 100.0 + i * 0.5
            prices_b.append(mb)

        def _side(db, aid, **kw):
            if aid == "A":
                return list(reversed(prices_a))
            return list(reversed(prices_b))

        mock_price.get_prices.side_effect = _side

        result = compute_spread(mock_db, "A", "B", z_threshold=1.5)
        # Should detect at least some events due to the spike
        assert len(result.convergence_events) >= 1

    @patch("api.services.analysis.spread_service.price_repo")
    def test_empty_data_raises(self, mock_price, mock_db):
        """No data → ValueError."""
        mock_price.get_prices.return_value = []

        with pytest.raises(ValueError, match="Insufficient price data"):
            compute_spread(mock_db, "A", "B")

    @patch("api.services.analysis.spread_service.price_repo")
    def test_insufficient_overlap_raises(self, mock_price, mock_db):
        """Non-overlapping dates → ValueError."""
        def _side(db, aid, **kw):
            if aid == "A":
                return _make_prices("A", 100.0, 3, trend=0.01)
            # B starts after A ends
            prices = []
            for i in range(3):
                m = MagicMock()
                m.asset_id = "B"
                m.date = date(2026, 2, 1 + i)
                m.close = 100.0
                prices.append(m)
            return list(reversed(prices))

        mock_price.get_prices.side_effect = _side

        with pytest.raises(ValueError, match="Insufficient overlapping"):
            compute_spread(mock_db, "A", "B")

    @patch("api.services.analysis.spread_service.price_repo")
    def test_date_params_passed(self, mock_price, mock_db):
        """start_date and end_date are passed to price_repo."""
        def _side(db, aid, **kw):
            return _make_prices(aid, 100.0, 10)

        mock_price.get_prices.side_effect = _side

        start = date(2026, 1, 1)
        end = date(2026, 1, 31)
        compute_spread(mock_db, "A", "B", start_date=start, end_date=end)

        calls = mock_price.get_prices.call_args_list
        for call in calls:
            assert call.kwargs["start_date"] == start
            assert call.kwargs["end_date"] == end

    @patch("api.services.analysis.spread_service.price_repo")
    def test_current_z_score(self, mock_price, mock_db):
        """current_z_score is the last z-score."""
        def _side(db, aid, **kw):
            return _make_prices(aid, 100.0, 15, trend=0.01)

        mock_price.get_prices.side_effect = _side

        result = compute_spread(mock_db, "A", "B")
        assert result.current_z_score == result.z_scores[-1]

    @patch("api.services.analysis.spread_service.price_repo")
    def test_event_directions(self, mock_price, mock_db):
        """Convergence events have valid direction values."""
        def _side(db, aid, **kw):
            if aid == "A":
                return _make_prices("A", 100.0, 30, trend=0.05)
            return _make_prices("B", 100.0, 30, trend=-0.02)

        mock_price.get_prices.side_effect = _side

        result = compute_spread(mock_db, "A", "B", z_threshold=1.0)
        for event in result.convergence_events:
            assert event.direction in ("convergence", "divergence")

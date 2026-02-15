"""Edge-case tests for all API routers — Step 4.14 Part 1.

Covers:
- DB error → 500 responses (per router)
- Pagination boundary values (limit/offset validation)
- Date range validation (start_date > end_date → 400)
- Correlation-specific edge cases
- Backtest UUID edge cases
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture
def client(mock_db):
    from api.dependencies import get_db

    def _override():
        yield mock_db

    app.dependency_overrides[get_db] = _override
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


# ── DB Error → 500 ──


class TestDBErrors:
    """Each router should return 500 when DB/service raises unexpected error."""

    def test_health_db_error(self, mock_db, client):
        """Health check returns 503 on DB failure."""
        mock_db.execute.side_effect = Exception("DB down")
        resp = client.get("/v1/health")
        assert resp.status_code == 503
        assert resp.json()["db"] == "disconnected"

    @patch("api.routers.assets.asset_repo")
    def test_assets_db_error(self, mock_repo, client):
        """GET /v1/assets → 500 on unhandled DB error."""
        mock_repo.get_all.side_effect = Exception("DB connection lost")
        resp = client.get("/v1/assets")
        assert resp.status_code == 500

    @patch("api.routers.prices.price_repo")
    def test_prices_db_error(self, mock_repo, client):
        """GET /v1/prices/daily → 500 on unhandled DB error."""
        mock_repo.get_prices.side_effect = Exception("DB timeout")
        resp = client.get("/v1/prices/daily?asset_id=005930")
        assert resp.status_code == 500

    @patch("api.routers.factors.factor_repo")
    def test_factors_db_error(self, mock_repo, client):
        """GET /v1/factors → 500 on unhandled DB error."""
        mock_repo.get_factors.side_effect = Exception("DB error")
        resp = client.get("/v1/factors")
        assert resp.status_code == 500

    @patch("api.routers.signals.signal_repo")
    def test_signals_db_error(self, mock_repo, client):
        """GET /v1/signals → 500 on unhandled DB error."""
        mock_repo.get_signals.side_effect = Exception("DB error")
        resp = client.get("/v1/signals")
        assert resp.status_code == 500

    @patch("api.routers.backtests.backtest_repo")
    def test_backtests_list_db_error(self, mock_repo, client):
        """GET /v1/backtests → 500 on unhandled DB error."""
        mock_repo.get_runs.side_effect = Exception("DB error")
        resp = client.get("/v1/backtests")
        assert resp.status_code == 500

    @patch("api.routers.backtests.backtest_repo")
    def test_backtests_get_db_error(self, mock_repo, client):
        """GET /v1/backtests/{id} → 500 on unhandled DB error."""
        mock_repo.get_run_by_id.side_effect = Exception("DB error")
        resp = client.get(f"/v1/backtests/{uuid4()}")
        assert resp.status_code == 500

    @patch("api.services.dashboard_service.asset_repo")
    def test_dashboard_db_error(self, mock_repo, client):
        """GET /v1/dashboard/summary → 500 on unhandled DB error."""
        mock_repo.get_all.side_effect = Exception("DB error")
        resp = client.get("/v1/dashboard/summary")
        assert resp.status_code == 500

    @patch("api.services.correlation_service.asset_repo")
    def test_correlation_db_error(self, mock_repo, client):
        """GET /v1/correlation → 500 on unhandled DB error."""
        mock_repo.get_all.side_effect = Exception("DB error")
        resp = client.get("/v1/correlation")
        assert resp.status_code == 500


# ── Pagination Boundary Values ──


class TestPaginationBoundary:
    """Pagination validation: limit/offset constraints (ge=1/ge=0, le=5000)."""

    def test_limit_zero(self, client):
        """limit=0 → 422 (minimum is 1)."""
        resp = client.get("/v1/prices/daily?asset_id=005930&limit=0")
        assert resp.status_code == 422

    def test_limit_negative(self, client):
        """limit=-1 → 422."""
        resp = client.get("/v1/prices/daily?asset_id=005930&limit=-1")
        assert resp.status_code == 422

    def test_offset_negative(self, client):
        """offset=-1 → 422."""
        resp = client.get("/v1/prices/daily?asset_id=005930&offset=-1")
        assert resp.status_code == 422

    def test_limit_exceeds_max(self, client):
        """limit=5001 → 422 (max 5000)."""
        resp = client.get("/v1/prices/daily?asset_id=005930&limit=5001")
        assert resp.status_code == 422

    @patch("api.routers.prices.price_repo")
    def test_limit_at_max(self, mock_repo, client):
        """limit=5000 → 200 (boundary ok)."""
        mock_repo.get_prices.return_value = []
        resp = client.get("/v1/prices/daily?asset_id=005930&limit=5000")
        assert resp.status_code == 200

    @patch("api.routers.prices.price_repo")
    def test_limit_at_min(self, mock_repo, client):
        """limit=1 → 200 (boundary ok)."""
        mock_repo.get_prices.return_value = []
        resp = client.get("/v1/prices/daily?asset_id=005930&limit=1")
        assert resp.status_code == 200

    def test_factors_limit_zero(self, client):
        """Pagination validation also applies to /v1/factors."""
        resp = client.get("/v1/factors?limit=0")
        assert resp.status_code == 422

    def test_signals_limit_exceeds(self, client):
        """Pagination validation also applies to /v1/signals."""
        resp = client.get("/v1/signals?limit=5001")
        assert resp.status_code == 422

    def test_backtests_offset_negative(self, client):
        """Pagination validation also applies to /v1/backtests."""
        resp = client.get("/v1/backtests?offset=-1")
        assert resp.status_code == 422


# ── Date Validation ──


class TestDateValidation:
    """start_date > end_date → 400 for factors, signals; prices already tested."""

    def test_factors_date_range_invalid(self, client):
        """GET /v1/factors start_date > end_date → 400."""
        resp = client.get("/v1/factors?start_date=2026-03-01&end_date=2026-01-01")
        assert resp.status_code == 400
        assert "start_date" in resp.json()["detail"]

    def test_signals_date_range_invalid(self, client):
        """GET /v1/signals start_date > end_date → 400."""
        resp = client.get("/v1/signals?start_date=2026-12-31&end_date=2026-01-01")
        assert resp.status_code == 400
        assert "start_date" in resp.json()["detail"]

    @patch("api.services.correlation_service.asset_repo")
    @patch("api.services.correlation_service.price_repo")
    def test_correlation_date_range_pass_through(
        self, mock_price, mock_asset, client
    ):
        """Correlation does not validate date order — passes to service."""
        # When start_date > end_date, no price data → 400 from service
        mock_asset.get_all.return_value = [
            MagicMock(asset_id="KS200", is_active=True),
            MagicMock(asset_id="BTC", is_active=True),
        ]
        mock_price.get_prices.return_value = []
        resp = client.get("/v1/correlation?start_date=2026-12-01&end_date=2026-01-01")
        # Either 400 (no data) or 200 (empty). Just make sure no crash.
        assert resp.status_code in (200, 400)


# ── Correlation-Specific Edge Cases ──


class TestCorrelationEdge:
    """Correlation parameter edge cases."""

    def test_window_below_min(self, client):
        """window < 5 → 422."""
        resp = client.get("/v1/correlation?window=4")
        assert resp.status_code == 422

    def test_window_above_max(self, client):
        """window > 500 → 422."""
        resp = client.get("/v1/correlation?window=501")
        assert resp.status_code == 422

    @patch("api.services.correlation_service.price_repo")
    @patch("api.services.correlation_service.asset_repo")
    def test_window_at_min(self, mock_asset, mock_price, client):
        """window=5 → 200 (boundary ok)."""
        mock_asset.get_all.return_value = [
            MagicMock(asset_id="KS200", is_active=True),
            MagicMock(asset_id="BTC", is_active=True),
        ]

        def _prices(db, aid, **kw):
            prices = []
            for i in range(10):
                m = MagicMock()
                m.asset_id = aid
                from datetime import date

                m.date = date(2026, 1, 10 - i)
                m.close = 100.0 + i
                prices.append(m)
            return prices

        mock_price.get_prices.side_effect = _prices
        resp = client.get("/v1/correlation?window=5")
        assert resp.status_code == 200

    @patch("api.services.correlation_service.price_repo")
    @patch("api.services.correlation_service.asset_repo")
    def test_window_at_max(self, mock_asset, mock_price, client):
        """window=500 → accepted (200 or 400 if insufficient data)."""
        mock_asset.get_all.return_value = [
            MagicMock(asset_id="KS200", is_active=True),
            MagicMock(asset_id="BTC", is_active=True),
        ]
        mock_price.get_prices.return_value = []
        resp = client.get("/v1/correlation?window=500")
        # May be 400 (insufficient data) but not 422 (validation error)
        assert resp.status_code != 422

    def test_empty_asset_ids(self, client):
        """asset_ids= (empty string) is treated as no filter."""
        # With empty string, split produces empty list → falls back to all active
        # This should not crash (either 200, 400, or 500 depending on DB mock)
        resp = client.get("/v1/correlation?asset_ids=")
        # Just ensure it doesn't return 422 (not a validation error)
        assert resp.status_code != 422

    @patch("api.services.correlation_service.asset_repo")
    def test_single_asset_id(self, mock_asset, client):
        """Single asset_id → 400 (need at least 2)."""
        resp = client.get("/v1/correlation?asset_ids=KS200")
        assert resp.status_code == 400


# ── Backtest UUID Edge Cases ──


class TestBacktestUUIDEdge:
    """Invalid UUID formats for backtest endpoints."""

    def test_invalid_uuid_get(self, client):
        """GET /v1/backtests/not-a-uuid → 422."""
        resp = client.get("/v1/backtests/not-a-uuid")
        assert resp.status_code == 422

    def test_invalid_uuid_equity(self, client):
        """GET /v1/backtests/xxx/equity → 422."""
        resp = client.get("/v1/backtests/invalid-uuid/equity")
        assert resp.status_code == 422

    def test_invalid_uuid_trades(self, client):
        """GET /v1/backtests/abc123/trades → 422."""
        resp = client.get("/v1/backtests/abc123/trades")
        assert resp.status_code == 422

    @patch("api.routers.backtests.backtest_repo")
    def test_valid_uuid_not_found(self, mock_repo, client):
        """Valid UUID but not in DB → 404."""
        mock_repo.get_run_by_id.return_value = None
        resp = client.get(f"/v1/backtests/{uuid4()}")
        assert resp.status_code == 404

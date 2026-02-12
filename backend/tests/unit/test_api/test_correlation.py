"""Tests for correlation endpoint."""

from datetime import date
from unittest.mock import MagicMock, patch

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


def _make_asset(asset_id: str):
    m = MagicMock()
    m.asset_id = asset_id
    m.is_active = True
    return m


def _make_prices(asset_id: str, base: float, n: int = 10):
    """Generate n mock price records with incrementing dates and varying close."""
    prices = []
    for i in range(n):
        m = MagicMock()
        m.asset_id = asset_id
        m.date = date(2026, 1, n - i)  # DESC order (newest first)
        m.close = base + i * 0.5
        prices.append(m)
    return prices


class TestCorrelation:
    """GET /v1/correlation tests."""

    @patch("api.services.correlation_service.price_repo")
    @patch("api.services.correlation_service.asset_repo")
    def test_correlation_basic(self, mock_asset, mock_price, client):
        """Returns NxN matrix for 2 assets."""
        mock_asset.get_all.return_value = [
            _make_asset("KS200"),
            _make_asset("005930"),
        ]

        def _price_side_effect(db, aid, **kwargs):
            if aid == "KS200":
                return _make_prices("KS200", 300.0, 10)
            return _make_prices("005930", 70000.0, 10)

        mock_price.get_prices.side_effect = _price_side_effect

        resp = client.get("/v1/correlation")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["asset_ids"]) == 2
        assert len(data["matrix"]) == 2
        assert len(data["matrix"][0]) == 2
        # Diagonal should be 1.0
        assert data["matrix"][0][0] == pytest.approx(1.0, abs=0.01)
        assert data["matrix"][1][1] == pytest.approx(1.0, abs=0.01)

    @patch("api.services.correlation_service.price_repo")
    @patch("api.services.correlation_service.asset_repo")
    def test_correlation_specific_assets(self, mock_asset, mock_price, client):
        """asset_ids query param filters assets."""
        def _price_side_effect(db, aid, **kwargs):
            return _make_prices(aid, 100.0, 10)

        mock_price.get_prices.side_effect = _price_side_effect

        resp = client.get("/v1/correlation?asset_ids=KS200,BTC")
        assert resp.status_code == 200
        data = resp.json()
        assert set(data["asset_ids"]) == {"KS200", "BTC"}
        # asset_repo.get_all should NOT be called when asset_ids specified
        mock_asset.get_all.assert_not_called()

    @patch("api.services.correlation_service.price_repo")
    @patch("api.services.correlation_service.asset_repo")
    def test_correlation_insufficient_assets(self, mock_asset, mock_price, client):
        """Single asset → 400."""
        mock_asset.get_all.return_value = [_make_asset("KS200")]

        resp = client.get("/v1/correlation")
        assert resp.status_code == 400
        assert "2 assets" in resp.json()["detail"]

    @patch("api.services.correlation_service.price_repo")
    @patch("api.services.correlation_service.asset_repo")
    def test_correlation_no_price_data(self, mock_asset, mock_price, client):
        """No price data → 400."""
        mock_asset.get_all.return_value = [
            _make_asset("KS200"),
            _make_asset("005930"),
        ]
        mock_price.get_prices.return_value = []

        resp = client.get("/v1/correlation")
        assert resp.status_code == 400

    @patch("api.services.correlation_service.price_repo")
    @patch("api.services.correlation_service.asset_repo")
    def test_correlation_window_param(self, mock_asset, mock_price, client):
        """Custom window parameter."""
        mock_asset.get_all.return_value = [
            _make_asset("KS200"),
            _make_asset("BTC"),
        ]

        def _price_side_effect(db, aid, **kwargs):
            return _make_prices(aid, 100.0, 20)

        mock_price.get_prices.side_effect = _price_side_effect

        resp = client.get("/v1/correlation?window=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["period"]["window"] <= 10

    @patch("api.services.correlation_service.price_repo")
    @patch("api.services.correlation_service.asset_repo")
    def test_correlation_date_filter(self, mock_asset, mock_price, client):
        """Date params are passed through."""
        mock_asset.get_all.return_value = [
            _make_asset("KS200"),
            _make_asset("005930"),
        ]

        def _price_side_effect(db, aid, **kwargs):
            return _make_prices(aid, 100.0, 10)

        mock_price.get_prices.side_effect = _price_side_effect

        resp = client.get("/v1/correlation?start_date=2026-01-01&end_date=2026-02-01")
        assert resp.status_code == 200

    def test_correlation_invalid_window(self, client):
        """Window below min → 422."""
        resp = client.get("/v1/correlation?window=2")
        assert resp.status_code == 422

    @patch("api.services.correlation_service.price_repo")
    @patch("api.services.correlation_service.asset_repo")
    def test_correlation_response_schema(self, mock_asset, mock_price, client):
        """Response matches CorrelationResponse schema."""
        mock_asset.get_all.return_value = [
            _make_asset("KS200"),
            _make_asset("BTC"),
        ]

        def _price_side_effect(db, aid, **kwargs):
            return _make_prices(aid, 100.0, 10)

        mock_price.get_prices.side_effect = _price_side_effect

        resp = client.get("/v1/correlation")
        data = resp.json()
        assert {"asset_ids", "matrix", "period"} <= set(data.keys())
        assert {"start", "end", "window"} <= set(data["period"].keys())

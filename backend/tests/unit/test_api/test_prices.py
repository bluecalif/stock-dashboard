"""Tests for GET /v1/prices/daily endpoint."""

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


def _make_price(asset_id: str, date_str: str, close: float = 100.0):
    m = MagicMock()
    m.asset_id = asset_id
    m.date = date_str
    m.open = close * 0.99
    m.high = close * 1.01
    m.low = close * 0.98
    m.close = close
    m.volume = 1000
    m.source = "fdr"
    return m


SAMPLE_PRICES = [
    _make_price("005930", "2026-01-03", 72000),
    _make_price("005930", "2026-01-02", 71500),
    _make_price("005930", "2026-01-01", 71000),
]


class TestListPrices:
    @patch("api.routers.prices.price_repo")
    def test_requires_asset_id(self, mock_repo, client):
        """asset_id is required — 422 without it."""
        response = client.get("/v1/prices/daily")
        assert response.status_code == 422

    @patch("api.routers.prices.price_repo")
    def test_returns_prices(self, mock_repo, client):
        """Returns prices for given asset_id."""
        mock_repo.get_prices.return_value = SAMPLE_PRICES
        response = client.get("/v1/prices/daily?asset_id=005930")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["asset_id"] == "005930"
        assert data[0]["close"] == 72000

    @patch("api.routers.prices.price_repo")
    def test_date_filter(self, mock_repo, client):
        """Date filters are passed to repo."""
        mock_repo.get_prices.return_value = [SAMPLE_PRICES[0]]
        response = client.get(
            "/v1/prices/daily?asset_id=005930&start_date=2026-01-03&end_date=2026-01-03"
        )
        assert response.status_code == 200
        _, kwargs = mock_repo.get_prices.call_args
        assert kwargs["start_date"] is not None
        assert kwargs["end_date"] is not None

    @patch("api.routers.prices.price_repo")
    def test_invalid_date_range(self, mock_repo, client):
        """start_date > end_date returns 400."""
        response = client.get(
            "/v1/prices/daily?asset_id=005930&start_date=2026-02-01&end_date=2026-01-01"
        )
        assert response.status_code == 400
        assert "start_date" in response.json()["detail"]

    @patch("api.routers.prices.price_repo")
    def test_pagination(self, mock_repo, client):
        """Pagination params are passed to repo."""
        mock_repo.get_prices.return_value = []
        response = client.get("/v1/prices/daily?asset_id=005930&limit=10&offset=5")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_prices.call_args
        assert kwargs["limit"] == 10
        assert kwargs["offset"] == 5

    @patch("api.routers.prices.price_repo")
    def test_empty_result(self, mock_repo, client):
        """Returns empty list when no prices found."""
        mock_repo.get_prices.return_value = []
        response = client.get("/v1/prices/daily?asset_id=NOTEXIST")
        assert response.status_code == 200
        assert response.json() == []

    @patch("api.routers.prices.price_repo")
    def test_response_schema(self, mock_repo, client):
        """Response matches PriceDailyResponse schema."""
        mock_repo.get_prices.return_value = [SAMPLE_PRICES[0]]
        response = client.get("/v1/prices/daily?asset_id=005930")
        data = response.json()[0]
        expected_keys = {"asset_id", "date", "open", "high", "low", "close", "volume", "source"}
        assert set(data.keys()) == expected_keys

    @patch("api.routers.prices.price_repo")
    def test_pagination_validation(self, mock_repo, client):
        """limit > 5000 returns 422."""
        response = client.get("/v1/prices/daily?asset_id=005930&limit=9999")
        assert response.status_code == 422

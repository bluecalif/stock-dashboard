"""Tests for GET /v1/factors endpoint."""

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


def _make_factor(asset_id: str, date_str: str, factor_name: str, value: float):
    m = MagicMock()
    m.asset_id = asset_id
    m.date = date_str
    m.factor_name = factor_name
    m.version = "v1"
    m.value = value
    return m


SAMPLE_FACTORS = [
    _make_factor("005930", "2026-01-03", "momentum_20d", 0.05),
    _make_factor("005930", "2026-01-02", "momentum_20d", 0.03),
    _make_factor("005930", "2026-01-03", "volatility_20d", 0.15),
]


class TestListFactors:
    @patch("api.routers.factors.factor_repo")
    def test_returns_all(self, mock_repo, client):
        """Returns factors without filters."""
        mock_repo.get_factors.return_value = SAMPLE_FACTORS
        response = client.get("/v1/factors")
        assert response.status_code == 200
        assert len(response.json()) == 3

    @patch("api.routers.factors.factor_repo")
    def test_filter_by_asset(self, mock_repo, client):
        """asset_id filter is passed to repo."""
        mock_repo.get_factors.return_value = SAMPLE_FACTORS[:2]
        response = client.get("/v1/factors?asset_id=005930")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_factors.call_args
        assert kwargs["asset_id"] == "005930"

    @patch("api.routers.factors.factor_repo")
    def test_filter_by_factor_name(self, mock_repo, client):
        """factor_name filter is passed to repo."""
        mock_repo.get_factors.return_value = [SAMPLE_FACTORS[2]]
        response = client.get("/v1/factors?factor_name=volatility_20d")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_factors.call_args
        assert kwargs["factor_name"] == "volatility_20d"

    @patch("api.routers.factors.factor_repo")
    def test_date_filter(self, mock_repo, client):
        """Date filters are passed to repo."""
        mock_repo.get_factors.return_value = []
        response = client.get("/v1/factors?start_date=2026-01-01&end_date=2026-01-03")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_factors.call_args
        assert kwargs["start_date"] is not None
        assert kwargs["end_date"] is not None

    @patch("api.routers.factors.factor_repo")
    def test_invalid_date_range(self, mock_repo, client):
        """start_date > end_date returns 400."""
        response = client.get("/v1/factors?start_date=2026-02-01&end_date=2026-01-01")
        assert response.status_code == 400

    @patch("api.routers.factors.factor_repo")
    def test_pagination(self, mock_repo, client):
        """Pagination params are passed to repo."""
        mock_repo.get_factors.return_value = []
        response = client.get("/v1/factors?limit=100&offset=20")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_factors.call_args
        assert kwargs["limit"] == 100
        assert kwargs["offset"] == 20

    @patch("api.routers.factors.factor_repo")
    def test_empty_result(self, mock_repo, client):
        """Returns empty list when no factors."""
        mock_repo.get_factors.return_value = []
        response = client.get("/v1/factors")
        assert response.status_code == 200
        assert response.json() == []

    @patch("api.routers.factors.factor_repo")
    def test_response_schema(self, mock_repo, client):
        """Response matches FactorDailyResponse schema."""
        mock_repo.get_factors.return_value = [SAMPLE_FACTORS[0]]
        response = client.get("/v1/factors")
        data = response.json()[0]
        expected_keys = {"asset_id", "date", "factor_name", "version", "value"}
        assert set(data.keys()) == expected_keys

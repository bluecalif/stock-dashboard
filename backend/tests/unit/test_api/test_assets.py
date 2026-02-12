"""Tests for GET /v1/assets endpoint."""

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


def _make_asset(asset_id: str, name: str, category: str, is_active: bool = True):
    """Create a mock asset object with from_attributes support."""
    m = MagicMock()
    m.asset_id = asset_id
    m.name = name
    m.category = category
    m.is_active = is_active
    return m


SAMPLE_ASSETS = [
    _make_asset("005930", "삼성전자", "stock"),
    _make_asset("KS200", "KOSPI200", "index"),
    _make_asset("SOXL", "SOXL ETF", "etf", is_active=False),
]


class TestListAssets:
    @patch("api.routers.assets.asset_repo")
    def test_returns_all(self, mock_repo, client):
        """GET /v1/assets returns all assets."""
        mock_repo.get_all.return_value = SAMPLE_ASSETS
        response = client.get("/v1/assets")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["asset_id"] == "005930"
        assert data[0]["name"] == "삼성전자"
        mock_repo.get_all.assert_called_once()

    @patch("api.routers.assets.asset_repo")
    def test_filter_active(self, mock_repo, client):
        """GET /v1/assets?is_active=true filters active assets."""
        active_only = [a for a in SAMPLE_ASSETS if a.is_active]
        mock_repo.get_all.return_value = active_only
        response = client.get("/v1/assets?is_active=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(a["is_active"] for a in data)
        _, kwargs = mock_repo.get_all.call_args
        assert kwargs["is_active"] is True

    @patch("api.routers.assets.asset_repo")
    def test_filter_inactive(self, mock_repo, client):
        """GET /v1/assets?is_active=false filters inactive assets."""
        inactive_only = [a for a in SAMPLE_ASSETS if not a.is_active]
        mock_repo.get_all.return_value = inactive_only
        response = client.get("/v1/assets?is_active=false")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["asset_id"] == "SOXL"

    @patch("api.routers.assets.asset_repo")
    def test_empty_result(self, mock_repo, client):
        """GET /v1/assets returns empty list when no assets."""
        mock_repo.get_all.return_value = []
        response = client.get("/v1/assets")
        assert response.status_code == 200
        assert response.json() == []

    @patch("api.routers.assets.asset_repo")
    def test_response_schema(self, mock_repo, client):
        """Response matches AssetResponse schema."""
        mock_repo.get_all.return_value = [SAMPLE_ASSETS[0]]
        response = client.get("/v1/assets")
        data = response.json()[0]
        assert set(data.keys()) == {"asset_id", "name", "category", "is_active"}

    @patch("api.routers.assets.asset_repo")
    def test_korean_name_encoding(self, mock_repo, client):
        """Korean asset names are correctly serialized."""
        mock_repo.get_all.return_value = [_make_asset("000660", "SK하이닉스", "stock")]
        response = client.get("/v1/assets")
        assert response.json()[0]["name"] == "SK하이닉스"

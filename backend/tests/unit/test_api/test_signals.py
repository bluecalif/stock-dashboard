"""Tests for GET /v1/signals endpoint."""

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


def _make_signal(
    id_: int, asset_id: str, date_str: str, strategy_id: str, signal: int, action: str
):
    m = MagicMock()
    m.id = id_
    m.asset_id = asset_id
    m.date = date_str
    m.strategy_id = strategy_id
    m.signal = signal
    m.score = 0.8
    m.action = action
    m.meta_json = None
    return m


SAMPLE_SIGNALS = [
    _make_signal(1, "005930", "2026-01-03", "momentum", 1, "BUY"),
    _make_signal(2, "005930", "2026-01-02", "momentum", 0, "HOLD"),
    _make_signal(3, "KS200", "2026-01-03", "trend", -1, "SELL"),
]


class TestListSignals:
    @patch("api.routers.signals.signal_repo")
    def test_returns_all(self, mock_repo, client):
        """Returns signals without filters."""
        mock_repo.get_signals.return_value = SAMPLE_SIGNALS
        response = client.get("/v1/signals")
        assert response.status_code == 200
        assert len(response.json()) == 3

    @patch("api.routers.signals.signal_repo")
    def test_filter_by_asset(self, mock_repo, client):
        """asset_id filter is passed to repo."""
        mock_repo.get_signals.return_value = SAMPLE_SIGNALS[:2]
        response = client.get("/v1/signals?asset_id=005930")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_signals.call_args
        assert kwargs["asset_id"] == "005930"

    @patch("api.routers.signals.signal_repo")
    def test_filter_by_strategy(self, mock_repo, client):
        """strategy_id filter is passed to repo."""
        mock_repo.get_signals.return_value = [SAMPLE_SIGNALS[2]]
        response = client.get("/v1/signals?strategy_id=trend")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_signals.call_args
        assert kwargs["strategy_id"] == "trend"

    @patch("api.routers.signals.signal_repo")
    def test_date_filter(self, mock_repo, client):
        """Date filters are passed to repo."""
        mock_repo.get_signals.return_value = []
        response = client.get("/v1/signals?start_date=2026-01-01&end_date=2026-01-03")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_signals.call_args
        assert kwargs["start_date"] is not None
        assert kwargs["end_date"] is not None

    @patch("api.routers.signals.signal_repo")
    def test_invalid_date_range(self, mock_repo, client):
        """start_date > end_date returns 400."""
        response = client.get("/v1/signals?start_date=2026-02-01&end_date=2026-01-01")
        assert response.status_code == 400

    @patch("api.routers.signals.signal_repo")
    def test_pagination(self, mock_repo, client):
        """Pagination params are passed to repo."""
        mock_repo.get_signals.return_value = []
        response = client.get("/v1/signals?limit=50&offset=10")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_signals.call_args
        assert kwargs["limit"] == 50
        assert kwargs["offset"] == 10

    @patch("api.routers.signals.signal_repo")
    def test_empty_result(self, mock_repo, client):
        """Returns empty list when no signals."""
        mock_repo.get_signals.return_value = []
        response = client.get("/v1/signals")
        assert response.status_code == 200
        assert response.json() == []

    @patch("api.routers.signals.signal_repo")
    def test_response_schema(self, mock_repo, client):
        """Response matches SignalDailyResponse schema."""
        mock_repo.get_signals.return_value = [SAMPLE_SIGNALS[0]]
        response = client.get("/v1/signals")
        data = response.json()[0]
        expected_keys = {
            "id", "asset_id", "date", "strategy_id",
            "signal", "score", "action", "meta_json",
        }
        assert set(data.keys()) == expected_keys

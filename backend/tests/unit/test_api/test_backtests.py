"""Tests for backtest endpoints."""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app

RUN_ID = uuid4()


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


def _make_run(strategy_id: str, asset_id: str, status: str = "completed", run_id=None):
    m = MagicMock()
    m.run_id = run_id or uuid4()
    m.strategy_id = strategy_id
    m.asset_id = asset_id
    m.status = status
    m.config_json = {"initial_cash": 10_000_000}
    m.metrics_json = {"total_return": 0.12}
    m.started_at = datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
    m.ended_at = datetime(2026, 1, 1, 9, 0, 5, tzinfo=timezone.utc)
    return m


def _make_equity(run_id, date_val: date, equity: float, drawdown: float):
    m = MagicMock()
    m.run_id = run_id
    m.date = date_val
    m.equity = equity
    m.drawdown = drawdown
    return m


def _make_trade(
    id_: int, run_id, asset_id: str, side: str = "LONG",
):
    m = MagicMock()
    m.id = id_
    m.run_id = run_id
    m.asset_id = asset_id
    m.entry_date = date(2026, 1, 2)
    m.entry_price = 50000.0
    m.exit_date = date(2026, 1, 10)
    m.exit_price = 52000.0
    m.side = side
    m.shares = 10.0
    m.pnl = 20000.0
    m.cost = 100.0
    return m


SAMPLE_RUNS = [
    _make_run("momentum", "005930"),
    _make_run("trend", "KS200"),
    _make_run("mean_reversion", "005930", status="running"),
]

SAMPLE_RUN = _make_run("momentum", "005930", run_id=RUN_ID)

SAMPLE_EQUITY = [
    _make_equity(RUN_ID, date(2026, 1, 2), 10_000_000, 0.0),
    _make_equity(RUN_ID, date(2026, 1, 3), 10_050_000, 0.0),
    _make_equity(RUN_ID, date(2026, 1, 6), 9_980_000, -0.007),
]

SAMPLE_TRADES = [
    _make_trade(1, RUN_ID, "005930"),
    _make_trade(2, RUN_ID, "005930", side="SHORT"),
]


# ── GET /v1/backtests ──


class TestListBacktests:
    @patch("api.routers.backtests.backtest_repo")
    def test_returns_all(self, mock_repo, client):
        """Returns all backtest runs without filters."""
        mock_repo.get_runs.return_value = SAMPLE_RUNS
        response = client.get("/v1/backtests")
        assert response.status_code == 200
        assert len(response.json()) == 3

    @patch("api.routers.backtests.backtest_repo")
    def test_filter_by_strategy(self, mock_repo, client):
        """strategy_id filter is passed to repo."""
        mock_repo.get_runs.return_value = [SAMPLE_RUNS[0]]
        response = client.get("/v1/backtests?strategy_id=momentum")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_runs.call_args
        assert kwargs["strategy_id"] == "momentum"

    @patch("api.routers.backtests.backtest_repo")
    def test_filter_by_asset(self, mock_repo, client):
        """asset_id filter is passed to repo."""
        mock_repo.get_runs.return_value = SAMPLE_RUNS[:1]
        response = client.get("/v1/backtests?asset_id=005930")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_runs.call_args
        assert kwargs["asset_id"] == "005930"

    @patch("api.routers.backtests.backtest_repo")
    def test_pagination(self, mock_repo, client):
        """Pagination params are passed to repo."""
        mock_repo.get_runs.return_value = []
        response = client.get("/v1/backtests?limit=10&offset=5")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_runs.call_args
        assert kwargs["limit"] == 10
        assert kwargs["offset"] == 5

    @patch("api.routers.backtests.backtest_repo")
    def test_empty_result(self, mock_repo, client):
        """Returns empty list when no runs."""
        mock_repo.get_runs.return_value = []
        response = client.get("/v1/backtests")
        assert response.status_code == 200
        assert response.json() == []

    @patch("api.routers.backtests.backtest_repo")
    def test_response_schema(self, mock_repo, client):
        """Response matches BacktestRunResponse schema."""
        mock_repo.get_runs.return_value = [SAMPLE_RUNS[0]]
        response = client.get("/v1/backtests")
        data = response.json()[0]
        expected_keys = {
            "run_id", "strategy_id", "asset_id", "status",
            "config_json", "metrics_json", "started_at", "ended_at",
        }
        assert set(data.keys()) == expected_keys

    @patch("api.routers.backtests.backtest_repo")
    def test_combined_filters(self, mock_repo, client):
        """Both strategy_id and asset_id filters are passed to repo."""
        mock_repo.get_runs.return_value = [SAMPLE_RUNS[0]]
        response = client.get("/v1/backtests?strategy_id=momentum&asset_id=005930")
        assert response.status_code == 200
        _, kwargs = mock_repo.get_runs.call_args
        assert kwargs["strategy_id"] == "momentum"
        assert kwargs["asset_id"] == "005930"


# ── GET /v1/backtests/{run_id} ──


class TestGetBacktest:
    @patch("api.routers.backtests.backtest_repo")
    def test_found(self, mock_repo, client):
        """Returns a single backtest run."""
        mock_repo.get_run_by_id.return_value = SAMPLE_RUN
        response = client.get(f"/v1/backtests/{RUN_ID}")
        assert response.status_code == 200
        data = response.json()
        assert data["strategy_id"] == "momentum"
        assert data["run_id"] == str(RUN_ID)

    @patch("api.routers.backtests.backtest_repo")
    def test_not_found(self, mock_repo, client):
        """Returns 404 when run_id does not exist."""
        mock_repo.get_run_by_id.return_value = None
        fake_id = uuid4()
        response = client.get(f"/v1/backtests/{fake_id}")
        assert response.status_code == 404

    @patch("api.routers.backtests.backtest_repo")
    def test_invalid_uuid(self, mock_repo, client):
        """Returns 422 for invalid UUID format."""
        response = client.get("/v1/backtests/not-a-uuid")
        assert response.status_code == 422


# ── GET /v1/backtests/{run_id}/equity ──


class TestGetEquity:
    @patch("api.routers.backtests.backtest_repo")
    def test_returns_equity_curve(self, mock_repo, client):
        """Returns equity curve records."""
        mock_repo.get_run_by_id.return_value = SAMPLE_RUN
        mock_repo.get_equity_curve.return_value = SAMPLE_EQUITY
        response = client.get(f"/v1/backtests/{RUN_ID}/equity")
        assert response.status_code == 200
        assert len(response.json()) == 3

    @patch("api.routers.backtests.backtest_repo")
    def test_equity_schema(self, mock_repo, client):
        """Response matches EquityCurveResponse schema."""
        mock_repo.get_run_by_id.return_value = SAMPLE_RUN
        mock_repo.get_equity_curve.return_value = [SAMPLE_EQUITY[0]]
        response = client.get(f"/v1/backtests/{RUN_ID}/equity")
        data = response.json()[0]
        expected_keys = {"run_id", "date", "equity", "drawdown"}
        assert set(data.keys()) == expected_keys

    @patch("api.routers.backtests.backtest_repo")
    def test_equity_empty(self, mock_repo, client):
        """Returns empty list when no equity data."""
        mock_repo.get_run_by_id.return_value = SAMPLE_RUN
        mock_repo.get_equity_curve.return_value = []
        response = client.get(f"/v1/backtests/{RUN_ID}/equity")
        assert response.status_code == 200
        assert response.json() == []

    @patch("api.routers.backtests.backtest_repo")
    def test_equity_run_not_found(self, mock_repo, client):
        """Returns 404 when run_id does not exist."""
        mock_repo.get_run_by_id.return_value = None
        fake_id = uuid4()
        response = client.get(f"/v1/backtests/{fake_id}/equity")
        assert response.status_code == 404


# ── GET /v1/backtests/{run_id}/trades ──


class TestGetTrades:
    @patch("api.routers.backtests.backtest_repo")
    def test_returns_trades(self, mock_repo, client):
        """Returns trade log records."""
        mock_repo.get_run_by_id.return_value = SAMPLE_RUN
        mock_repo.get_trades.return_value = SAMPLE_TRADES
        response = client.get(f"/v1/backtests/{RUN_ID}/trades")
        assert response.status_code == 200
        assert len(response.json()) == 2

    @patch("api.routers.backtests.backtest_repo")
    def test_trades_schema(self, mock_repo, client):
        """Response matches TradeLogResponse schema."""
        mock_repo.get_run_by_id.return_value = SAMPLE_RUN
        mock_repo.get_trades.return_value = [SAMPLE_TRADES[0]]
        response = client.get(f"/v1/backtests/{RUN_ID}/trades")
        data = response.json()[0]
        expected_keys = {
            "id", "run_id", "asset_id", "entry_date", "entry_price",
            "exit_date", "exit_price", "side", "shares", "pnl", "cost",
        }
        assert set(data.keys()) == expected_keys

    @patch("api.routers.backtests.backtest_repo")
    def test_trades_empty(self, mock_repo, client):
        """Returns empty list when no trades."""
        mock_repo.get_run_by_id.return_value = SAMPLE_RUN
        mock_repo.get_trades.return_value = []
        response = client.get(f"/v1/backtests/{RUN_ID}/trades")
        assert response.status_code == 200
        assert response.json() == []

    @patch("api.routers.backtests.backtest_repo")
    def test_trades_run_not_found(self, mock_repo, client):
        """Returns 404 when run_id does not exist."""
        mock_repo.get_run_by_id.return_value = None
        fake_id = uuid4()
        response = client.get(f"/v1/backtests/{fake_id}/trades")
        assert response.status_code == 404

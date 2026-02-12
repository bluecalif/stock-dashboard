"""Tests for dashboard summary endpoint."""

from datetime import date, datetime, timezone
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


def _make_asset(asset_id: str, name: str, is_active: bool = True):
    m = MagicMock()
    m.asset_id = asset_id
    m.name = name
    m.category = "index"
    m.is_active = is_active
    return m


def _make_price(asset_id: str, date_val: date, close: float):
    m = MagicMock()
    m.asset_id = asset_id
    m.date = date_val
    m.open = close
    m.high = close
    m.low = close
    m.close = close
    m.volume = 1000
    m.source = "fdr"
    return m


def _make_signal(asset_id: str, strategy_id: str, action: str):
    m = MagicMock()
    m.asset_id = asset_id
    m.strategy_id = strategy_id
    m.action = action
    m.signal = 1
    m.date = date(2026, 2, 10)
    return m


def _make_run(strategy_id: str, asset_id: str):
    m = MagicMock()
    m.run_id = uuid4()
    m.strategy_id = strategy_id
    m.asset_id = asset_id
    m.status = "completed"
    m.config_json = {"initial_cash": 10_000_000}
    m.metrics_json = {"total_return": 0.1}
    m.started_at = datetime(2026, 1, 1, 9, 0, 0, tzinfo=timezone.utc)
    m.ended_at = datetime(2026, 1, 1, 9, 0, 5, tzinfo=timezone.utc)
    return m


class TestDashboardSummary:
    """GET /v1/dashboard/summary tests."""

    @patch("api.services.dashboard_service.backtest_repo")
    @patch("api.services.dashboard_service.signal_repo")
    @patch("api.services.dashboard_service.price_repo")
    @patch("api.services.dashboard_service.asset_repo")
    def test_summary_basic(self, mock_asset, mock_price, mock_signal, mock_bt, client):
        """Returns assets with latest price and change %."""
        mock_asset.get_all.return_value = [_make_asset("KS200", "KOSPI200")]
        mock_price.get_prices.return_value = [
            _make_price("KS200", date(2026, 2, 10), 300.0),
            _make_price("KS200", date(2026, 2, 9), 290.0),
        ]
        mock_signal.get_latest_signal.return_value = None
        mock_bt.get_runs.return_value = []

        resp = client.get("/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["assets"]) == 1
        asset = data["assets"][0]
        assert asset["asset_id"] == "KS200"
        assert asset["latest_price"] == 300.0
        # (300-290)/290 * 100 = 3.45
        assert asset["price_change_pct"] == pytest.approx(3.45, abs=0.01)

    @patch("api.services.dashboard_service.backtest_repo")
    @patch("api.services.dashboard_service.signal_repo")
    @patch("api.services.dashboard_service.price_repo")
    @patch("api.services.dashboard_service.asset_repo")
    def test_summary_no_prices(self, mock_asset, mock_price, mock_signal, mock_bt, client):
        """Asset with no prices → null values."""
        mock_asset.get_all.return_value = [_make_asset("BTC", "비트코인")]
        mock_price.get_prices.return_value = []
        mock_signal.get_latest_signal.return_value = None
        mock_bt.get_runs.return_value = []

        resp = client.get("/v1/dashboard/summary")
        assert resp.status_code == 200
        asset = resp.json()["assets"][0]
        assert asset["latest_price"] is None
        assert asset["price_change_pct"] is None

    @patch("api.services.dashboard_service.backtest_repo")
    @patch("api.services.dashboard_service.signal_repo")
    @patch("api.services.dashboard_service.price_repo")
    @patch("api.services.dashboard_service.asset_repo")
    def test_summary_single_price(self, mock_asset, mock_price, mock_signal, mock_bt, client):
        """Only one price record → change is null."""
        mock_asset.get_all.return_value = [_make_asset("SOXL", "SOXL")]
        mock_price.get_prices.return_value = [
            _make_price("SOXL", date(2026, 2, 10), 50.0),
        ]
        mock_signal.get_latest_signal.return_value = None
        mock_bt.get_runs.return_value = []

        resp = client.get("/v1/dashboard/summary")
        asset = resp.json()["assets"][0]
        assert asset["latest_price"] == 50.0
        assert asset["price_change_pct"] is None

    @patch("api.services.dashboard_service.backtest_repo")
    @patch("api.services.dashboard_service.signal_repo")
    @patch("api.services.dashboard_service.price_repo")
    @patch("api.services.dashboard_service.asset_repo")
    def test_summary_with_signals(self, mock_asset, mock_price, mock_signal, mock_bt, client):
        """Signals are included per strategy."""
        mock_asset.get_all.return_value = [_make_asset("005930", "삼성전자")]
        mock_price.get_prices.return_value = [
            _make_price("005930", date(2026, 2, 10), 70000.0),
            _make_price("005930", date(2026, 2, 9), 69000.0),
        ]

        def _signal_side_effect(db, asset_id, *, strategy_id=None):
            if strategy_id == "momentum":
                return _make_signal(asset_id, "momentum", "buy")
            if strategy_id == "trend":
                return _make_signal(asset_id, "trend", "hold")
            return None

        mock_signal.get_latest_signal.side_effect = _signal_side_effect
        mock_bt.get_runs.return_value = []

        resp = client.get("/v1/dashboard/summary")
        asset = resp.json()["assets"][0]
        assert asset["latest_signal"]["momentum"] == "buy"
        assert asset["latest_signal"]["trend"] == "hold"
        assert "mean_reversion" not in asset["latest_signal"]

    @patch("api.services.dashboard_service.backtest_repo")
    @patch("api.services.dashboard_service.signal_repo")
    @patch("api.services.dashboard_service.price_repo")
    @patch("api.services.dashboard_service.asset_repo")
    def test_summary_recent_backtests(self, mock_asset, mock_price, mock_signal, mock_bt, client):
        """Recent backtests are included."""
        mock_asset.get_all.return_value = []
        mock_bt.get_runs.return_value = [
            _make_run("momentum", "KS200"),
            _make_run("trend", "005930"),
        ]

        resp = client.get("/v1/dashboard/summary")
        data = resp.json()
        assert len(data["recent_backtests"]) == 2
        assert data["recent_backtests"][0]["strategy_id"] == "momentum"

    @patch("api.services.dashboard_service.backtest_repo")
    @patch("api.services.dashboard_service.signal_repo")
    @patch("api.services.dashboard_service.price_repo")
    @patch("api.services.dashboard_service.asset_repo")
    def test_summary_empty(self, mock_asset, mock_price, mock_signal, mock_bt, client):
        """No assets, no backtests → empty lists."""
        mock_asset.get_all.return_value = []
        mock_bt.get_runs.return_value = []

        resp = client.get("/v1/dashboard/summary")
        data = resp.json()
        assert data["assets"] == []
        assert data["recent_backtests"] == []
        assert "updated_at" in data

    @patch("api.services.dashboard_service.backtest_repo")
    @patch("api.services.dashboard_service.signal_repo")
    @patch("api.services.dashboard_service.price_repo")
    @patch("api.services.dashboard_service.asset_repo")
    def test_summary_multiple_assets(self, mock_asset, mock_price, mock_signal, mock_bt, client):
        """Multiple assets are all returned."""
        mock_asset.get_all.return_value = [
            _make_asset("KS200", "KOSPI200"),
            _make_asset("005930", "삼성전자"),
            _make_asset("BTC", "비트코인"),
        ]
        mock_price.get_prices.return_value = []
        mock_signal.get_latest_signal.return_value = None
        mock_bt.get_runs.return_value = []

        resp = client.get("/v1/dashboard/summary")
        assert len(resp.json()["assets"]) == 3

    @patch("api.services.dashboard_service.backtest_repo")
    @patch("api.services.dashboard_service.signal_repo")
    @patch("api.services.dashboard_service.price_repo")
    @patch("api.services.dashboard_service.asset_repo")
    def test_summary_response_schema(self, mock_asset, mock_price, mock_signal, mock_bt, client):
        """Response matches DashboardSummaryResponse schema."""
        mock_asset.get_all.return_value = [_make_asset("GC=F", "Gold")]
        mock_price.get_prices.return_value = [
            _make_price("GC=F", date(2026, 2, 10), 2000.0),
        ]
        mock_signal.get_latest_signal.return_value = None
        mock_bt.get_runs.return_value = []

        resp = client.get("/v1/dashboard/summary")
        data = resp.json()
        required_keys = {"assets", "recent_backtests", "updated_at"}
        assert required_keys <= set(data.keys())
        asset_keys = {"asset_id", "name", "latest_price", "price_change_pct", "latest_signal"}
        assert asset_keys <= set(data["assets"][0].keys())

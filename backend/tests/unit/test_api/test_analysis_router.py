"""Tests for analysis router — signal-accuracy & indicator-comparison endpoints."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from api.services.analysis.indicator_comparison import IndicatorComparisonRow
from api.services.analysis.signal_accuracy_service import SignalAccuracyResult


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


# ---------------------------------------------------------------------------
# GET /v1/analysis/signal-accuracy
# ---------------------------------------------------------------------------


class TestSignalAccuracyEndpoint:
    @patch("api.routers.analysis.compute_signal_accuracy")
    def test_success(self, mock_compute, client):
        mock_compute.return_value = SignalAccuracyResult(
            asset_id="005930",
            strategy_id="momentum",
            forward_days=5,
            total_signals=50,
            evaluated_signals=45,
            buy_count=25,
            buy_success_count=15,
            buy_success_rate=0.6,
            avg_return_after_buy=0.012,
            sell_count=20,
            sell_success_count=12,
            sell_success_rate=0.6,
            avg_return_after_sell=-0.008,
        )

        resp = client.get(
            "/v1/analysis/signal-accuracy",
            params={"asset_id": "005930", "strategy_id": "momentum"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["asset_id"] == "005930"
        assert data["strategy_id"] == "momentum"
        assert data["buy_success_rate"] == 0.6
        assert data["insufficient_data"] is False

    @patch("api.routers.analysis.compute_signal_accuracy")
    def test_insufficient_data(self, mock_compute, client):
        mock_compute.return_value = SignalAccuracyResult(
            asset_id="005930",
            strategy_id="momentum",
            forward_days=5,
            total_signals=2,
            evaluated_signals=2,
            insufficient_data=True,
        )

        resp = client.get(
            "/v1/analysis/signal-accuracy",
            params={"asset_id": "005930", "strategy_id": "momentum"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["insufficient_data"] is True
        assert data["buy_success_rate"] is None

    def test_missing_params(self, client):
        resp = client.get("/v1/analysis/signal-accuracy")
        assert resp.status_code == 422

    @patch("api.routers.analysis.compute_signal_accuracy")
    def test_custom_forward_days(self, mock_compute, client):
        mock_compute.return_value = SignalAccuracyResult(
            asset_id="005930",
            strategy_id="trend",
            forward_days=10,
            total_signals=0,
            evaluated_signals=0,
            insufficient_data=True,
        )

        resp = client.get(
            "/v1/analysis/signal-accuracy",
            params={
                "asset_id": "005930",
                "strategy_id": "trend",
                "forward_days": 10,
            },
        )

        assert resp.status_code == 200
        mock_compute.assert_called_once()
        call_kwargs = mock_compute.call_args
        assert call_kwargs.kwargs["forward_days"] == 10


# ---------------------------------------------------------------------------
# GET /v1/analysis/indicator-comparison
# ---------------------------------------------------------------------------


class TestIndicatorComparisonEndpoint:
    @patch("api.routers.analysis.compare_indicator_accuracy")
    def test_success(self, mock_compare, client):
        mock_compare.return_value = [
            IndicatorComparisonRow(
                strategy_id="trend",
                rank=1,
                buy_success_rate=0.75,
                sell_success_rate=0.7,
                avg_return_after_buy=0.02,
                avg_return_after_sell=-0.015,
                evaluated_signals=30,
                insufficient_data=False,
            ),
            IndicatorComparisonRow(
                strategy_id="momentum",
                rank=2,
                buy_success_rate=0.6,
                sell_success_rate=0.55,
                avg_return_after_buy=0.01,
                avg_return_after_sell=-0.008,
                evaluated_signals=25,
                insufficient_data=False,
            ),
            IndicatorComparisonRow(
                strategy_id="mean_reversion",
                rank=3,
                buy_success_rate=None,
                sell_success_rate=None,
                avg_return_after_buy=None,
                avg_return_after_sell=None,
                evaluated_signals=2,
                insufficient_data=True,
            ),
        ]

        resp = client.get(
            "/v1/analysis/indicator-comparison",
            params={"asset_id": "005930"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["asset_id"] == "005930"
        assert data["forward_days"] == 5
        assert data["total_strategies"] == 3
        assert len(data["strategies"]) == 3
        assert data["strategies"][0]["strategy_id"] == "trend"
        assert data["strategies"][0]["rank"] == 1
        assert data["strategies"][2]["insufficient_data"] is True

    @patch("api.routers.analysis.compare_indicator_accuracy")
    def test_custom_forward_days(self, mock_compare, client):
        mock_compare.return_value = []

        resp = client.get(
            "/v1/analysis/indicator-comparison",
            params={"asset_id": "005930", "forward_days": 20},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["forward_days"] == 20

    def test_missing_asset_id(self, client):
        resp = client.get("/v1/analysis/indicator-comparison")
        assert resp.status_code == 422

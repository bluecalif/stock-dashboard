"""Tests for analysis router — signal-accuracy, indicator-signals, indicator-comparison."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app
from api.services.analysis.indicator_comparison import IndicatorComparisonRow
from api.services.analysis.indicator_signal_service import IndicatorSignal
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
    def test_success_with_strategy(self, mock_compute, client):
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

    @patch("api.routers.analysis.compute_indicator_acc")
    def test_success_with_indicator(self, mock_compute, client):
        mock_compute.return_value = SignalAccuracyResult(
            asset_id="005930",
            strategy_id="rsi_14",
            forward_days=5,
            total_signals=30,
            evaluated_signals=25,
            buy_count=15,
            buy_success_count=10,
            buy_success_rate=0.6667,
            avg_return_after_buy=0.015,
        )

        resp = client.get(
            "/v1/analysis/signal-accuracy",
            params={"asset_id": "005930", "indicator_id": "rsi_14"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["strategy_id"] == "rsi_14"
        assert data["buy_success_rate"] == 0.6667

    def test_missing_both_ids(self, client):
        """Neither strategy_id nor indicator_id → 422."""
        resp = client.get(
            "/v1/analysis/signal-accuracy",
            params={"asset_id": "005930"},
        )
        assert resp.status_code == 422

    def test_invalid_indicator_id(self, client):
        resp = client.get(
            "/v1/analysis/signal-accuracy",
            params={"asset_id": "005930", "indicator_id": "invalid"},
        )
        assert resp.status_code == 422

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
# GET /v1/analysis/indicator-signals (DR.4 신규)
# ---------------------------------------------------------------------------


class TestIndicatorSignalsEndpoint:
    @patch("api.routers.analysis.generate_indicator_signals")
    def test_success(self, mock_gen, client):
        from datetime import date
        mock_gen.return_value = [
            IndicatorSignal(
                date=date(2026, 1, 5), indicator_id="rsi_14",
                signal=1, label="RSI 과매도 진입", value=28.5, entry_price=72000,
            ),
            IndicatorSignal(
                date=date(2026, 1, 20), indicator_id="rsi_14",
                signal=-1, label="RSI 과매수 진입", value=73.2, entry_price=81000,
            ),
        ]

        resp = client.get(
            "/v1/analysis/indicator-signals",
            params={"asset_id": "005930", "indicator_id": "rsi_14"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["asset_id"] == "005930"
        assert data["indicator_id"] == "rsi_14"
        assert data["total_signals"] == 2
        assert len(data["signals"]) == 2
        assert data["signals"][0]["signal"] == 1
        assert data["signals"][0]["label"] == "RSI 과매도 진입"

    def test_invalid_indicator(self, client):
        resp = client.get(
            "/v1/analysis/indicator-signals",
            params={"asset_id": "005930", "indicator_id": "invalid"},
        )
        assert resp.status_code == 422

    def test_missing_params(self, client):
        resp = client.get("/v1/analysis/indicator-signals")
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /v1/analysis/indicator-comparison
# ---------------------------------------------------------------------------


class TestIndicatorComparisonEndpoint:
    @patch("api.routers.analysis.compare_indicators")
    def test_indicator_mode_default(self, mock_compare, client):
        """Default mode=indicator → RSI vs MACD comparison."""
        mock_compare.return_value = [
            IndicatorComparisonRow(
                strategy_id="macd", rank=1,
                buy_success_rate=0.7, sell_success_rate=0.65,
                avg_return_after_buy=0.02, avg_return_after_sell=-0.015,
                evaluated_signals=30, insufficient_data=False,
            ),
            IndicatorComparisonRow(
                strategy_id="rsi_14", rank=2,
                buy_success_rate=0.6, sell_success_rate=0.55,
                avg_return_after_buy=0.01, avg_return_after_sell=-0.008,
                evaluated_signals=25, insufficient_data=False,
            ),
        ]

        resp = client.get(
            "/v1/analysis/indicator-comparison",
            params={"asset_id": "005930"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "indicators" in data
        assert data["total_indicators"] == 2
        assert data["indicators"][0]["strategy_id"] == "macd"

    @patch("api.routers.analysis.compare_indicator_accuracy")
    def test_strategy_mode(self, mock_compare, client):
        """mode=strategy → 3전략 비교 (하위호환)."""
        mock_compare.return_value = [
            IndicatorComparisonRow(
                strategy_id="trend", rank=1,
                buy_success_rate=0.75, sell_success_rate=0.7,
                avg_return_after_buy=0.02, avg_return_after_sell=-0.015,
                evaluated_signals=30, insufficient_data=False,
            ),
        ]

        resp = client.get(
            "/v1/analysis/indicator-comparison",
            params={"asset_id": "005930", "mode": "strategy"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert "strategies" in data
        assert data["total_strategies"] == 1

    def test_missing_asset_id(self, client):
        resp = client.get("/v1/analysis/indicator-comparison")
        assert resp.status_code == 422

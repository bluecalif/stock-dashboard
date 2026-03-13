"""Tests for LLM tools — analyze_correlation_tool, get_spread."""

import json
from datetime import date
from unittest.mock import MagicMock, patch

from api.services.llm.tools import analyze_correlation_tool, get_spread


def _make_price(asset_id: str, d: date, close: float):
    m = MagicMock()
    m.asset_id = asset_id
    m.date = d
    m.close = close
    return m


def _make_corr_response(asset_ids, matrix, start, end, window):
    m = MagicMock()
    m.asset_ids = asset_ids
    m.matrix = matrix
    m.period = MagicMock()
    m.period.start = start
    m.period.end = end
    m.period.window = window
    return m


# ---------------------------------------------------------------------------
# analyze_correlation_tool
# ---------------------------------------------------------------------------

class TestAnalyzeCorrelationTool:
    @patch("api.services.llm.tools.compute_correlation")
    @patch("api.services.llm.tools.SessionLocal")
    def test_returns_valid_json(self, mock_session_cls, mock_compute):
        mock_db = MagicMock()
        mock_session_cls.return_value = mock_db

        mock_compute.return_value = _make_corr_response(
            asset_ids=["KS200", "005930"],
            matrix=[[1.0, 0.9], [0.9, 1.0]],
            start=date(2026, 1, 1),
            end=date(2026, 3, 1),
            window=60,
        )

        result = analyze_correlation_tool.invoke({
            "asset_ids": ["KS200", "005930"],
            "days": 60,
            "threshold": 0.7,
        })
        data = json.loads(result)
        assert "groups" in data
        assert "top_pairs" in data
        assert "similar" in data
        assert "period" in data

    @patch("api.services.llm.tools.compute_correlation")
    @patch("api.services.llm.tools.SessionLocal")
    def test_groups_with_high_correlation(self, mock_session_cls, mock_compute):
        mock_session_cls.return_value = MagicMock()
        mock_compute.return_value = _make_corr_response(
            asset_ids=["KS200", "005930", "BTC"],
            matrix=[
                [1.0, 0.9, 0.3],
                [0.9, 1.0, 0.2],
                [0.3, 0.2, 1.0],
            ],
            start=date(2026, 1, 1),
            end=date(2026, 3, 1),
            window=60,
        )

        result = analyze_correlation_tool.invoke({
            "asset_ids": ["KS200", "005930", "BTC"],
            "days": 60,
            "threshold": 0.7,
        })
        data = json.loads(result)
        assert len(data["groups"]) == 1
        assert set(data["groups"][0]["asset_ids"]) == {"KS200", "005930"}
        assert "interpretation" in data["groups"][0]

    @patch("api.services.llm.tools.compute_correlation")
    @patch("api.services.llm.tools.SessionLocal")
    def test_similar_with_target(self, mock_session_cls, mock_compute):
        mock_session_cls.return_value = MagicMock()
        mock_compute.return_value = _make_corr_response(
            asset_ids=["KS200", "005930"],
            matrix=[[1.0, 0.85], [0.85, 1.0]],
            start=date(2026, 1, 1),
            end=date(2026, 3, 1),
            window=60,
        )

        result = analyze_correlation_tool.invoke({
            "asset_ids": ["KS200", "005930"],
            "days": 60,
            "threshold": 0.7,
            "target_id": "KS200",
        })
        data = json.loads(result)
        assert len(data["similar"]) == 1
        assert data["similar"][0]["asset_id"] == "005930"

    @patch("api.services.llm.tools.compute_correlation")
    @patch("api.services.llm.tools.SessionLocal")
    def test_top_pairs_have_interpretation(self, mock_session_cls, mock_compute):
        mock_session_cls.return_value = MagicMock()
        mock_compute.return_value = _make_corr_response(
            asset_ids=["A", "B"],
            matrix=[[1.0, 0.5], [0.5, 1.0]],
            start=date(2026, 1, 1),
            end=date(2026, 3, 1),
            window=60,
        )

        result = analyze_correlation_tool.invoke({"days": 60})
        data = json.loads(result)
        for pair in data["top_pairs"]:
            assert "interpretation" in pair


# ---------------------------------------------------------------------------
# get_spread
# ---------------------------------------------------------------------------

class TestGetSpreadTool:
    @patch("api.services.llm.tools.compute_spread")
    @patch("api.services.llm.tools.SessionLocal")
    def test_returns_valid_json(self, mock_session_cls, mock_compute):
        mock_session_cls.return_value = MagicMock()

        spread_result = MagicMock()
        spread_result.asset_a = "KS200"
        spread_result.asset_b = "005930"
        spread_result.current_z_score = 1.5
        spread_result.mean = 1.0
        spread_result.std = 0.05
        spread_result.dates = [date(2026, 1, i) for i in range(1, 11)]
        spread_result.convergence_events = []
        mock_compute.return_value = spread_result

        result = get_spread.invoke({
            "asset_a": "KS200",
            "asset_b": "005930",
            "days": 60,
        })
        data = json.loads(result)
        assert data["asset_a"] == "KS200"
        assert data["asset_b"] == "005930"
        assert data["current_z_score"] == 1.5
        assert "z_score_interpretation" in data
        assert "z_score_description" in data
        assert data["data_points"] == 10

    @patch("api.services.llm.tools.compute_spread")
    @patch("api.services.llm.tools.SessionLocal")
    def test_convergence_events_serialized(self, mock_session_cls, mock_compute):
        mock_session_cls.return_value = MagicMock()

        event = MagicMock()
        event.date = date(2026, 2, 15)
        event.z_score = 2.3
        event.direction = "divergence"

        spread_result = MagicMock()
        spread_result.asset_a = "A"
        spread_result.asset_b = "B"
        spread_result.current_z_score = 0.5
        spread_result.mean = 1.0
        spread_result.std = 0.03
        spread_result.dates = [date(2026, 1, 1)]
        spread_result.convergence_events = [event]
        mock_compute.return_value = spread_result

        result = get_spread.invoke({"asset_a": "A", "asset_b": "B", "days": 30})
        data = json.loads(result)
        assert len(data["convergence_events"]) == 1
        assert data["convergence_events"][0]["direction"] == "divergence"

    @patch("api.services.llm.tools.compute_spread")
    @patch("api.services.llm.tools.SessionLocal")
    def test_extreme_z_score_interpretation(self, mock_session_cls, mock_compute):
        mock_session_cls.return_value = MagicMock()

        spread_result = MagicMock()
        spread_result.asset_a = "A"
        spread_result.asset_b = "B"
        spread_result.current_z_score = 2.5
        spread_result.mean = 1.0
        spread_result.std = 0.05
        spread_result.dates = [date(2026, 1, 1)]
        spread_result.convergence_events = []
        mock_compute.return_value = spread_result

        result = get_spread.invoke({"asset_a": "A", "asset_b": "B", "days": 60})
        data = json.loads(result)
        assert "극단" in data["z_score_interpretation"]

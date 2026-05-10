"""F.4: DataFetcher — tool 호출 mock 테스트."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from api.services.llm.agentic.data_fetcher import (
    _build_tool_args,
    fetch_data,
)
from api.services.llm.agentic.schemas import ClassificationResult


class TestBuildToolArgs:
    def _make_classification(self, **overrides) -> ClassificationResult:
        defaults = {
            "target_page": "home",
            "category": "general",
            "confidence": 0.8,
            "asset_ids": ["KS200"],
            "params": {},
            "required_tools": [],
        }
        defaults.update(overrides)
        return ClassificationResult(**defaults)

    def test_get_prices_args(self):
        c = self._make_classification(params={"days": 20})
        args = _build_tool_args("get_prices", c)
        assert args["asset_id"] == "KS200"
        assert args["days"] == 20

    def test_get_spread_two_assets(self):
        c = self._make_classification(asset_ids=["KS200", "005930"])
        args = _build_tool_args("get_spread", c)
        assert args["asset_a"] == "KS200"
        assert args["asset_b"] == "005930"

    def test_get_spread_defaults(self):
        c = self._make_classification(asset_ids=[])
        args = _build_tool_args("get_spread", c)
        assert args["asset_a"] == "KS200"
        assert args["asset_b"] == "005930"

    def test_simulation_replay_args(self):
        c = self._make_classification(
            asset_ids=["QQQ"],
            params={"monthly_amount": 500_000, "period_years": 5},
        )
        args = _build_tool_args("simulation_replay", c)
        assert args["asset_code"] == "QQQ"
        assert args["monthly_amount"] == 500_000
        assert args["period_years"] == 5

    def test_simulation_strategy_args(self):
        c = self._make_classification(
            asset_ids=["SPY"],
            params={"strategy": "B", "period_years": 3},
        )
        args = _build_tool_args("simulation_strategy", c)
        assert args["asset_code"] == "SPY"
        assert args["strategy"] == "B"

    def test_analyze_indicators_args(self):
        c = self._make_classification(params={"forward_days": 10})
        args = _build_tool_args("analyze_indicators", c)
        assert args["forward_days"] == 10

    def test_analyze_correlation_with_target(self):
        c = self._make_classification(
            asset_ids=["005930"],
            params={"target_id": "005930"},
        )
        args = _build_tool_args("analyze_correlation_tool", c)
        assert args["target_id"] == "005930"
        # 1개 자산 → asset_ids=None (전체 활성 자산 사용)
        assert args["asset_ids"] is None

    def test_analyze_correlation_two_assets(self):
        c = self._make_classification(
            asset_ids=["005930", "KS200"],
            params={"target_id": "005930"},
        )
        args = _build_tool_args("analyze_correlation_tool", c)
        assert args["asset_ids"] == ["005930", "KS200"]

    def test_get_correlation_single_asset_uses_all(self):
        """asset_ids가 1개일 때 None 전달 (전체 자산 사용)."""
        c = self._make_classification(asset_ids=["005930"])
        args = _build_tool_args("get_correlation", c)
        assert args["asset_ids"] is None

    def test_get_correlation_two_assets(self):
        c = self._make_classification(asset_ids=["005930", "KS200"])
        args = _build_tool_args("get_correlation", c)
        assert args["asset_ids"] == ["005930", "KS200"]

    def test_unknown_tool(self):
        c = self._make_classification()
        args = _build_tool_args("nonexistent", c)
        assert args == {}


class TestFetchData:
    @pytest.mark.asyncio
    async def test_single_tool_success(self):
        classification = ClassificationResult(
            target_page="prices",
            category="general",
            confidence=0.8,
            required_tools=["get_prices"],
            asset_ids=["KS200"],
            params={"days": 5},
        )

        mock_data = [{"date": "2026-03-01", "close": 350.0}]
        mock_tool = MagicMock()
        mock_tool.invoke.return_value = json.dumps(mock_data)

        with (
            patch.dict(
                "api.services.llm.agentic.data_fetcher._TOOL_MAP",
                {"get_prices": mock_tool},
            ),
            patch(
                "api.services.llm.agentic.data_fetcher._get_name_map",
                return_value={"KS200": "KOSPI200"},
            ),
        ):
            results = await fetch_data(classification)

        assert "get_prices" in results
        assert results["get_prices"] == mock_data
        assert results["name_map"] == {"KS200": "KOSPI200"}

    @pytest.mark.asyncio
    async def test_tool_failure_skipped(self):
        """개별 tool 실패 시 skip, 나머지 결과 반환."""
        classification = ClassificationResult(
            target_page="indicators",
            category="indicator_explain",
            confidence=0.8,
            required_tools=["analyze_indicators", "get_factors"],
            asset_ids=["KS200"],
            params={},
        )

        mock_indicators = MagicMock()
        mock_indicators.invoke.side_effect = Exception("DB error")

        mock_factors = MagicMock()
        mock_factors.invoke.return_value = json.dumps([{"factor": "rsi"}])

        with (
            patch.dict(
                "api.services.llm.agentic.data_fetcher._TOOL_MAP",
                {
                    "analyze_indicators": mock_indicators,
                    "get_factors": mock_factors,
                },
            ),
            patch(
                "api.services.llm.agentic.data_fetcher._get_name_map",
                return_value={},
            ),
        ):
            results = await fetch_data(classification)

        # Failed tool has error marker
        assert "error" in results["analyze_indicators"]
        # Successful tool has data
        assert results["get_factors"] == [{"factor": "rsi"}]

    @pytest.mark.asyncio
    async def test_no_tools(self):
        """required_tools가 빈 리스트일 때."""
        classification = ClassificationResult(
            target_page="home",
            category="general",
            confidence=0.3,
            required_tools=[],
            asset_ids=[],
            params={},
        )

        with patch(
            "api.services.llm.agentic.data_fetcher._get_name_map",
            return_value={},
        ):
            results = await fetch_data(classification)

        assert results == {"name_map": {}}

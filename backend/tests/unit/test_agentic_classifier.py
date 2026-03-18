"""F.3: LLM Classifier — mock 기반 유닛 테스트."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from api.services.llm.agentic.classifier import (
    _build_user_message,
    classify_question,
)


class TestBuildUserMessage:
    def test_minimal(self):
        msg = _build_user_message("상관관계 분석해줘", "home", None, None)
        assert "현재 페이지: home" in msg
        assert "상관관계 분석해줘" in msg

    def test_with_assets_and_params(self):
        msg = _build_user_message(
            "RSI 보여줘",
            "indicators",
            ["KS200", "005930"],
            {"forward_days": 5},
        )
        assert "indicators" in msg
        assert "KS200" in msg
        assert "005930" in msg
        assert "forward_days" in msg


class TestClassifyQuestion:
    @pytest.mark.asyncio
    async def test_successful_classification(self):
        mock_json = (
            '{"target_page": "correlation", "should_navigate": true,'
            ' "category": "similar_assets",'
            ' "required_tools": ["analyze_correlation_tool"],'
            ' "asset_ids": ["KS200"], "params": {"days": 60},'
            ' "confidence": 0.9}'
        )
        mock_response = AsyncMock()
        mock_response.content = mock_json

        with patch(
            "api.services.llm.agentic.classifier.ChatOpenAI",
        ) as mock_cls:
            mock_llm = mock_cls.return_value
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await classify_question(
                "유사 자산 추천해줘",
                current_page="prices",
                asset_ids=["KS200"],
            )

        assert result.category == "similar_assets"
        assert result.confidence == 0.9
        assert result.should_navigate is True

    @pytest.mark.asyncio
    async def test_fallback_on_error(self):
        """LLM 실패 시 general/0.0 confidence fallback."""
        with patch(
            "api.services.llm.agentic.classifier.ChatOpenAI",
            side_effect=Exception("API error"),
        ):
            result = await classify_question("아무 질문")

        assert result.category == "general"
        assert result.confidence == 0.0
        assert result.target_page == "home"
        assert result.should_navigate is False

    @pytest.mark.asyncio
    async def test_passes_asset_ids_on_fallback(self):
        """Fallback 시 원래 asset_ids를 유지."""
        with patch(
            "api.services.llm.agentic.classifier.ChatOpenAI",
            side_effect=Exception("fail"),
        ):
            result = await classify_question(
                "질문",
                asset_ids=["005930", "000660"],
            )

        assert result.asset_ids == ["005930", "000660"]

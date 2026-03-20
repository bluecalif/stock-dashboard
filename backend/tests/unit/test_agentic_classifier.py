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


class TestUserContextBlock:
    """user_context_block 파라미터 통합 테스트."""

    def test_build_user_message_with_context_block(self):
        """user_context_block이 user message에 포함되는지 확인."""
        ctx_block = "경험 수준: beginner\n의사결정 성향: feeling"
        msg = _build_user_message(
            "RSI가 뭐야?", "indicators", None, None, ctx_block,
        )
        assert "사용자 정보" in msg
        assert "beginner" in msg
        assert "feeling" in msg

    def test_build_user_message_without_context_block(self):
        """user_context_block=None이면 사용자 정보 섹션 없음."""
        msg = _build_user_message("RSI가 뭐야?", "indicators", None, None, None)
        assert "사용자 정보" not in msg

    @pytest.mark.asyncio
    async def test_classify_passes_context_to_llm(self):
        """user_context_block이 LLM 호출 시 user message에 포함."""
        mock_json = (
            '{"target_page":"indicators","should_navigate":false,'
            '"category":"indicator_explain","required_tools":[],'
            '"asset_ids":[],"params":{},"confidence":0.85}'
        )
        mock_response = AsyncMock()
        mock_response.content = mock_json

        with patch(
            "api.services.llm.agentic.classifier.ChatOpenAI",
        ) as mock_cls:
            mock_llm = mock_cls.return_value
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            await classify_question(
                "RSI가 뭐야?",
                current_page="indicators",
                user_context_block="경험 수준: beginner",
            )

            # ainvoke에 전달된 user message 확인
            call_args = mock_llm.ainvoke.call_args[0][0]
            user_msg = call_args[1]["content"]
            assert "beginner" in user_msg

    @pytest.mark.asyncio
    async def test_classify_unsupported_category(self):
        """unsupported 카테고리가 정상 반환되는지 확인."""
        mock_json = (
            '{"target_page":"home","should_navigate":false,'
            '"category":"unsupported","required_tools":[],'
            '"asset_ids":[],"params":{},"confidence":0.95}'
        )
        mock_response = AsyncMock()
        mock_response.content = mock_json

        with patch(
            "api.services.llm.agentic.classifier.ChatOpenAI",
        ) as mock_cls:
            mock_llm = mock_cls.return_value
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await classify_question("오늘 날씨 어때?")

        assert result.category == "unsupported"
        assert result.confidence == 0.95

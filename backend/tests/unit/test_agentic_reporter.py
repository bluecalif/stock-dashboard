"""F.5: LLM Reporter — mock 기반 유닛 테스트."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from api.services.llm.agentic.reporter import (
    _build_system_prompt,
    _build_user_message,
    generate_report,
)
from api.services.llm.agentic.schemas import CuratedReport, UIActionModel


class TestBuildSystemPrompt:
    def test_includes_expert_prompt(self):
        prompt = _build_system_prompt("correlation_explain", "correlation")
        assert "상관도 분석 전문가" in prompt
        assert "correlation_explain" in prompt

    def test_includes_category(self):
        prompt = _build_system_prompt("strategy_backtest", "strategy")
        assert "strategy_backtest" in prompt
        assert "투자 전략 분석 전문가" in prompt

    def test_unknown_page_falls_back(self):
        prompt = _build_system_prompt("general", "unknown_page")
        assert "가격 분석 전문가" in prompt  # default


class TestBuildUserMessage:
    def test_includes_question(self):
        msg = _build_user_message("RSI가 뭔가요?", {"data": 42})
        assert "RSI가 뭔가요?" in msg

    def test_includes_data(self):
        msg = _build_user_message("질문", {"rsi": 75.3, "signal": "sell"})
        assert "75.3" in msg
        assert "sell" in msg


class TestGenerateReport:
    @pytest.mark.asyncio
    async def test_successful_report(self):
        mock_report = CuratedReport(
            summary="RSI가 과매수 구간입니다.",
            analysis="## RSI 분석\nKS200의 RSI는 75입니다.",
            verdict="단기 조정에 주의",
            ui_actions=[
                UIActionModel(action="set_filter", payload={"key": "factor", "value": "rsi_14"}),
            ],
            follow_up_questions=["MACD는 어떤가요?", "다른 자산도 볼까요?"],
        )

        mock_json = mock_report.model_dump_json()
        mock_response = AsyncMock()
        mock_response.content = mock_json

        with patch(
            "api.services.llm.agentic.reporter.ChatOpenAI",
        ) as mock_cls:
            mock_llm = mock_cls.return_value
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            result = await generate_report(
                category="indicator_explain",
                tool_results={"analyze_indicators": {"rsi": 75}},
                page_id="indicators",
                question="RSI가 뭔가요?",
            )

        assert result.summary == "RSI가 과매수 구간입니다."
        assert len(result.follow_up_questions) == 2
        assert len(result.ui_actions) == 1

    @pytest.mark.asyncio
    async def test_deep_mode_uses_pro_model(self):
        mock_report = CuratedReport(
            summary="심층 분석",
            analysis="상세 내용",
        )
        mock_response = AsyncMock()
        mock_response.content = mock_report.model_dump_json()

        with patch(
            "api.services.llm.agentic.reporter.ChatOpenAI",
        ) as mock_cls:
            mock_llm = mock_cls.return_value
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            await generate_report(
                category="strategy_backtest",
                tool_results={},
                page_id="strategy",
                question="백테스트 결과",
                deep_mode=True,
            )

            # ChatOpenAI should be called with pro model
            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["model"] == "gpt-5"

    @pytest.mark.asyncio
    async def test_lite_mode_uses_lite_model(self):
        mock_report = CuratedReport(summary="요약", analysis="분석")
        mock_response = AsyncMock()
        mock_response.content = mock_report.model_dump_json()

        with patch(
            "api.services.llm.agentic.reporter.ChatOpenAI",
        ) as mock_cls:
            mock_llm = mock_cls.return_value
            mock_llm.ainvoke = AsyncMock(return_value=mock_response)

            await generate_report(
                category="general",
                tool_results={},
                page_id="home",
                question="안녕",
                deep_mode=False,
            )

            call_kwargs = mock_cls.call_args[1]
            assert call_kwargs["model"] == "gpt-5-mini"

    @pytest.mark.asyncio
    async def test_fallback_on_error(self):
        """LLM 실패 시 fallback 리포트 반환."""
        with patch(
            "api.services.llm.agentic.reporter.ChatOpenAI",
            side_effect=Exception("API error"),
        ):
            result = await generate_report(
                category="general",
                tool_results={},
                page_id="home",
                question="테스트",
            )

        assert "생성하지 못했습니다" in result.summary
        assert result.follow_up_questions == []
        assert result.ui_actions == []

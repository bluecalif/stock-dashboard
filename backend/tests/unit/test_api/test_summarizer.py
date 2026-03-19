"""Tests for summarizer service."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from api.services.chat.summarizer import summarize_session


@pytest.fixture()
def sample_messages():
    return [
        {"role": "user", "content": "삼성전자 최근 주가 어때?"},
        {"role": "assistant", "content": "삼성전자(005930)는 최근 3% 상승했습니다."},
        {"role": "user", "content": "BTC와 비교하면?"},
        {"role": "assistant", "content": "BTC/KRW는 같은 기간 5% 상승하여 더 높은 수익률을 보입니다."},
    ]


class TestSummarizeSession:
    @patch("api.services.chat.summarizer.ChatOpenAI")
    async def test_returns_parsed_json(self, mock_llm_cls, sample_messages):
        summary_json = {
            "turn_count": 2,
            "categories_used": ["price_current"],
            "assets_discussed": ["005930", "BTC/KRW"],
            "key_findings": ["삼성전자 3% 상승", "BTC 5% 상승"],
            "user_intent": "자산 비교 분석",
        }
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(
            return_value=MagicMock(content=json.dumps(summary_json)),
        )
        mock_llm_cls.return_value = mock_instance

        result = await summarize_session(sample_messages)
        assert result["turn_count"] == 2
        assert "005930" in result["assets_discussed"]
        assert result["user_intent"] == "자산 비교 분석"

    @patch("api.services.chat.summarizer.ChatOpenAI")
    async def test_handles_invalid_json(self, mock_llm_cls, sample_messages):
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(
            return_value=MagicMock(content="not valid json"),
        )
        mock_llm_cls.return_value = mock_instance

        result = await summarize_session(sample_messages)
        assert result["turn_count"] == 2  # fallback: user message count
        assert result["user_intent"] == "요약 생성 실패"

    @patch("api.services.chat.summarizer.ChatOpenAI")
    async def test_skips_empty_content(self, mock_llm_cls):
        messages = [
            {"role": "user", "content": "테스트"},
            {"role": "assistant", "content": ""},
            {"role": "user", "content": "다음 질문"},
        ]
        summary_json = {
            "turn_count": 2,
            "categories_used": [],
            "assets_discussed": [],
            "key_findings": [],
            "user_intent": "테스트",
        }
        mock_instance = MagicMock()
        mock_instance.ainvoke = AsyncMock(
            return_value=MagicMock(content=json.dumps(summary_json)),
        )
        mock_llm_cls.return_value = mock_instance

        result = await summarize_session(messages)
        assert result["turn_count"] == 2

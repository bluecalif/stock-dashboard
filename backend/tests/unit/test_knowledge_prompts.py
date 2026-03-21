"""F.2: Knowledge Expert Prompts — 구조 및 커버리지 테스트."""

from __future__ import annotations

import pytest

from api.services.llm.agentic.knowledge_prompts import (
    CLASSIFIER_PROMPT,
    CORRELATION_EXPERT_PROMPT,
    INDICATORS_EXPERT_PROMPT,
    PRICES_EXPERT_PROMPT,
    STRATEGY_EXPERT_PROMPT,
    get_knowledge_prompt,
)


class TestClassifierPrompt:
    def test_contains_all_categories(self):
        categories = [
            "correlation_explain",
            "similar_assets",
            "spread_analysis",
            "indicator_explain",
            "indicator_accuracy",
            "indicator_compare",
            "strategy_explain",
            "strategy_backtest",
            "strategy_compare",
            "general",
        ]
        for cat in categories:
            assert cat in CLASSIFIER_PROMPT, f"Missing category: {cat}"

    def test_contains_all_pages(self):
        pages = ["prices", "correlation", "indicators", "strategy"]
        for page in pages:
            assert page in CLASSIFIER_PROMPT, f"Missing page: {page}"

    def test_contains_tool_names(self):
        tools = [
            "get_prices",
            "analyze_correlation_tool",
            "get_spread",
            "analyze_indicators",
            "backtest_strategy",
        ]
        for tool in tools:
            assert tool in CLASSIFIER_PROMPT, f"Missing tool: {tool}"

    def test_contains_asset_mapping(self):
        assert "KS200" in CLASSIFIER_PROMPT
        assert "005930" in CLASSIFIER_PROMPT
        assert "BTC/KRW" in CLASSIFIER_PROMPT


class TestExpertPrompts:
    @pytest.mark.parametrize(
        "prompt,keywords",
        [
            (PRICES_EXPERT_PROMPT, ["가격", "OHLCV", "수익률"]),
            (CORRELATION_EXPERT_PROMPT, ["상관", "스프레드", "Z-Score"]),
            (INDICATORS_EXPERT_PROMPT, ["RSI", "MACD", "ATR", "성공률"]),
            (STRATEGY_EXPERT_PROMPT, ["모멘텀", "역발상", "위험회피", "Sharpe"]),
        ],
    )
    def test_expert_has_domain_keywords(self, prompt: str, keywords: list[str]):
        for kw in keywords:
            assert kw in prompt, f"Missing keyword '{kw}' in expert prompt"

    @pytest.mark.parametrize("prompt", [
        PRICES_EXPERT_PROMPT,
        CORRELATION_EXPERT_PROMPT,
        INDICATORS_EXPERT_PROMPT,
        STRATEGY_EXPERT_PROMPT,
    ])
    def test_expert_has_common_rules(self, prompt: str):
        assert "응답 규칙" in prompt
        assert "follow_up_questions" in prompt
        assert "한국어" in prompt

    @pytest.mark.parametrize("prompt", [
        PRICES_EXPERT_PROMPT,
        CORRELATION_EXPERT_PROMPT,
        INDICATORS_EXPERT_PROMPT,
        STRATEGY_EXPERT_PROMPT,
    ])
    def test_expert_has_asset_mapping(self, prompt: str):
        assert "KS200" in prompt


class TestGetKnowledgePrompt:
    @pytest.mark.parametrize("page_id,expected_prompt", [
        ("prices", PRICES_EXPERT_PROMPT),
        ("correlation", CORRELATION_EXPERT_PROMPT),
        ("indicators", INDICATORS_EXPERT_PROMPT),
        ("strategy", STRATEGY_EXPERT_PROMPT),
        ("home", PRICES_EXPERT_PROMPT),
    ])
    def test_returns_correct_prompt(self, page_id: str, expected_prompt: str):
        assert get_knowledge_prompt(page_id) == expected_prompt

    def test_unknown_page_returns_default(self):
        result = get_knowledge_prompt("unknown_page")
        assert result == PRICES_EXPERT_PROMPT

    def test_return_type_is_str(self):
        assert isinstance(get_knowledge_prompt("correlation"), str)

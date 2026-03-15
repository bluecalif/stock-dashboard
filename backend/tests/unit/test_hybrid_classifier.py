"""Tests for hybrid classifier + templates + nudge questions."""

import pytest

from api.services.llm.hybrid.actions import (
    highlight_pair,
    navigate,
    set_filter,
    update_chart,
)
from api.services.llm.hybrid.classifier import (
    CORRELATION_EXPLAIN,
    INDICATOR_COMPARE,
    INDICATOR_EXPLAIN,
    SIGNAL_ACCURACY,
    SIMILAR_ASSETS,
    SPREAD_ANALYSIS,
    classify_question,
)
from api.services.llm.hybrid.context import PageContext
from api.services.llm.hybrid.templates import (
    get_nudge_questions,
    get_template_response,
)

# ---------------------------------------------------------------------------
# PageContext
# ---------------------------------------------------------------------------

class TestPageContext:
    def test_from_dict_full(self):
        ctx = PageContext.from_dict({
            "page_id": "correlation",
            "asset_ids": ["KS200"],
            "params": {"window": 60},
        })
        assert ctx.page_id == "correlation"
        assert ctx.asset_ids == ["KS200"]
        assert ctx.params == {"window": 60}

    def test_from_dict_none(self):
        ctx = PageContext.from_dict(None)
        assert ctx.page_id == "home"

    def test_from_dict_empty(self):
        ctx = PageContext.from_dict({})
        assert ctx.page_id == "home"


# ---------------------------------------------------------------------------
# classify_question — correlation page
# ---------------------------------------------------------------------------

class TestClassifyCorrelation:
    @pytest.fixture
    def corr_ctx(self):
        return PageContext(page_id="correlation")

    @pytest.mark.parametrize("question", [
        "상관관계가 뭔가요?",
        "상관계수가 높은 이유가 뭐죠?",
        "왜 같이 움직이는 건가요?",
        "동조화 현상이 궁금해요",
        "두 자산이 연동되는 이유",
    ])
    def test_correlation_explain(self, corr_ctx, question):
        assert classify_question(question, corr_ctx) == CORRELATION_EXPLAIN

    @pytest.mark.parametrize("question", [
        "비슷한 자산 추천해주세요",
        "유사한 종목 알려줘",
        "어떤 자산들이 비슷하게 움직이나요",
        "그룹별로 묶어주세요",
        "클러스터링 해줘",
    ])
    def test_similar_assets(self, corr_ctx, question):
        assert classify_question(question, corr_ctx) == SIMILAR_ASSETS

    @pytest.mark.parametrize("question", [
        "스프레드 분석해줘",
        "괴리율이 얼마나 되나요",
        "두 자산이 벌어지고 있나요",
        "수렴 가능성은?",
        "z-score 확인해줘",
        "페어 트레이딩 가능할까요",
    ])
    def test_spread_analysis(self, corr_ctx, question):
        assert classify_question(question, corr_ctx) == SPREAD_ANALYSIS

    @pytest.mark.parametrize("question", [
        "오늘 날씨 어때?",
        "삼성전자 가격 알려줘",
        "백테스트 결과 보여줘",
    ])
    def test_no_match_returns_none(self, corr_ctx, question):
        assert classify_question(question, corr_ctx) is None

    def test_non_correlation_page_returns_none(self):
        """Non-correlation page → no match for correlation patterns."""
        ctx = PageContext(page_id="prices")
        assert classify_question("상관관계가 뭔가요?", ctx) is None


# ---------------------------------------------------------------------------
# classify_question — indicators page
# ---------------------------------------------------------------------------

class TestClassifyIndicators:
    @pytest.fixture
    def ind_ctx(self):
        return PageContext(page_id="indicators")

    @pytest.mark.parametrize("question", [
        "현재 RSI 상태가 궁금해요",
        "MACD가 지금 어떤 상태인가요?",
        "지표 현재 수준을 보여주세요",
        "과매수인가요?",
        "골든크로스인지 확인해주세요",
    ])
    def test_indicator_explain(self, ind_ctx, question):
        assert classify_question(question, ind_ctx) == INDICATOR_EXPLAIN

    @pytest.mark.parametrize("question", [
        "매수 신호 성공률은 어떤가요?",
        "성공률을 확인해볼까요?",
        "시그널 적중률이 궁금해요",
    ])
    def test_signal_accuracy(self, ind_ctx, question):
        assert classify_question(question, ind_ctx) == SIGNAL_ACCURACY

    @pytest.mark.parametrize("question", [
        "어떤 전략의 예측력이 가장 높나요?",
        "전략 비교해주세요",
        "예측력 순위를 보여주세요",
    ])
    def test_indicator_compare(self, ind_ctx, question):
        assert classify_question(question, ind_ctx) == INDICATOR_COMPARE

    def test_non_indicator_page_returns_none(self):
        ctx = PageContext(page_id="prices")
        assert classify_question("RSI 상태 궁금해요", ctx) is None


# ---------------------------------------------------------------------------
# UIAction
# ---------------------------------------------------------------------------

class TestUIAction:
    def test_navigate(self):
        action = navigate("/correlation")
        assert action.action == "navigate"
        assert action.payload["path"] == "/correlation"

    def test_update_chart(self):
        action = update_chart("heatmap", window=30)
        d = action.to_dict()
        assert d["action"] == "update_chart"
        assert d["payload"]["chart_id"] == "heatmap"
        assert d["payload"]["window"] == 30

    def test_set_filter(self):
        action = set_filter("asset_id", "KS200")
        assert action.payload == {"key": "asset_id", "value": "KS200"}

    def test_highlight_pair(self):
        action = highlight_pair("KS200", "005930")
        assert action.payload["asset_a"] == "KS200"
        assert action.payload["asset_b"] == "005930"


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

class TestTemplates:
    def test_correlation_explain_template(self):
        ctx = PageContext(page_id="correlation")
        data = {
            "groups": [
                {
                    "group_id": 0,
                    "asset_ids": ["KS200", "005930"],
                    "avg_correlation": 0.9,
                    "interpretation": "매우 강한 양의 상관",
                },
            ],
            "top_pairs": [
                {
                    "asset_a": "KS200",
                    "asset_b": "005930",
                    "correlation": 0.9,
                    "interpretation": "매우 강한 양의 상관",
                },
            ],
        }
        result = get_template_response(CORRELATION_EXPLAIN, ctx, data)
        assert result is not None
        text, actions = result
        assert "상관도 분석" in text
        assert "KS200" in text
        assert len(actions) >= 1

    def test_similar_assets_template(self):
        ctx = PageContext(page_id="correlation")
        data = {
            "target_id": "KS200",
            "similar": [
                {"asset_id": "005930", "correlation": 0.85, "interpretation": "매우 강한"},
            ],
        }
        result = get_template_response(SIMILAR_ASSETS, ctx, data)
        assert result is not None
        text, actions = result
        assert "KS200" in text
        assert "005930" in text

    def test_spread_analysis_template(self):
        ctx = PageContext(page_id="correlation")
        data = {
            "asset_a": "KS200",
            "asset_b": "BTC",
            "current_z_score": 2.3,
            "z_score_interpretation": "극단적 이탈",
            "z_score_description": "스프레드가 크게 벗어남",
            "convergence_events": [
                {"date": "2026-03-01", "direction": "divergence", "z_score": 2.1},
            ],
        }
        result = get_template_response(SPREAD_ANALYSIS, ctx, data)
        assert result is not None
        text, actions = result
        assert "스프레드" in text
        assert "2.30" in text

    def test_indicator_explain_template(self):
        ctx = PageContext(page_id="indicators")
        data = {
            "asset_id": "005930",
            "name_map": {"005930": "삼성전자"},
            "indicator_states": [
                {
                    "factor": "RSI (14일)",
                    "value": 75.5,
                    "label": "과매수",
                    "signal": "sell",
                    "description": "RSI가 70 이상으로 과매수 구간입니다.",
                },
            ],
        }
        result = get_template_response(INDICATOR_EXPLAIN, ctx, data)
        assert result is not None
        text, actions = result
        assert "삼성전자" in text
        assert "과매수" in text
        assert len(actions) >= 1

    def test_signal_accuracy_template(self):
        ctx = PageContext(page_id="indicators")
        data = {
            "asset_id": "005930",
            "name_map": {"005930": "삼성전자"},
            "forward_days": 5,
            "signal_accuracy": [
                {
                    "strategy_id": "momentum",
                    "buy_success_rate": 0.65,
                    "sell_success_rate": 0.55,
                    "avg_return_after_buy": 0.012,
                    "avg_return_after_sell": -0.008,
                    "evaluated_signals": 20,
                    "insufficient_data": False,
                },
            ],
        }
        result = get_template_response(SIGNAL_ACCURACY, ctx, data)
        assert result is not None
        text, _ = result
        assert "성공률" in text
        assert "65.0%" in text

    def test_indicator_compare_template(self):
        ctx = PageContext(page_id="indicators")
        data = {
            "asset_id": "005930",
            "name_map": {"005930": "삼성전자"},
            "forward_days": 5,
            "strategy_ranking": [
                {
                    "rank": 1,
                    "strategy_id": "trend",
                    "buy_success_rate": 0.75,
                    "sell_success_rate": 0.7,
                    "insufficient_data": False,
                },
                {
                    "rank": 2,
                    "strategy_id": "momentum",
                    "buy_success_rate": 0.6,
                    "sell_success_rate": None,
                    "insufficient_data": False,
                },
            ],
        }
        result = get_template_response(INDICATOR_COMPARE, ctx, data)
        assert result is not None
        text, _ = result
        assert "순위" in text
        assert "75.0%" in text

    def test_unknown_category_returns_none(self):
        ctx = PageContext(page_id="correlation")
        assert get_template_response("unknown_cat", ctx, {}) is None


# ---------------------------------------------------------------------------
# Nudge questions
# ---------------------------------------------------------------------------

class TestNudgeQuestions:
    @pytest.mark.parametrize("page_id", [
        "correlation", "indicators", "strategy", "prices", "home",
    ])
    def test_nudge_per_page(self, page_id):
        questions = get_nudge_questions(page_id)
        assert len(questions) >= 1
        assert all(isinstance(q, str) for q in questions)

    def test_unknown_page_fallback(self):
        questions = get_nudge_questions("nonexistent")
        assert questions == get_nudge_questions("home")

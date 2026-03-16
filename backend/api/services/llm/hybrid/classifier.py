"""Hybrid classifier — regex + keyword based question classification.

Returns a Category string if matched, None if should fallback to LLM.
"""

from __future__ import annotations

import re

from .context import PageContext

# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

# Correlation page categories
CORRELATION_EXPLAIN = "correlation_explain"
SIMILAR_ASSETS = "similar_assets"
SPREAD_ANALYSIS = "spread_analysis"

# (Future) Indicator page categories
INDICATOR_EXPLAIN = "indicator_explain"
SIGNAL_ACCURACY = "signal_accuracy"
INDICATOR_COMPARE = "indicator_compare"

# Strategy page categories
STRATEGY_EXPLAIN = "strategy_explain"
STRATEGY_BACKTEST = "strategy_backtest"
STRATEGY_COMPARE = "strategy_compare"

# ---------------------------------------------------------------------------
# Pattern definitions: (compiled_regex, category)
# ---------------------------------------------------------------------------

_CORRELATION_PATTERNS: list[tuple[re.Pattern, str]] = [
    # similar_assets — 구체적 패턴을 먼저 매칭 (순서 중요)
    (re.compile(
        r"(비슷|유사|닮|같은).*(자산|종목|움직|패턴)",
        re.IGNORECASE,
    ), SIMILAR_ASSETS),
    (re.compile(
        r"(자산|종목).*(비슷|유사|닮|같은)",
        re.IGNORECASE,
    ), SIMILAR_ASSETS),
    (re.compile(
        r"상관.*(높|낮).*(자산|종목)",
        re.IGNORECASE,
    ), SIMILAR_ASSETS),
    (re.compile(
        r"(분산|포트폴리오|조합|배분).*(투자|적합|추천)",
        re.IGNORECASE,
    ), SIMILAR_ASSETS),
    (re.compile(
        r"(그룹|묶|분류|클러스터)",
        re.IGNORECASE,
    ), SIMILAR_ASSETS),

    # correlation_explain
    (re.compile(
        r"상관.*(관계|계수|의미|뜻|높|낮|강|약|설명|왜|이유)",
        re.IGNORECASE,
    ), CORRELATION_EXPLAIN),
    (re.compile(
        r"(왜|이유).*(같이|함께|반대|동조|역|연동)",
        re.IGNORECASE,
    ), CORRELATION_EXPLAIN),
    (re.compile(
        r"(동조|연동|커플링|디커플링)",
        re.IGNORECASE,
    ), CORRELATION_EXPLAIN),

    # spread_analysis
    (re.compile(
        r"(스프레드|괴리|이격|벌어|좁|수렴|발산)",
        re.IGNORECASE,
    ), SPREAD_ANALYSIS),
    (re.compile(
        r"(z.?score|z점수|표준편차|시그마)",
        re.IGNORECASE,
    ), SPREAD_ANALYSIS),
    (re.compile(
        r"(페어|pair).*(트레이딩|거래|매매)",
        re.IGNORECASE,
    ), SPREAD_ANALYSIS),
]

# Indicator page patterns — 구체적 패턴 먼저 (순서 중요)
_INDICATOR_PATTERNS: list[tuple[re.Pattern, str]] = [
    # indicator_compare — 가장 구체적
    (re.compile(
        r"(비교|순위|어떤|어느).*(전략|지표|예측|높|낮|좋|나은)",
        re.IGNORECASE,
    ), INDICATOR_COMPARE),
    (re.compile(
        r"(전략|지표).*(비교|순위|랭킹)",
        re.IGNORECASE,
    ), INDICATOR_COMPARE),
    (re.compile(
        r"(예측력|정확도|승률).*(비교|순위|높|낮)",
        re.IGNORECASE,
    ), INDICATOR_COMPARE),

    # signal_accuracy — 성공률 관련
    (re.compile(
        r"(성공률|적중률|정중률|승률)",
        re.IGNORECASE,
    ), SIGNAL_ACCURACY),
    (re.compile(
        r"(매수|매도).*(신호|시그널).*(성공|정확|맞)",
        re.IGNORECASE,
    ), SIGNAL_ACCURACY),
    (re.compile(
        r"(신호|시그널).*(성공|적중|정확)",
        re.IGNORECASE,
    ), SIGNAL_ACCURACY),

    # indicator_explain — 가장 넓은 매칭
    (re.compile(
        r"(RSI|MACD|변동성|ATR|지표).*(상태|뜻|의미|설명|얼마|현재|수준|보여)",
        re.IGNORECASE,
    ), INDICATOR_EXPLAIN),
    (re.compile(
        r"(과매수|과매도|골든크로스|데드크로스)",
        re.IGNORECASE,
    ), INDICATOR_EXPLAIN),
    (re.compile(
        r"(현재|지금).*(RSI|MACD|지표)",
        re.IGNORECASE,
    ), INDICATOR_EXPLAIN),
]

# Strategy page patterns — 구체적 패턴 먼저 (순서 중요)
_STRATEGY_PATTERNS: list[tuple[re.Pattern, str]] = [
    # strategy_compare — 비교 관련
    (re.compile(
        r"(비교|순위|어떤|어느).*(전략|수익|성과)",
        re.IGNORECASE,
    ), STRATEGY_COMPARE),
    (re.compile(
        r"(전략).*(비교|순위|랭킹|나은|좋)",
        re.IGNORECASE,
    ), STRATEGY_COMPARE),
    (re.compile(
        r"(모멘텀|역발상|위험회피).*(vs|비교|대비)",
        re.IGNORECASE,
    ), STRATEGY_COMPARE),

    # strategy_backtest — 백테스트/성과 관련
    (re.compile(
        r"(백테스트|수익률|손익|에쿼티|커브|성과)",
        re.IGNORECASE,
    ), STRATEGY_BACKTEST),
    (re.compile(
        r"(매매|거래).*(내역|이력|포인트|결과)",
        re.IGNORECASE,
    ), STRATEGY_BACKTEST),
    (re.compile(
        r"(모멘텀|역발상|위험회피).*(결과|수익|손실|실행|돌려)",
        re.IGNORECASE,
    ), STRATEGY_BACKTEST),
    (re.compile(
        r"(연간|연도별).*(성과|수익|손실)",
        re.IGNORECASE,
    ), STRATEGY_BACKTEST),

    # strategy_explain — 전략 설명
    (re.compile(
        r"(모멘텀|역발상|위험회피).*(뭐|무엇|설명|어떤|원리|방식|전략)",
        re.IGNORECASE,
    ), STRATEGY_EXPLAIN),
    (re.compile(
        r"(전략).*(뭐|무엇|설명|어떻게|원리|방식)",
        re.IGNORECASE,
    ), STRATEGY_EXPLAIN),
    (re.compile(
        r"(MACD|RSI|ATR).*(전략|매매)",
        re.IGNORECASE,
    ), STRATEGY_EXPLAIN),
]

# Map page_id → pattern list
_PAGE_PATTERNS: dict[str, list[tuple[re.Pattern, str]]] = {
    "correlation": _CORRELATION_PATTERNS,
    "indicators": _INDICATOR_PATTERNS,
    "strategy": _STRATEGY_PATTERNS,
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def classify_question(
    question: str,
    page_context: PageContext,
) -> str | None:
    """Classify a user question into a category based on regex patterns.

    Returns category string if matched, None if should fallback to LLM.
    Checks page-specific patterns first, then general patterns.
    """
    # Page-specific patterns
    patterns = _PAGE_PATTERNS.get(page_context.page_id, [])
    for pattern, category in patterns:
        if pattern.search(question):
            return category

    return None

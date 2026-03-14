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

# (Future) Strategy page categories
STRATEGY_EXPLAIN = "strategy_explain"
STRATEGY_COMPARE = "strategy_compare"
TRADE_STORY = "trade_story"

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

# Map page_id → pattern list
_PAGE_PATTERNS: dict[str, list[tuple[re.Pattern, str]]] = {
    "correlation": _CORRELATION_PATTERNS,
    # "indicators": _INDICATOR_PATTERNS,  # Phase D에서 추가
    # "strategy": _STRATEGY_PATTERNS,     # Phase E에서 추가
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

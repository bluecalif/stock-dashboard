"""Pydantic v2 schemas for the agentic flow.

ClassificationResult — Step 1 (LLM Classifier) output.
CuratedReport      — Step 2 (LLM Reporter) output.
UIActionModel      — Structured UI action for frontend.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PageId = Literal["prices", "correlation", "indicators", "strategy", "home"]

Category = Literal[
    # Correlation page
    "correlation_explain",
    "similar_assets",
    "spread_analysis",
    # Indicator page
    "indicator_explain",
    "signal_accuracy",
    "indicator_compare",
    # Strategy page
    "strategy_explain",
    "strategy_backtest",
    "strategy_compare",
    # Cross-page / fallback
    "general",
]

ToolName = Literal[
    "get_prices",
    "get_factors",
    "get_correlation",
    "get_signals",
    "list_backtests",
    "analyze_correlation_tool",
    "get_spread",
    "analyze_indicators",
    "backtest_strategy",
]

UIActionType = Literal[
    "navigate",
    "update_chart",
    "set_filter",
    "highlight_pair",
]


# ---------------------------------------------------------------------------
# UIActionModel
# ---------------------------------------------------------------------------

class UIActionModel(BaseModel):
    """A structured UI action sent to the frontend via SSE."""

    action: UIActionType
    payload: dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Step 1: ClassificationResult
# ---------------------------------------------------------------------------

class ClassificationResult(BaseModel):
    """Output of the LLM Classifier (Step 1).

    Determines the target page, category, and which tools to call.
    """

    target_page: PageId = Field(
        description="페이지 ID — 질문에 가장 적합한 페이지",
    )
    should_navigate: bool = Field(
        default=False,
        description="현재 페이지와 target_page가 다르면 True",
    )
    category: Category = Field(
        description="질문 카테고리 (9개 전문 + general fallback)",
    )
    required_tools: list[ToolName] = Field(
        default_factory=list,
        description="데이터 수집에 필요한 tool 이름 목록",
    )
    asset_ids: list[str] = Field(
        default_factory=list,
        description="질문에 언급된 자산 ID 목록",
    )
    params: dict[str, Any] = Field(
        default_factory=dict,
        description="tool 호출에 필요한 추가 파라미터 (예: days, strategy_name)",
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="분류 확신도 (0.5 미만이면 LangGraph fallback)",
    )


# ---------------------------------------------------------------------------
# Step 2: CuratedReport
# ---------------------------------------------------------------------------

class CuratedReport(BaseModel):
    """Output of the LLM Reporter (Step 2).

    Structured analysis report with UI actions and follow-up questions.
    """

    summary: str = Field(
        description="핵심 요약 (1~2문장)",
    )
    analysis: str = Field(
        description="상세 분석 (마크다운 허용)",
    )
    verdict: str = Field(
        default="",
        description="투자 판단/결론 (선택적, 짧은 문구)",
    )
    ui_actions: list[UIActionModel] = Field(
        default_factory=list,
        description="프론트엔드에 전송할 UI 액션 목록",
    )
    follow_up_questions: list[str] = Field(
        default_factory=list,
        min_length=0,
        max_length=5,
        description="동적 후속 질문 (최대 5개)",
    )

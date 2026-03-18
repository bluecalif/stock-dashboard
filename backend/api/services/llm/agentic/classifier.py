"""LLM Classifier — Step 1 of the agentic flow.

Uses OpenAI Structured Output to classify user questions into
a ClassificationResult (target_page, category, required_tools, etc.).
"""

from __future__ import annotations

import logging

from langchain_openai import ChatOpenAI

from config.settings import settings

from .knowledge_prompts import CLASSIFIER_PROMPT
from .schemas import ClassificationResult

logger = logging.getLogger(__name__)


async def classify_question(
    question: str,
    current_page: str = "home",
    asset_ids: list[str] | None = None,
    params: dict | None = None,
) -> ClassificationResult:
    """Classify a user question via LLM Structured Output.

    Returns ClassificationResult. On any failure, returns a safe
    general/low-confidence fallback so LangGraph handles it.
    """
    user_msg = _build_user_message(question, current_page, asset_ids, params)

    try:
        llm = ChatOpenAI(
            model=settings.llm_lite_model,
            api_key=settings.openai_api_key,
            temperature=0,
            max_retries=3,
            request_timeout=10,
        )
        structured_llm = llm.with_structured_output(ClassificationResult)
        result: ClassificationResult = await structured_llm.ainvoke([
            {"role": "system", "content": CLASSIFIER_PROMPT},
            {"role": "user", "content": user_msg},
        ])
        return result

    except Exception:
        logger.exception("LLM Classifier failed — falling back to general")
        return ClassificationResult(
            target_page="home",
            should_navigate=False,
            category="general",
            required_tools=[],
            asset_ids=asset_ids or [],
            params={},
            confidence=0.0,
        )


def _build_user_message(
    question: str,
    current_page: str,
    asset_ids: list[str] | None,
    params: dict | None,
) -> str:
    """Build the user message with context for the classifier."""
    parts = [
        f"현재 페이지: {current_page}",
    ]
    if asset_ids:
        parts.append(f"선택된 자산: {', '.join(asset_ids)}")
    if params:
        parts.append(f"페이지 파라미터: {params}")
    parts.append(f"\n질문: {question}")
    return "\n".join(parts)

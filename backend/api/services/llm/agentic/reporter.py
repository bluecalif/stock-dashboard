"""LLM Reporter — Step 2 of the agentic flow.

Uses OpenAI Structured Output to generate a CuratedReport
from tool results + knowledge expert prompt.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from langchain_openai import ChatOpenAI

from config.settings import settings

from .knowledge_prompts import get_knowledge_prompt
from .schemas import CuratedReport

logger = logging.getLogger(__name__)


async def generate_report(
    category: str,
    tool_results: dict[str, Any],
    page_id: str,
    question: str,
    deep_mode: bool = False,
) -> CuratedReport:
    """Generate a curated report from tool results via LLM.

    Uses gpt-5 for deep_mode, gpt-5-mini otherwise.
    On failure, returns a minimal fallback report.
    """
    system_prompt = _build_system_prompt(category, page_id)
    user_msg = _build_user_message(question, tool_results)

    try:
        model_name = settings.llm_pro_model if deep_mode else settings.llm_lite_model
        llm = ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key,
            temperature=0.3,
            max_retries=3,
            request_timeout=30,
        )
        structured_llm = llm.with_structured_output(CuratedReport)
        result: CuratedReport = await structured_llm.ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ])
        return result

    except Exception:
        logger.exception("LLM Reporter failed — returning fallback report")
        return CuratedReport(
            summary="분석 결과를 생성하지 못했습니다.",
            analysis="데이터는 수집되었으나 리포트 생성 중 오류가 발생했습니다. "
                     "다시 시도해주세요.",
            verdict="",
            ui_actions=[],
            follow_up_questions=[],
        )


def _build_system_prompt(category: str, page_id: str) -> str:
    """Combine knowledge expert prompt with category context."""
    expert = get_knowledge_prompt(page_id)
    return (
        f"{expert}\n\n"
        f"## 현재 카테고리: {category}\n"
        f"이 카테고리에 맞는 분석을 제공하세요."
    )


def _build_user_message(question: str, tool_results: dict[str, Any]) -> str:
    """Format question + tool data for the reporter."""
    # Serialize tool results, handling non-serializable gracefully
    try:
        data_str = json.dumps(tool_results, ensure_ascii=False, default=str)
    except Exception:
        data_str = str(tool_results)

    return (
        f"사용자 질문: {question}\n\n"
        f"## 수집된 데이터\n```json\n{data_str}\n```\n\n"
        f"위 데이터를 바탕으로 분석 리포트를 생성하세요."
    )

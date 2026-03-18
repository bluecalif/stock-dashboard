"""LLM Reporter — Step 2 of the agentic flow.

Uses OpenAI JSON mode to generate a CuratedReport
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

# CuratedReport JSON 스키마 힌트
_REPORT_SCHEMA_HINT = """
## 출력 형식 (반드시 아래 JSON 구조를 따르세요)
```json
{
  "summary": "핵심 요약 1~2문장",
  "analysis": "상세 분석 (마크다운 허용)",
  "verdict": "데이터 기반 결론 (선택적, 짧은 문구)",
  "ui_actions": [
    {"action": "highlight_pair", "payload": {"asset_a": "005930", "asset_b": "KS200"}}
  ],
  "follow_up_questions": ["후속 질문 1", "후속 질문 2"]
}
```
- ui_actions의 action 종류: navigate, update_chart, set_filter, highlight_pair
- follow_up_questions: 사용자가 이어서 물을 만한 질문 2~3개
- JSON만 출력하세요. 다른 텍스트는 포함하지 마세요."""


async def generate_report(
    category: str,
    tool_results: dict[str, Any],
    page_id: str,
    question: str,
    deep_mode: bool = False,
) -> CuratedReport:
    """Generate a curated report from tool results via LLM JSON mode.

    Uses gpt-5 for deep_mode, gpt-5-mini otherwise.
    On failure, returns a minimal fallback report.
    """
    system_prompt = _build_system_prompt(category, page_id)
    user_msg = _build_user_message(question, tool_results)

    try:
        model_name = (
            settings.llm_pro_model if deep_mode else settings.llm_lite_model
        )
        llm = ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key,
            temperature=0.3,
            max_retries=3,
            request_timeout=30,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        response = await llm.ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ])

        raw = response.content.strip()
        data = json.loads(raw)
        result = CuratedReport(**data)
        logger.info(
            "Reporter OK: summary=%.50s, ui_actions=%d, follow_ups=%d",
            result.summary,
            len(result.ui_actions),
            len(result.follow_up_questions),
        )
        return result

    except json.JSONDecodeError as exc:
        logger.error(
            "Reporter JSON parse failed: %s — raw: %.200s",
            exc,
            raw if "raw" in dir() else "(no response)",
        )
        return _fallback_report()

    except Exception as exc:
        logger.error(
            "LLM Reporter failed (model=%s): %s",
            settings.llm_pro_model if deep_mode else settings.llm_lite_model,
            exc,
        )
        return _fallback_report()


def _fallback_report() -> CuratedReport:
    """Minimal fallback report."""
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
        f"{_REPORT_SCHEMA_HINT}"
    )


def _build_user_message(question: str, tool_results: dict[str, Any]) -> str:
    """Format question + tool data for the reporter."""
    try:
        data_str = json.dumps(
            tool_results, ensure_ascii=False, default=str,
        )
    except Exception:
        data_str = str(tool_results)

    return (
        f"사용자 질문: {question}\n\n"
        f"## 수집된 데이터\n```json\n{data_str}\n```\n\n"
        f"위 데이터를 바탕으로 분석 리포트를 JSON으로 생성하세요."
    )

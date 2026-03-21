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

from .compressor import compress_tool_results
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
    user_context_block: str | None = None,
    chat_history: list[dict[str, str]] | None = None,
) -> CuratedReport:
    """Generate a curated report from tool results via LLM JSON mode.

    Uses gpt-5 for deep_mode, gpt-5-mini otherwise.
    On failure, returns a minimal fallback report.
    """
    system_prompt = _build_system_prompt(category, page_id, user_context_block)
    compressed = compress_tool_results(tool_results)
    user_msg = _build_user_message(question, compressed, chat_history)
    logger.debug("Reporter system_prompt (first 500): %s", system_prompt[:500])
    logger.debug("Reporter user_msg (first 1000): %s", user_msg[:1000])

    try:
        model_name = settings.llm_report_model
        llm = ChatOpenAI(
            model=model_name,
            api_key=settings.openai_api_key,
            temperature=0,
            max_retries=2,
            request_timeout=30,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        response = await llm.ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ])

        raw = response.content.strip()
        logger.debug("Reporter raw response (first 500): %s", raw[:500])
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
        logger.exception(
            "LLM Reporter failed (model=%s, user_msg_len=%d, tools=%s) — %s: %s",
            settings.llm_report_model,
            len(user_msg),
            list(tool_results.keys()),
            type(exc).__name__,
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


def _build_system_prompt(
    category: str,
    page_id: str,
    user_context_block: str | None = None,
) -> str:
    """Combine knowledge expert prompt with category context + user context."""
    expert = get_knowledge_prompt(page_id)
    parts = [
        expert,
        f"\n\n## 현재 카테고리: {category}",
        "\n이 카테고리에 맞는 분석을 제공하세요.",
    ]

    if user_context_block:
        parts.append(
            f"\n\n## 사용자 정보\n{user_context_block}\n"
            "위 사용자 정보를 참고하여 톤과 깊이를 조정하세요:\n"
            "- beginner: 쉬운 용어, 짧은 설명, 핵심만 전달.\n"
            "- expert: 전문 용어 사용, 수치 중심의 깊은 분석.\n"
            "- feeling 성향: 직관적·서사적 설명 (예: \"시장이 불안해 보입니다\").\n"
            "- logic 성향: 데이터·지표 중심 (예: \"RSI 28.3으로 과매도\").\n"
            "- 자주 조회하는 자산이 있으면 해당 자산 관련 예시를 포함.\n"
            "- 최근 대화 주제가 있으면 연속성 있는 분석 제공."
        )

    parts.append(_REPORT_SCHEMA_HINT)
    return "".join(parts)


def _build_user_message(
    question: str,
    tool_results: dict[str, Any],
    chat_history: list[dict[str, str]] | None = None,
) -> str:
    """Format question + tool data + conversation history for the reporter."""
    parts: list[str] = []

    # 이전 대화 맥락 (최근 N턴)
    if chat_history:
        parts.append("## 이전 대화\n")
        for msg in chat_history:
            role = "사용자" if msg["role"] == "user" else "AI"
            # 이전 응답은 200자로 요약해서 토큰 절약
            content = msg["content"]
            if msg["role"] == "assistant" and len(content) > 200:
                content = content[:200] + "…"
            parts.append(f"{role}: {content}")
        parts.append("")

    parts.append(f"사용자 질문: {question}\n")

    try:
        data_str = json.dumps(
            tool_results, ensure_ascii=False, default=str,
        )
    except Exception:
        data_str = str(tool_results)

    parts.append(f"## 수집된 데이터\n```json\n{data_str}\n```\n")
    parts.append("위 데이터를 바탕으로 분석 리포트를 JSON으로 생성하세요.")

    return "\n".join(parts)

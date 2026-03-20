"""LLM Classifier — Step 1 of the agentic flow.

Uses OpenAI JSON mode to classify user questions into
a ClassificationResult (target_page, category, required_tools, etc.).
"""

from __future__ import annotations

import json
import logging

from langchain_openai import ChatOpenAI

from config.settings import settings

from .knowledge_prompts import CLASSIFIER_PROMPT
from .schemas import ClassificationResult

logger = logging.getLogger(__name__)

# ClassificationResult의 JSON 스키마를 프롬프트에 포함
_SCHEMA_HINT = """
## 출력 형식 (반드시 아래 JSON 구조를 따르세요)
```json
{
  "target_page": "prices | correlation | indicators | strategy | home",
  "should_navigate": true/false,
  "category": "<카테고리 중 하나 (unsupported 포함)>",
  "required_tools": ["tool_name", ...],
  "asset_ids": ["KS200", ...],
  "params": {"days": 60, ...},
  "confidence": 0.0~1.0
}
```
JSON만 출력하세요. 다른 텍스트는 포함하지 마세요."""


async def classify_question(
    question: str,
    current_page: str = "home",
    asset_ids: list[str] | None = None,
    params: dict | None = None,
    user_context_block: str | None = None,
) -> ClassificationResult:
    """Classify a user question via LLM JSON mode.

    Returns ClassificationResult. On any failure, returns a safe
    general/low-confidence fallback so LangGraph handles it.
    """
    user_msg = _build_user_message(question, current_page, asset_ids, params, user_context_block)
    system_prompt = CLASSIFIER_PROMPT + _SCHEMA_HINT

    try:
        llm = ChatOpenAI(
            model=settings.llm_lite_model,
            api_key=settings.openai_api_key,
            temperature=0,
            max_retries=3,
            request_timeout=10,
            model_kwargs={"response_format": {"type": "json_object"}},
        )
        response = await llm.ainvoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ])

        raw = response.content.strip()
        data = json.loads(raw)
        result = ClassificationResult(**data)
        logger.info(
            "Classifier OK: category=%s confidence=%.2f target=%s tools=%s",
            result.category, result.confidence,
            result.target_page, result.required_tools,
        )
        return result

    except json.JSONDecodeError as exc:
        logger.error(
            "Classifier JSON parse failed: %s — raw: %.200s",
            exc, raw if "raw" in dir() else "(no response)",
        )
        return _fallback(asset_ids)

    except Exception as exc:
        logger.error(
            "LLM Classifier failed (model=%s): %s",
            settings.llm_lite_model, exc,
        )
        return _fallback(asset_ids)


def _fallback(asset_ids: list[str] | None = None) -> ClassificationResult:
    """Safe fallback — routes to LangGraph."""
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
    user_context_block: str | None = None,
) -> str:
    """Build the user message with context for the classifier."""
    parts = [
        f"현재 페이지: {current_page}",
    ]
    if asset_ids:
        parts.append(f"선택된 자산: {', '.join(asset_ids)}")
    if params:
        parts.append(f"페이지 파라미터: {params}")
    if user_context_block:
        parts.append(f"\n## 사용자 정보\n{user_context_block}")
    parts.append(f"\n질문: {question}")
    return "\n".join(parts)

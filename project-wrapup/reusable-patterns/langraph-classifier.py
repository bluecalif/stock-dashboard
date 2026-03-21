"""
## 용도
LangGraph + OpenAI 기반 질문 분류기.
JSON Mode로 구조화 응답, fallback 전략, 대화 히스토리 컨텍스트 빌드.

## 사용법
1. ClassificationResult Pydantic 모델 정의
2. 시스템 프롬프트에 JSON 스키마 힌트 포함
3. classify_question() 호출 — async

## 출처
stock-dashboard/backend/api/services/llm/agentic/classifier.py
"""

import json
import logging
from dataclasses import dataclass

from langchain_openai import ChatOpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ClassificationResult(BaseModel):
    target_page: str
    should_navigate: bool
    category: str
    required_tools: list[str]
    asset_ids: list[str]
    params: dict
    confidence: float


# JSON Mode + 수동 파싱 (with_structured_output 대신 — 프로덕션 안정성)
async def classify_question(
    question: str,
    current_page: str = "home",
    asset_ids: list[str] | None = None,
    system_prompt: str = "",
    chat_history: list[dict[str, str]] | None = None,
) -> ClassificationResult:
    user_msg = _build_user_message(question, current_page, asset_ids, chat_history)

    try:
        llm = ChatOpenAI(
            model="gpt-4o-mini",  # 경량 모델 사용
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
        return ClassificationResult(**data)

    except json.JSONDecodeError as exc:
        logger.error("Classifier JSON parse failed: %s", exc)
        return _fallback(asset_ids)
    except Exception as exc:
        logger.error("LLM Classifier failed: %s", exc)
        return _fallback(asset_ids)


def _fallback(asset_ids: list[str] | None = None) -> ClassificationResult:
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
    chat_history: list[dict[str, str]] | None = None,
) -> str:
    parts = [f"현재 페이지: {current_page}"]
    if asset_ids:
        parts.append(f"선택된 자산: {', '.join(asset_ids)}")
    if chat_history:
        lines = []
        for msg in chat_history:
            role = "사용자" if msg["role"] == "user" else "AI"
            content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
            lines.append(f"{role}: {content}")
        parts.append("\n## 이전 대화\n" + "\n".join(lines))
    parts.append(f"\n질문: {question}")
    return "\n".join(parts)

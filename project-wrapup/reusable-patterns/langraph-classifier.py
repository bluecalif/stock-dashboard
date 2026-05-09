"""
## 용도
LangGraph + OpenAI 기반 질문 분류기. JSON Mode + fallback + 대화 히스토리 컨텍스트.
수정 필요 (프롬프트/카테고리/ClassificationResult 필드 교체).

## 언제 쓰는가
사용자 질문을 카테고리/의도별로 분류하여 적절한 처리 파이프라인으로 라우팅할 때.
with_structured_output 대신 안정적인 JSON Mode가 필요할 때 (T-010).

## 전제조건
- OpenAI API 키 + 결제 설정 (P-008)
- 분류 카테고리 정의 (프로젝트별로 다름)

## 의존성
- langchain-openai: ChatOpenAI
- pydantic: ClassificationResult 스키마
- json, logging: 파싱 + 에러 로깅

## 통합 포인트
- services/llm/agentic/ 디렉토리에 배치
- LangGraph 그래프의 첫 번째 노드(classify)에서 호출
- ClassificationResult로 다음 노드(data_fetch, report 등) 결정
- 하이브리드 분류: 정규표현식 먼저, LLM은 fallback (A-007)

## 주의사항
- with_structured_output 사용 금지 — JSON Mode + 수동 파싱이 프로덕션에서 안정적
- max_retries=3, request_timeout=10 반드시 명시 (T-012)
- LLM 출력(asset_ids 등)을 tool에 전달 전 validation 필수 (P-009)
- reasoning 모델(gpt-5-mini/nano)은 temperature 미지원 — non-reasoning 모델 사용 (T-023)

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

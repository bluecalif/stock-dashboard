"""LLM 세션 요약 서비스 — gpt-5-nano JSON mode."""

from __future__ import annotations

import json
import logging

from langchain_openai import ChatOpenAI

from config.settings import settings

logger = logging.getLogger(__name__)

_SUMMARIZE_PROMPT = """당신은 투자 분석 대화의 요약 전문가입니다.
아래 대화 내역을 분석하여 JSON 형식으로 요약하세요.

## 출력 형식 (반드시 아래 JSON 구조를 따르세요)
```json
{
  "turn_count": 대화 턴 수(int),
  "categories_used": ["사용된 분석 카테고리 목록"],
  "assets_discussed": ["논의된 자산 ID 목록"],
  "key_findings": ["핵심 발견 1", "핵심 발견 2"],
  "user_intent": "사용자의 주요 의도 요약 (1문장)"
}
```
- JSON만 출력하세요. 다른 텍스트는 포함하지 마세요.
- assets_discussed에는 종목코드(005930 등)나 자산ID(KS200, BTC/KRW 등)를 사용하세요.
"""


async def summarize_session(messages: list[dict[str, str]]) -> dict:
    """대화 메시지를 LLM으로 요약하여 summary_data dict 반환.

    Args:
        messages: [{"role": "user"|"assistant", "content": "..."}, ...]

    Returns:
        요약 데이터 dict (turn_count, categories_used, assets_discussed, key_findings, user_intent)
    """
    conversation = "\n".join(
        f"{'사용자' if m['role'] == 'user' else 'AI'}: {m['content']}"
        for m in messages
        if m.get("content")
    )

    llm = ChatOpenAI(
        model="gpt-5-nano",
        api_key=settings.openai_api_key,
        max_retries=2,
        request_timeout=60,
        model_kwargs={"response_format": {"type": "json_object"}},
    )

    resp = await llm.ainvoke([
        {"role": "system", "content": _SUMMARIZE_PROMPT},
        {"role": "user", "content": f"## 대화 내역\n{conversation}"},
    ])

    try:
        return json.loads(resp.content)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Summarizer JSON parse failed: %s", resp.content[:200])
        return {
            "turn_count": len([m for m in messages if m.get("role") == "user"]),
            "categories_used": [],
            "assets_discussed": [],
            "key_findings": [],
            "user_intent": "요약 생성 실패",
        }

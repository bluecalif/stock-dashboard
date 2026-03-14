"""Chat service — LangGraph 오케스트레이션 + 하이브리드 분류기 + SSE 이벤트 생성."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncGenerator

from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from api.repositories import chat_repo
from api.services.llm.graph import build_graph
from api.services.llm.hybrid.classifier import classify_question
from api.services.llm.hybrid.context import PageContext
from api.services.llm.hybrid.templates import get_template_response
from db.models import ChatSession

logger = logging.getLogger(__name__)

# 그래프 싱글톤 (MemorySaver 유지)
_graph = None


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def create_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    title: str | None = None,
) -> ChatSession:
    """새 채팅 세션 생성."""
    session = chat_repo.create_session(db, user_id=user_id, title=title)
    db.commit()
    return session


def get_session_with_messages(
    db: Session,
    *,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    """세션 + 메시지 조회 (소유권 검증 포함)."""
    session = chat_repo.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session",
        )
    messages = chat_repo.list_messages_by_session(db, session_id)
    return {"session": session, "messages": messages}


def list_sessions(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> list[ChatSession]:
    """사용자의 채팅 세션 목록."""
    return chat_repo.list_sessions_by_user(db, user_id)


def _get_name_map(asset_ids: list[str]) -> dict[str, str]:
    """종목명 매핑 조회 (템플릿 응답용)."""
    from api.repositories import asset_repo
    from db.session import SessionLocal

    db = SessionLocal()
    try:
        return asset_repo.get_name_map(db, asset_ids)
    finally:
        db.close()


def _fetch_hybrid_data(category: str, page_context: PageContext) -> dict | None:
    """하이브리드 분류기가 매칭한 카테고리에 대해 Tool 데이터를 가져온다."""
    from api.services.llm.hybrid.classifier import (
        CORRELATION_EXPLAIN,
        SIMILAR_ASSETS,
        SPREAD_ANALYSIS,
    )

    try:
        if category == CORRELATION_EXPLAIN:
            from api.services.llm.tools import analyze_correlation_tool
            raw = analyze_correlation_tool.invoke({
                "asset_ids": page_context.asset_ids or None,
                "days": page_context.params.get("window", 60),
            })
            data = json.loads(raw)
            # 종목명 매핑 추가
            all_ids = set()
            for g in data.get("groups", []):
                all_ids.update(g.get("asset_ids", []))
            for p in data.get("top_pairs", []):
                all_ids.update([p["asset_a"], p["asset_b"]])
            if all_ids:
                data["name_map"] = _get_name_map(list(all_ids))
            return data

        if category == SIMILAR_ASSETS:
            target = (
                page_context.asset_ids[0]
                if page_context.asset_ids
                else "KS200"
            )
            from api.services.llm.tools import analyze_correlation_tool
            raw = analyze_correlation_tool.invoke({
                "asset_ids": None,
                "target_id": target,
            })
            data = json.loads(raw)
            data["target_id"] = target
            # 종목명 매핑 추가
            all_ids = {target}
            for s in data.get("similar", []):
                all_ids.add(s["asset_id"])
            data["name_map"] = _get_name_map(list(all_ids))
            return data

        if category == SPREAD_ANALYSIS:
            pair = page_context.params.get("selected_pair", [])
            if len(pair) >= 2:
                asset_a, asset_b = pair[0], pair[1]
            elif len(page_context.asset_ids) >= 2:
                asset_a, asset_b = page_context.asset_ids[0], page_context.asset_ids[1]
            else:
                return None  # 페어 정보 없으면 LLM fallback
            from api.services.llm.tools import get_spread
            raw = get_spread.invoke({
                "asset_a": asset_a,
                "asset_b": asset_b,
                "days": page_context.params.get("window", 60),
            })
            data = json.loads(raw)
            data["name_map"] = _get_name_map([asset_a, asset_b])
            return data

    except Exception:
        logger.exception("Hybrid data fetch error for category=%s", category)
        return None

    return None


def _status_event(step: str, message: str) -> str:
    """status SSE 이벤트 생성."""
    evt = {"type": "status", "data": {"step": step, "message": message}}
    return f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"


async def stream_chat(
    db: Session,
    *,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    content: str,
    deep_mode: bool = False,
    page_context: dict | None = None,
    is_nudge: bool = False,
) -> AsyncGenerator[str, None]:
    """하이브리드 분류기 → 템플릿 응답 / LangGraph fallback → SSE 이벤트 스트림."""
    # 세션 소유권 검증
    session = chat_repo.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session",
        )

    # user 메시지 DB 저장
    chat_repo.create_message(db, session_id=session_id, role="user", content=content)
    db.commit()

    ctx = PageContext.from_dict(page_context)
    full_response = ""

    # ── 1) 하이브리드 분류기 시도 ──
    yield _status_event("analyzing", "질문 분석 중...")

    # is_nudge=True → regex 분류 시도, is_nudge=False → 바로 LLM fallback
    if is_nudge:
        category = classify_question(content, ctx)
    else:
        category = None

    # is_nudge인데 분류 실패 시 → 페이지별 기본 카테고리 적용
    if not category and is_nudge:
        from api.services.llm.hybrid.classifier import (
            CORRELATION_EXPLAIN,
            SIMILAR_ASSETS,
        )
        _page_defaults = {
            "correlation": SIMILAR_ASSETS,
            "indicators": CORRELATION_EXPLAIN,
            "strategy": CORRELATION_EXPLAIN,
        }
        category = _page_defaults.get(ctx.page_id, SIMILAR_ASSETS)

    if category:
        yield _status_event("fetching", "데이터 조회 중...")
        data = _fetch_hybrid_data(category, ctx)
        if data:
            result = get_template_response(category, ctx, data)
            if result:
                text, actions = result
                full_response = text

                # 텍스트 스트리밍 (청크 단위)
                for chunk in _chunk_text(text, 80):
                    evt = {"type": "text_delta", "content": chunk}
                    yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"

                # UI 액션 전송
                for action in actions:
                    evt = {"type": "ui_action", **action.to_dict()}
                    yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"

                # DB 저장 + done
                if full_response:
                    chat_repo.create_message(
                        db, session_id=session_id, role="assistant",
                        content=full_response,
                    )
                    db.commit()
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

    # is_nudge인데 여기까지 왔으면 데이터 fetch 실패 → LLM 방지
    if is_nudge:
        fallback_text = "죄송합니다. 데이터를 조회하지 못했습니다. 잠시 후 다시 시도해주세요."
        evt = {"type": "text_delta", "content": fallback_text}
        yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"
        chat_repo.create_message(
            db, session_id=session_id, role="assistant", content=fallback_text,
        )
        db.commit()
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        return

    # ── 2) LangGraph fallback ──
    yield _status_event("thinking", "AI가 생각하고 있어요...")
    graph = _get_graph()
    thread_id = str(session_id)

    try:
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=content)]},
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "deep_mode": deep_mode,
                    "page_context": page_context,
                },
            },
            version="v2",
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    text = chunk.content
                    full_response += text
                    evt = {"type": "text_delta", "content": text}
                    yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"

            elif kind == "on_tool_start":
                evt = {
                    "type": "tool_call",
                    "name": event["name"],
                    "args": event["data"].get("input", {}),
                }
                yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"

            elif kind == "on_tool_end":
                raw_output = event["data"].get("output", "")
                if hasattr(raw_output, "content"):
                    raw_output = raw_output.content
                evt = {
                    "type": "tool_result",
                    "name": event["name"],
                    "data": str(raw_output),
                }
                yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"

    except Exception:
        logger.exception("LangGraph stream error for session %s", session_id)
        evt = {"type": "error", "content": "응답 생성 중 오류가 발생했습니다."}
        yield f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"

    # assistant 메시지 DB 저장
    if full_response:
        chat_repo.create_message(
            db, session_id=session_id, role="assistant", content=full_response,
        )
        db.commit()

    yield f"data: {json.dumps({'type': 'done'})}\n\n"


def _chunk_text(text: str, size: int) -> list[str]:
    """텍스트를 size 글자 단위로 분할 (SSE 스트리밍 시뮬레이션)."""
    return [text[i:i + size] for i in range(0, len(text), size)]

"""Chat service — LangGraph 오케스트레이션 + SSE 이벤트 생성."""

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


async def stream_chat(
    db: Session,
    *,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    content: str,
) -> AsyncGenerator[str, None]:
    """LangGraph 호출 → SSE 이벤트 스트림 생성."""
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

    graph = _get_graph()
    thread_id = str(session_id)
    full_response = ""

    try:
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=content)]},
            config={"configurable": {"thread_id": thread_id}},
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
                evt = {
                    "type": "tool_result",
                    "name": event["name"],
                    "data": event["data"].get("output", ""),
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

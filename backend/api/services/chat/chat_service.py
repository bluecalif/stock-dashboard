"""Chat service — Agentic flow (Classifier → DataFetcher → Reporter) + LangGraph fallback."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncGenerator

from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from api.repositories import chat_repo
from api.services.llm.agentic.classifier import classify_question as llm_classify
from api.services.llm.agentic.data_fetcher import fetch_data
from api.services.llm.agentic.reporter import generate_report
from api.services.llm.agentic.schemas import CuratedReport
from api.services.llm.graph import build_graph
from api.services.llm.hybrid.context import PageContext
from db.models import ChatSession

logger = logging.getLogger(__name__)

# LangGraph 싱글톤 (MemorySaver 유지)
_graph = None

# Confidence threshold — 이 값 미만이면 LangGraph fallback
_CONFIDENCE_THRESHOLD = 0.5


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


# ---------------------------------------------------------------------------
# Session CRUD (변경 없음)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _status_event(step: str, message: str) -> str:
    """status SSE 이벤트 생성."""
    evt = {"type": "status", "data": {"step": step, "message": message}}
    return f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"


def _chunk_text(text: str, size: int) -> list[str]:
    """텍스트를 size 글자 단위로 분할 (SSE 스트리밍 시뮬레이션)."""
    return [text[i:i + size] for i in range(0, len(text), size)]


def _sse(evt: dict) -> str:
    """SSE data line from dict."""
    return f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"


# ---------------------------------------------------------------------------
# Main streaming function
# ---------------------------------------------------------------------------

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
    """Agentic flow → SSE 이벤트 스트림.

    1. LLM Classifier: 질문 분류
    2. confidence >= threshold AND category != general:
       → DataFetcher → LLM Reporter → 구조화된 응답
    3. else: LangGraph fallback (기존 agent+tools 루프)
    """
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

    # ── Step 1: LLM Classifier ──
    yield _status_event("analyzing", "질문 분석 중...")

    classification = await llm_classify(
        question=content,
        current_page=ctx.page_id,
        asset_ids=ctx.asset_ids or None,
        params=ctx.params or None,
    )

    logger.info(
        "Classifier result: category=%s confidence=%.2f target_page=%s",
        classification.category,
        classification.confidence,
        classification.target_page,
    )

    # ── Agentic flow or LangGraph fallback ──
    use_agentic = (
        classification.confidence >= _CONFIDENCE_THRESHOLD
        and classification.category != "general"
    )

    if use_agentic:
        # Navigate 액션 (페이지 이동이 필요한 경우)
        if classification.should_navigate:
            page_path = _page_id_to_path(classification.target_page)
            if page_path:
                yield _sse({
                    "type": "ui_action",
                    "action": "navigate",
                    "payload": {"path": page_path},
                })

        # ── Step 2: DataFetcher ──
        yield _status_event("fetching", "데이터 조회 중...")
        tool_results = await fetch_data(classification)

        # ── Step 3: LLM Reporter ──
        yield _status_event("generating", "분석 리포트 생성 중...")
        report = await generate_report(
            category=classification.category,
            tool_results=tool_results,
            page_id=classification.target_page,
            question=content,
            deep_mode=deep_mode,
        )

        # ── 응답 스트리밍 ──
        full_response = _format_report(report)

        for chunk in _chunk_text(full_response, 80):
            yield _sse({"type": "text_delta", "content": chunk})

        # UI 액션 전송
        for action in report.ui_actions:
            yield _sse({"type": "ui_action", **action.model_dump()})

        # Follow-up 질문 전송
        if report.follow_up_questions:
            yield _sse({
                "type": "follow_up",
                "questions": report.follow_up_questions,
            })

        # DB 저장 + done
        if full_response:
            chat_repo.create_message(
                db, session_id=session_id, role="assistant",
                content=full_response,
            )
            db.commit()
        yield _sse({"type": "done"})
        return

    # ── LangGraph fallback ──
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
                    yield _sse({"type": "text_delta", "content": text})

            elif kind == "on_tool_start":
                yield _sse({
                    "type": "tool_call",
                    "name": event["name"],
                    "args": event["data"].get("input", {}),
                })

            elif kind == "on_tool_end":
                raw_output = event["data"].get("output", "")
                if hasattr(raw_output, "content"):
                    raw_output = raw_output.content
                yield _sse({
                    "type": "tool_result",
                    "name": event["name"],
                    "data": str(raw_output),
                })

    except Exception:
        logger.exception("LangGraph stream error for session %s", session_id)
        yield _sse({"type": "error", "content": "응답 생성 중 오류가 발생했습니다."})

    # assistant 메시지 DB 저장
    if full_response:
        chat_repo.create_message(
            db, session_id=session_id, role="assistant", content=full_response,
        )
        db.commit()

    yield _sse({"type": "done"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_report(report: CuratedReport) -> str:
    """CuratedReport를 텍스트로 포매팅."""
    parts = [report.summary, "", report.analysis]
    if report.verdict:
        parts.extend(["", f"> {report.verdict}"])
    return "\n".join(parts)


def _page_id_to_path(page_id: str) -> str | None:
    """page_id → React Router 경로."""
    mapping = {
        "prices": "/prices",
        "correlation": "/correlation",
        "indicators": "/indicators",
        "strategy": "/strategy",
        "home": "/",
    }
    return mapping.get(page_id)

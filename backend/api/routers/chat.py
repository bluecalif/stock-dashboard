"""Chat endpoints — 세션 CRUD + SSE 메시지 스트리밍."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.schemas.chat import (
    CreateSessionRequest,
    MessageResponse,
    SendMessageRequest,
    SessionDetailResponse,
    SessionResponse,
)
from api.services.chat import chat_service
from api.services.llm.hybrid.templates import get_nudge_questions
from db.models import User

router = APIRouter(prefix="/v1/chat", tags=["chat"])


@router.post(
    "/sessions",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    body: CreateSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionResponse:
    session = chat_service.create_session(db, user_id=current_user.id, title=body.title)
    return SessionResponse.model_validate(session)


@router.get("/sessions", response_model=list[SessionResponse])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[SessionResponse]:
    sessions = chat_service.list_sessions(db, user_id=current_user.id)
    return [SessionResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=SessionDetailResponse)
def get_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SessionDetailResponse:
    result = chat_service.get_session_with_messages(
        db, session_id=session_id, user_id=current_user.id,
    )
    session_resp = SessionDetailResponse.model_validate(result["session"])
    session_resp.messages = [MessageResponse.model_validate(m) for m in result["messages"]]
    return session_resp


@router.post("/sessions/{session_id}/messages")
async def send_message(
    session_id: uuid.UUID,
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    page_ctx = body.page_context.model_dump() if body.page_context else None
    event_stream = chat_service.stream_chat(
        db,
        session_id=session_id,
        user_id=current_user.id,
        content=body.content,
        deep_mode=body.deep_mode,
        page_context=page_ctx,
    )
    return StreamingResponse(event_stream, media_type="text/event-stream")


@router.get("/nudge-questions")
def nudge_questions(
    page_id: str = Query(default="home", description="현재 페이지 ID"),
    _current_user: User = Depends(get_current_user),
) -> dict[str, list[str]]:
    """Return nudge questions for the current page context."""
    return {"questions": get_nudge_questions(page_id)}

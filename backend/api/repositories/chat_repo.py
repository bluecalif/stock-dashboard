"""Chat repository."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from db.models import ChatMessage, ChatSession


def create_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    title: str | None = None,
) -> ChatSession:
    """채팅 세션 생성."""
    session = ChatSession(user_id=user_id, title=title)
    db.add(session)
    db.flush()
    return session


def get_session(db: Session, session_id: uuid.UUID) -> ChatSession | None:
    """ID로 채팅 세션 조회."""
    return db.query(ChatSession).filter(ChatSession.id == session_id).first()


def list_sessions_by_user(
    db: Session,
    user_id: uuid.UUID,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[ChatSession]:
    """사용자별 채팅 세션 목록 (최신순)."""
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def create_message(
    db: Session,
    *,
    session_id: uuid.UUID,
    role: str,
    content: str | None = None,
    tool_payload: dict | None = None,
    token_count: int | None = None,
) -> ChatMessage:
    """채팅 메시지 저장."""
    msg = ChatMessage(
        session_id=session_id,
        role=role,
        content=content,
        tool_payload=tool_payload,
        token_count=token_count,
    )
    db.add(msg)
    db.flush()
    return msg


def list_messages_by_session(
    db: Session,
    session_id: uuid.UUID,
) -> list[ChatMessage]:
    """세션의 전체 메시지 (시간순)."""
    return (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

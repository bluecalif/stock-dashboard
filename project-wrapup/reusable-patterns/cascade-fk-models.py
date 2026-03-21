"""
## 용도
SQLAlchemy 2.0 CASCADE FK + UUID PK + Mapped 타입 패턴.
User 삭제 시 관련 데이터(세션, 채팅, 프로필) 자동 정리.

## 사용법
1. User 테이블 정의 (UUID PK, is_active, created_at, updated_at)
2. 관련 테이블에 ForeignKey(..., ondelete="CASCADE") 설정
3. user 삭제 시 관련 데이터 자동 삭제 — 별도 삭제 로직 불필요

## 출처
stock-dashboard/backend/db/models.py
"""

import uuid

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Index, String, Text, JSON,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (Index("ix_users_email", "email"),)


class UserSession(Base):
    __tablename__ = "user_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    refresh_token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at = mapped_column(DateTime(timezone=True), nullable=False)
    __table_args__ = (
        Index("ix_user_sessions_user_id", "user_id"),
        Index("ix_user_sessions_expires", "expires_at"),
    )


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"),
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    __table_args__ = (Index("ix_chat_sessions_user_id", "user_id"),)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"),
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_payload = mapped_column(JSON, nullable=True)
    __table_args__ = (Index("ix_chat_messages_session_id", "session_id"),)

# User 삭제 → UserSession, ChatSession → ChatMessage 자동 삭제

"""
## 용도
SQLAlchemy 2.0 CASCADE FK + UUID PK + Mapped 타입 패턴.
User 삭제 시 관련 데이터(세션, 채팅, 프로필) 자동 CASCADE 정리.
수정 필요 (테이블명/컬럼 교체).

## 언제 쓰는가
사용자→세션→메시지 같은 소유 관계가 있고, 상위 엔티티 삭제 시 하위를 자동 정리할 때.
회원 탈퇴 기능에서 수동 삭제 로직을 최소화하고 싶을 때.

## 전제조건
- PostgreSQL (CASCADE FK 지원)
- SQLAlchemy 2.0+ (Mapped, mapped_column 사용)
- Alembic 마이그레이션 설정

## 의존성
- sqlalchemy: DeclarativeBase, Mapped, mapped_column, ForeignKey
- sqlalchemy.dialects.postgresql: UUID
- uuid: Python 표준 라이브러리

## 통합 포인트
- db/models.py에 배치
- Alembic 마이그레이션으로 테이블 생성
- Repository 레이어에서 User 삭제 시 db.query(User).delete() 한 번으로 전체 정리

## 주의사항
- CASCADE는 DB 레벨에서 동작 — SQLAlchemy relationship의 cascade와 혼동 주의
- 대용량 데이터 CASCADE 삭제 시 잠금 시간 주의. 배치 삭제 검토
- UUID PK는 인덱스 성능이 정수 PK보다 느림 — 성능 민감 시 트레이드오프 고려

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

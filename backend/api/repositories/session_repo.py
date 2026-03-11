"""User session (refresh token) repository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from db.models import UserSession


def create_session(
    db: Session,
    *,
    user_id: UUID,
    refresh_token_hash: str,
    expires_at: datetime,
) -> UserSession:
    session = UserSession(
        user_id=user_id,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at,
    )
    db.add(session)
    db.flush()
    return session


def get_by_token_hash(db: Session, token_hash: str) -> UserSession | None:
    return (
        db.query(UserSession)
        .filter(
            UserSession.refresh_token_hash == token_hash,
            UserSession.expires_at > datetime.now(timezone.utc),
        )
        .first()
    )


def delete_session(db: Session, session_id: UUID) -> None:
    db.query(UserSession).filter(UserSession.id == session_id).delete()


def delete_expired(db: Session) -> int:
    count = (
        db.query(UserSession)
        .filter(UserSession.expires_at <= datetime.now(timezone.utc))
        .delete()
    )
    return count

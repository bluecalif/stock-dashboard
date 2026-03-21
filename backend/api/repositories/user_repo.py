"""User repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from db.models import User


def create_user(
    db: Session, *, email: str, password_hash: str, nickname: str | None = None,
) -> User:
    user = User(email=email, password_hash=password_hash, nickname=nickname)
    db.add(user)
    db.flush()
    return user


def get_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def get_by_id(db: Session, user_id: UUID) -> User | None:
    return db.query(User).filter(User.id == user_id).first()


def delete_user(db: Session, user_id: UUID) -> None:
    db.query(User).filter(User.id == user_id).delete()
    db.flush()

"""Tests for chat_repo summary CRUD (ConversationSummary)."""

import uuid

import pytest

from api.repositories import chat_repo
from db.models import ChatSession, ConversationSummary, User


@pytest.fixture()
def seed_user(db):
    user = User(
        id=uuid.uuid4(),
        email="summary@example.com",
        password_hash="hashed",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


@pytest.fixture()
def seed_session(db, seed_user):
    session = ChatSession(user_id=seed_user.id, title="Test Session")
    db.add(session)
    db.commit()
    return session


class TestUpsertSummary:
    def test_creates_new(self, db, seed_session):
        data = {"turn_count": 5, "key_findings": ["BTC 상승"]}
        result = chat_repo.upsert_summary(
            db, session_id=seed_session.id, summary_data=data,
        )
        assert result.session_id == seed_session.id
        assert result.summary_data["turn_count"] == 5

    def test_updates_existing(self, db, seed_session):
        chat_repo.upsert_summary(
            db, session_id=seed_session.id,
            summary_data={"turn_count": 5},
        )
        db.commit()

        result = chat_repo.upsert_summary(
            db, session_id=seed_session.id,
            summary_data={"turn_count": 10, "user_intent": "분석 요청"},
        )
        assert result.summary_data["turn_count"] == 10
        assert result.summary_data["user_intent"] == "분석 요청"
        count = db.query(ConversationSummary).count()
        assert count == 1


class TestGetRecentSummaries:
    def test_returns_empty(self, db, seed_user):
        result = chat_repo.get_recent_summaries(db, seed_user.id)
        assert result == []

    def test_returns_by_user(self, db, seed_user):
        # 3개 세션 + 요약 생성
        for i in range(3):
            s = ChatSession(user_id=seed_user.id, title=f"Session {i}")
            db.add(s)
            db.flush()
            db.add(ConversationSummary(
                session_id=s.id,
                summary_data={"turn_count": (i + 1) * 5},
            ))
        db.commit()

        result = chat_repo.get_recent_summaries(db, seed_user.id, limit=2)
        assert len(result) == 2

    def test_excludes_other_users(self, db, seed_user):
        other = User(
            id=uuid.uuid4(), email="other@example.com",
            password_hash="h", is_active=True,
        )
        db.add(other)
        db.flush()

        s1 = ChatSession(user_id=seed_user.id, title="Mine")
        s2 = ChatSession(user_id=other.id, title="Others")
        db.add_all([s1, s2])
        db.flush()
        db.add(ConversationSummary(session_id=s1.id, summary_data={"a": 1}))
        db.add(ConversationSummary(session_id=s2.id, summary_data={"b": 2}))
        db.commit()

        result = chat_repo.get_recent_summaries(db, seed_user.id)
        assert len(result) == 1
        assert result[0].summary_data == {"a": 1}

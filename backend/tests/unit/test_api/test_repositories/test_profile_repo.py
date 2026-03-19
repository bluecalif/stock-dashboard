"""Tests for profile_repo — UserProfile & UserActivity CRUD."""

import uuid

import pytest

from api.repositories import profile_repo
from db.models import User, UserActivity, UserProfile


@pytest.fixture()
def seed_user(db):
    """Insert a test user for FK references."""
    user = User(
        id=uuid.uuid4(),
        email="test@example.com",
        password_hash="hashed",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


# ── UserProfile ────────────────────────────────────────────────


class TestGetProfile:
    def test_returns_none_when_empty(self, db, seed_user):
        result = profile_repo.get_profile(db, seed_user.id)
        assert result is None

    def test_returns_profile(self, db, seed_user):
        db.add(UserProfile(user_id=seed_user.id, experience_level="beginner"))
        db.commit()
        result = profile_repo.get_profile(db, seed_user.id)
        assert result is not None
        assert result.experience_level == "beginner"


class TestUpsertProfile:
    def test_creates_when_missing(self, db, seed_user):
        result = profile_repo.upsert_profile(
            db, user_id=seed_user.id, experience_level="expert",
        )
        assert result.user_id == seed_user.id
        assert result.experience_level == "expert"

    def test_updates_when_exists(self, db, seed_user):
        profile_repo.upsert_profile(db, user_id=seed_user.id, experience_level="beginner")
        db.commit()
        result = profile_repo.upsert_profile(
            db, user_id=seed_user.id, experience_level="expert",
        )
        assert result.experience_level == "expert"
        # 단일 레코드만 존재
        count = db.query(UserProfile).count()
        assert count == 1


class TestSaveIceBreaking:
    def test_saves_all_fields(self, db, seed_user):
        result = profile_repo.save_ice_breaking(
            db,
            user_id=seed_user.id,
            experience_level="intermediate",
            decision_style="logic",
            raw_answers={"q1": "intermediate", "q2": "logic"},
        )
        assert result.experience_level == "intermediate"
        assert result.decision_style == "logic"
        assert result.onboarding_completed is True
        assert result.ice_breaking_raw == {"q1": "intermediate", "q2": "logic"}


# ── UserActivity ───────────────────────────────────────────────


class TestGetActivity:
    def test_returns_none_when_empty(self, db, seed_user):
        result = profile_repo.get_activity(db, seed_user.id)
        assert result is None


class TestEnsureActivity:
    def test_creates_when_missing(self, db, seed_user):
        result = profile_repo._ensure_activity(db, seed_user.id)
        assert result.user_id == seed_user.id
        assert result.activity_data == {}

    def test_returns_existing(self, db, seed_user):
        db.add(UserActivity(user_id=seed_user.id, activity_data={"total_questions": 5}))
        db.commit()
        result = profile_repo._ensure_activity(db, seed_user.id)
        assert result.activity_data["total_questions"] == 5
        count = db.query(UserActivity).count()
        assert count == 1

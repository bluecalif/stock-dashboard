"""Tests for profile router — 4 endpoints."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.main import app


def _make_user(user_id=None):
    u = MagicMock()
    u.id = user_id or uuid.uuid4()
    u.email = "test@example.com"
    u.is_active = True
    return u


def _make_profile(user_id, **overrides):
    import datetime
    defaults = {
        "user_id": user_id,
        "experience_level": None,
        "decision_style": None,
        "onboarding_completed": False,
        "preferred_depth": "brief",
        "top_assets": None,
        "top_categories": None,
        "updated_at": datetime.datetime(2026, 3, 19, tzinfo=datetime.timezone.utc),
    }
    defaults.update(overrides)
    m = MagicMock()
    for k, v in defaults.items():
        setattr(m, k, v)
    return m


def _make_activity(user_id, activity_data=None):
    import datetime
    m = MagicMock()
    m.user_id = user_id
    m.activity_data = activity_data or {}
    m.updated_at = datetime.datetime(2026, 3, 19, tzinfo=datetime.timezone.utc)
    return m


@pytest.fixture()
def fake_user():
    return _make_user()


@pytest.fixture()
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture()
def client(mock_db, fake_user):
    def _override_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


# ── GET /v1/profile ────────────────────────────────────────────


class TestGetProfile:
    @patch("api.routers.profile.profile_repo")
    def test_returns_profile(self, mock_repo, client, fake_user):
        mock_repo.upsert_profile.return_value = _make_profile(fake_user.id)
        resp = client.get("/v1/profile")
        assert resp.status_code == 200
        data = resp.json()
        assert data["onboarding_completed"] is False
        assert data["preferred_depth"] == "brief"

    @patch("api.routers.profile.profile_repo")
    def test_creates_lazy_profile(self, mock_repo, client, fake_user):
        mock_repo.upsert_profile.return_value = _make_profile(fake_user.id)
        client.get("/v1/profile")
        mock_repo.upsert_profile.assert_called_once()


# ── POST /v1/profile/ice-breaking ──────────────────────────────


class TestIceBreaking:
    @patch("api.routers.profile.profile_repo")
    def test_submit_success(self, mock_repo, client, fake_user):
        mock_repo.save_ice_breaking.return_value = _make_profile(
            fake_user.id,
            experience_level="beginner",
            decision_style="logic",
            onboarding_completed=True,
        )
        resp = client.post("/v1/profile/ice-breaking", json={
            "experience_level": "beginner",
            "decision_style": "logic",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["experience_level"] == "beginner"
        assert data["decision_style"] == "logic"
        assert data["onboarding_completed"] is True

    def test_invalid_experience_level(self, client):
        resp = client.post("/v1/profile/ice-breaking", json={
            "experience_level": "invalid",
            "decision_style": "logic",
        })
        assert resp.status_code == 422

    def test_missing_field(self, client):
        resp = client.post("/v1/profile/ice-breaking", json={
            "experience_level": "beginner",
        })
        assert resp.status_code == 422


# ── GET /v1/profile/activity ───────────────────────────────────


class TestGetActivity:
    @patch("api.routers.profile.profile_repo")
    def test_returns_activity(self, mock_repo, client, fake_user):
        mock_repo.get_activity.return_value = _make_activity(
            fake_user.id, {"total_questions": 10},
        )
        resp = client.get("/v1/profile/activity")
        assert resp.status_code == 200
        assert resp.json()["activity_data"]["total_questions"] == 10

    @patch("api.routers.profile.profile_repo")
    def test_creates_when_empty(self, mock_repo, client, fake_user):
        mock_repo.get_activity.return_value = None
        mock_repo._ensure_activity.return_value = _make_activity(fake_user.id)
        resp = client.get("/v1/profile/activity")
        assert resp.status_code == 200
        assert resp.json()["activity_data"] == {}


# ── POST /v1/profile/activity/page-visit ───────────────────────


class TestPageVisit:
    @patch("api.routers.profile.profile_repo")
    def test_records_visit(self, mock_repo, client, fake_user):
        mock_repo.record_page_visit.return_value = _make_activity(
            fake_user.id, {"page_visits": {"prices": 1}},
        )
        resp = client.post("/v1/profile/activity/page-visit", json={
            "page_id": "prices",
        })
        assert resp.status_code == 200
        assert resp.json()["activity_data"]["page_visits"]["prices"] == 1

    def test_missing_page_id(self, client):
        resp = client.post("/v1/profile/activity/page-visit", json={})
        assert resp.status_code == 422


# ── Auth 미인증 ────────────────────────────────────────────────


class TestUnauthorized:
    def test_get_profile_no_auth(self):
        """인증 없이 접근 시 401."""
        app.dependency_overrides.clear()
        c = TestClient(app, raise_server_exceptions=False)
        resp = c.get("/v1/profile")
        assert resp.status_code == 401

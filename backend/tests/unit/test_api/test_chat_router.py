"""Tests for chat router endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from api.main import app


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture
def fake_user():
    u = MagicMock()
    u.id = uuid.uuid4()
    u.email = "chat@example.com"
    u.nickname = "chatter"
    u.is_active = True
    u.created_at = datetime.now(timezone.utc)
    return u


@pytest.fixture
def client(mock_db, fake_user):
    from api.dependencies import get_current_user, get_db

    def _override_db():
        yield mock_db

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.clear()


def _make_session_mock(user_id, session_id=None, title="Test"):
    s = MagicMock()
    s.id = session_id or uuid.uuid4()
    s.user_id = user_id
    s.title = title
    s.created_at = datetime.now(timezone.utc)
    s.updated_at = datetime.now(timezone.utc)
    return s


def _make_message_mock(session_id, role="user", content="hello"):
    m = MagicMock()
    m.id = uuid.uuid4()
    m.session_id = session_id
    m.role = role
    m.content = content
    m.tool_payload = None
    m.token_count = None
    m.created_at = datetime.now(timezone.utc)
    return m


# --- POST /v1/chat/sessions ---


@patch("api.routers.chat.chat_service")
def test_create_session(mock_service, client, fake_user):
    fake = _make_session_mock(fake_user.id, title="New Chat")
    mock_service.create_session.return_value = fake

    resp = client.post("/v1/chat/sessions", json={"title": "New Chat"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "New Chat"
    assert "id" in data


@patch("api.routers.chat.chat_service")
def test_create_session_no_title(mock_service, client, fake_user):
    fake = _make_session_mock(fake_user.id, title=None)
    mock_service.create_session.return_value = fake

    resp = client.post("/v1/chat/sessions", json={})
    assert resp.status_code == 201


# --- GET /v1/chat/sessions ---


@patch("api.routers.chat.chat_service")
def test_list_sessions(mock_service, client, fake_user):
    mock_service.list_sessions.return_value = [
        _make_session_mock(fake_user.id, title="Session 1"),
    ]
    resp = client.get("/v1/chat/sessions")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1


# --- GET /v1/chat/sessions/{id} ---


@patch("api.routers.chat.chat_service")
def test_get_session_detail(mock_service, client, fake_user):
    sid = uuid.uuid4()
    fake = _make_session_mock(fake_user.id, session_id=sid)
    msg = _make_message_mock(sid, role="user", content="hello")

    mock_service.get_session_with_messages.return_value = {
        "session": fake,
        "messages": [msg],
    }

    resp = client.get(f"/v1/chat/sessions/{sid}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["messages"]) == 1
    assert data["messages"][0]["role"] == "user"


# --- POST /v1/chat/sessions/{id}/messages ---


@patch("api.routers.chat.chat_service")
def test_send_message_returns_sse(mock_service, client, fake_user):
    sid = uuid.uuid4()

    async def fake_stream(*args, **kwargs):
        yield 'data: {"type": "text_delta", "content": "Hi"}\n\n'
        yield 'data: {"type": "done"}\n\n'

    mock_service.stream_chat.return_value = fake_stream()

    resp = client.post(
        f"/v1/chat/sessions/{sid}/messages",
        json={"content": "hello"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    body = resp.text
    assert "text_delta" in body
    assert "done" in body


# --- 인증 없이 접근 ---


def test_no_auth_returns_401():
    """인증 없이 접근 시 401."""
    app.dependency_overrides.clear()
    raw_client = TestClient(app, raise_server_exceptions=False)
    resp = raw_client.post("/v1/chat/sessions", json={})
    assert resp.status_code == 401

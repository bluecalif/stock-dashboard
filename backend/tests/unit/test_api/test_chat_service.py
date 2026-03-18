"""Tests for chat_service — 세션 CRUD, stream_chat (LLM mock)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.services.chat.chat_service import (
    create_session,
    get_session_with_messages,
    list_sessions,
    stream_chat,
)


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


def _make_session(user_id=None, session_id=None, title="Test"):
    s = MagicMock()
    s.id = session_id or uuid.uuid4()
    s.user_id = user_id or uuid.uuid4()
    s.title = title
    return s


# --- create_session ---


@patch("api.services.chat.chat_service.chat_repo")
def test_create_session_success(mock_repo, mock_db):
    uid = uuid.uuid4()
    fake = _make_session(user_id=uid)
    mock_repo.create_session.return_value = fake

    result = create_session(mock_db, user_id=uid, title="Hello")
    assert result == fake
    mock_repo.create_session.assert_called_once_with(
        mock_db, user_id=uid, title="Hello",
    )
    mock_db.commit.assert_called_once()


# --- get_session_with_messages ---


@patch("api.services.chat.chat_service.chat_repo")
def test_get_session_not_found(mock_repo, mock_db):
    mock_repo.get_session.return_value = None
    with pytest.raises(HTTPException) as exc_info:
        get_session_with_messages(mock_db, session_id=uuid.uuid4(), user_id=uuid.uuid4())
    assert exc_info.value.status_code == 404


@patch("api.services.chat.chat_service.chat_repo")
def test_get_session_forbidden(mock_repo, mock_db):
    owner = uuid.uuid4()
    other = uuid.uuid4()
    fake = _make_session(user_id=owner)
    mock_repo.get_session.return_value = fake

    with pytest.raises(HTTPException) as exc_info:
        get_session_with_messages(mock_db, session_id=fake.id, user_id=other)
    assert exc_info.value.status_code == 403


@patch("api.services.chat.chat_service.chat_repo")
def test_get_session_success(mock_repo, mock_db):
    uid = uuid.uuid4()
    fake = _make_session(user_id=uid)
    mock_repo.get_session.return_value = fake
    mock_repo.list_messages_by_session.return_value = []

    result = get_session_with_messages(mock_db, session_id=fake.id, user_id=uid)
    assert result["session"] == fake
    assert result["messages"] == []


# --- list_sessions ---


@patch("api.services.chat.chat_service.chat_repo")
def test_list_sessions(mock_repo, mock_db):
    uid = uuid.uuid4()
    mock_repo.list_sessions_by_user.return_value = [_make_session(user_id=uid)]

    result = list_sessions(mock_db, user_id=uid)
    assert len(result) == 1
    mock_repo.list_sessions_by_user.assert_called_once_with(mock_db, uid)


# --- stream_chat ---


@patch("api.services.chat.chat_service.chat_repo")
async def test_stream_chat_session_not_found(mock_repo, mock_db):
    mock_repo.get_session.return_value = None
    with pytest.raises(HTTPException) as exc_info:
        gen = stream_chat(
            mock_db, session_id=uuid.uuid4(), user_id=uuid.uuid4(), content="hi",
        )
        await gen.__anext__()
    assert exc_info.value.status_code == 404


@patch("api.services.chat.chat_service.chat_repo")
async def test_stream_chat_forbidden(mock_repo, mock_db):
    owner = uuid.uuid4()
    other = uuid.uuid4()
    fake = _make_session(user_id=owner)
    mock_repo.get_session.return_value = fake

    with pytest.raises(HTTPException) as exc_info:
        gen = stream_chat(
            mock_db, session_id=fake.id, user_id=other, content="hi",
        )
        await gen.__anext__()
    assert exc_info.value.status_code == 403


@patch("api.services.chat.chat_service._get_graph")
@patch("api.services.chat.chat_service.chat_repo")
async def test_stream_chat_success(mock_repo, mock_graph, mock_db):
    uid = uuid.uuid4()
    fake = _make_session(user_id=uid)
    mock_repo.get_session.return_value = fake

    # Mock LangGraph astream_events
    mock_event = {
        "event": "on_chat_model_stream",
        "data": {"chunk": MagicMock(content="안녕하세요")},
    }

    async def fake_stream(*args, **kwargs):
        yield mock_event

    graph_instance = MagicMock()
    graph_instance.astream_events = fake_stream
    mock_graph.return_value = graph_instance

    events = []
    gen = stream_chat(mock_db, session_id=fake.id, user_id=uid, content="hello")
    async for event in gen:
        events.append(event)

    # status(analyzing) + status(thinking) + text_delta + follow_up + done
    assert len(events) == 5
    assert '"status"' in events[0]
    assert '"status"' in events[1]
    assert '"text_delta"' in events[2]
    assert '"follow_up"' in events[3]
    assert '"done"' in events[4]

    # user 메시지 + assistant 메시지 저장
    assert mock_repo.create_message.call_count == 2

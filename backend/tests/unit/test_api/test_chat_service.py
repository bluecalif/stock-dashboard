"""Tests for chat_service — 세션 CRUD, stream_chat (LLM mock)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.services.chat.chat_service import (
    _default_follow_ups,
    _dynamic_follow_ups,
    create_session,
    get_session_with_messages,
    list_sessions,
    stream_chat,
)
from api.services.chat.user_context import UserContext


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


@patch("api.services.chat.chat_service.profile_repo")
@patch("api.services.chat.chat_service.build_user_context")
@patch("api.services.chat.chat_service.llm_classify")
@patch("api.services.chat.chat_service._get_graph")
@patch("api.services.chat.chat_service.chat_repo")
async def test_stream_chat_success(
    mock_repo, mock_graph, mock_classify, mock_build_ctx, mock_profile_repo, mock_db,
):
    uid = uuid.uuid4()
    fake = _make_session(user_id=uid)
    mock_repo.get_session.return_value = fake

    # Mock UserContext — build_user_context가 None 반환 시 _ctx_block=None → LangGraph fallback
    mock_build_ctx.side_effect = Exception("no profile")

    # Mock Classifier — general + low confidence → LangGraph fallback
    mock_classification = MagicMock()
    mock_classification.category = "general"
    mock_classification.confidence = 0.3
    mock_classification.target_page = "home"
    mock_classification.should_navigate = False
    mock_classification.asset_ids = []
    mock_classify.return_value = mock_classification

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


# --- stream_chat: unsupported category ---


@patch("api.services.chat.chat_service.profile_repo")
@patch("api.services.chat.chat_service.build_user_context")
@patch("api.services.chat.chat_service.llm_classify")
@patch("api.services.chat.chat_service.chat_repo")
async def test_stream_chat_unsupported(
    mock_repo, mock_classify, mock_build_ctx, mock_profile_repo, mock_db,
):
    """unsupported 카테고리 → 안내 메시지 + follow_up + done."""
    uid = uuid.uuid4()
    fake = _make_session(user_id=uid)
    mock_repo.get_session.return_value = fake

    mock_build_ctx.side_effect = Exception("no profile")

    mock_classification = MagicMock()
    mock_classification.category = "unsupported"
    mock_classification.confidence = 0.9
    mock_classification.target_page = "home"
    mock_classification.should_navigate = False
    mock_classification.asset_ids = []
    mock_classify.return_value = mock_classification

    events = []
    gen = stream_chat(
        mock_db, session_id=fake.id, user_id=uid,
        content="오늘 날씨 어때?",
    )
    async for event in gen:
        events.append(event)

    # status(analyzing) + text_delta(안내 메시지) + follow_up + done
    assert any('"status"' in e for e in events)
    assert any('"text_delta"' in e for e in events)
    assert any('"follow_up"' in e for e in events)
    assert any('"done"' in e for e in events)

    # 안내 메시지에 핵심 문구 포함
    text_events = [e for e in events if '"text_delta"' in e]
    combined = "".join(text_events)
    assert "분석 범위를 벗어납니다" in combined

    # assistant 메시지 DB 저장
    calls = mock_repo.create_message.call_args_list
    roles = [c.kwargs.get("role") or c[1].get("role") for c in calls]
    assert "assistant" in roles


# --- _dynamic_follow_ups ---


class TestDynamicFollowUps:
    """_dynamic_follow_ups 단위 테스트."""

    def test_none_context_returns_defaults(self):
        """UserContext=None → _default_follow_ups fallback."""
        result = _dynamic_follow_ups("prices", None)
        assert result == _default_follow_ups("prices")

    def test_beginner_prices_with_top_assets(self):
        """beginner + prices 페이지 + top_assets → 자산 이름 포함 질문."""
        ctx = UserContext(
            experience_level="beginner",
            decision_style="cautious",
            top_assets=["005930", "KS200"],
            top_categories=[],
            total_questions=5,
        )
        result = _dynamic_follow_ups("prices", ctx)
        assert len(result) <= 3
        assert any("삼성전자" in q for q in result)

    def test_beginner_correlation(self):
        """beginner + correlation → 쉬운 설명 질문."""
        ctx = UserContext(
            experience_level="beginner",
            decision_style="cautious",
            top_assets=[],
            top_categories=[],
            total_questions=2,
        )
        result = _dynamic_follow_ups("correlation", ctx)
        assert any("쉽게" in q for q in result)

    def test_expert_indicators(self):
        """expert + indicators → MACD/RSI 고급 질문."""
        ctx = UserContext(
            experience_level="expert",
            decision_style="data_driven",
            top_assets=["SOXL"],
            top_categories=[],
            total_questions=50,
        )
        result = _dynamic_follow_ups("indicators", ctx)
        assert any("MACD" in q or "RSI" in q for q in result)

    def test_expert_strategy(self):
        """expert + strategy → Sharpe 비율 질문."""
        ctx = UserContext(
            experience_level="expert",
            decision_style="data_driven",
            top_assets=[],
            top_categories=[],
            total_questions=30,
        )
        result = _dynamic_follow_ups("strategy", ctx)
        assert any("Sharpe" in q for q in result)

    def test_max_three_questions(self):
        """결과는 최대 3개."""
        ctx = UserContext(
            experience_level="beginner",
            decision_style="cautious",
            top_assets=["005930", "KS200", "SOXL"],
            top_categories=[],
            total_questions=10,
        )
        result = _dynamic_follow_ups("prices", ctx)
        assert len(result) <= 3

    def test_unknown_page_fills_defaults(self):
        """알 수 없는 page_id → 기본 질문으로 보충."""
        ctx = UserContext(
            experience_level="beginner",
            decision_style="cautious",
            top_assets=[],
            top_categories=[],
            total_questions=1,
        )
        result = _dynamic_follow_ups("unknown_page", ctx)
        assert len(result) >= 1

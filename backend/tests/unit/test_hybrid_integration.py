"""Tests for chat_service agentic flow integration.

- stream_chat() agentic 경로 테스트
- LangGraph fallback 테스트
- graph.py _build_system_prompt 테스트
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.services.chat.chat_service import _chunk_text, stream_chat
from api.services.llm.agentic.schemas import (
    ClassificationResult,
    CuratedReport,
    UIActionModel,
)
from api.services.llm.graph import _build_system_prompt

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


def _make_session(user_id=None, session_id=None):
    s = MagicMock()
    s.id = session_id or uuid.uuid4()
    s.user_id = user_id or uuid.uuid4()
    s.title = "Test"
    return s


# ---------------------------------------------------------------------------
# _build_system_prompt
# ---------------------------------------------------------------------------

class TestBuildSystemPrompt:
    def test_no_context(self):
        from api.services.llm.prompts import SYSTEM_PROMPT
        assert _build_system_prompt(None) == SYSTEM_PROMPT

    def test_with_page_context(self):
        result = _build_system_prompt({
            "page_id": "correlation",
            "asset_ids": ["KS200", "005930"],
            "params": {"window": 60},
        })
        assert "correlation" in result
        assert "KS200" in result
        assert "window" in result

    def test_empty_context(self):
        from api.services.llm.prompts import SYSTEM_PROMPT
        result = _build_system_prompt({"page_id": "home"})
        assert SYSTEM_PROMPT in result
        assert "home" in result


# ---------------------------------------------------------------------------
# _chunk_text
# ---------------------------------------------------------------------------

class TestChunkText:
    def test_short_text(self):
        assert _chunk_text("hello", 80) == ["hello"]

    def test_long_text(self):
        text = "a" * 200
        chunks = _chunk_text(text, 80)
        assert len(chunks) == 3
        assert len(chunks[0]) == 80
        assert len(chunks[1]) == 80
        assert len(chunks[2]) == 40

    def test_empty_text(self):
        assert _chunk_text("", 80) == []


# ---------------------------------------------------------------------------
# stream_chat — agentic 경로
# ---------------------------------------------------------------------------

class TestStreamChatAgentic:
    @patch("api.services.chat.chat_service.chat_repo")
    async def test_session_not_found(self, mock_repo, mock_db):
        mock_repo.get_session.return_value = None
        with pytest.raises(HTTPException) as exc_info:
            gen = stream_chat(
                mock_db,
                session_id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                content="hi",
            )
            await gen.__anext__()
        assert exc_info.value.status_code == 404

    @patch("api.services.chat.chat_service.generate_report")
    @patch("api.services.chat.chat_service.fetch_data")
    @patch("api.services.chat.chat_service.llm_classify")
    @patch("api.services.chat.chat_service.chat_repo")
    async def test_agentic_path_returns_report(
        self, mock_repo, mock_classify, mock_fetch, mock_report, mock_db,
    ):
        """Classifier 높은 confidence → DataFetcher → Reporter 경로."""
        uid = uuid.uuid4()
        fake = _make_session(user_id=uid)
        mock_repo.get_session.return_value = fake

        mock_classify.return_value = ClassificationResult(
            target_page="correlation",
            should_navigate=False,
            category="similar_assets",
            required_tools=["analyze_correlation_tool"],
            asset_ids=["KS200"],
            params={},
            confidence=0.9,
        )
        mock_fetch.return_value = {"analyze_correlation_tool": {}, "name_map": {}}
        mock_report.return_value = CuratedReport(
            summary="유사 자산 분석 결과입니다.",
            analysis="## 유사 자산\n\nKS200과 유사한 자산 목록",
            ui_actions=[
                UIActionModel(
                    action="highlight_pair",
                    payload={"asset_a": "KS200", "asset_b": "005930"},
                ),
            ],
            follow_up_questions=["스프레드도 볼까요?"],
        )

        events = []
        gen = stream_chat(
            mock_db,
            session_id=fake.id,
            user_id=uid,
            content="유사 자산 추천해줘",
            page_context={"page_id": "correlation", "asset_ids": ["KS200"], "params": {}},
        )
        async for event in gen:
            events.append(event)

        event_types = []
        for e in events:
            data = json.loads(e.replace("data: ", "").strip())
            event_types.append(data["type"])

        assert "status" in event_types  # analyzing, fetching, generating
        assert "text_delta" in event_types
        assert "ui_action" in event_types
        assert "follow_up" in event_types
        assert event_types[-1] == "done"

        # assistant 메시지 DB 저장
        assert mock_repo.create_message.call_count == 2  # user + assistant

    @patch("api.services.chat.chat_service.generate_report")
    @patch("api.services.chat.chat_service.fetch_data")
    @patch("api.services.chat.chat_service.llm_classify")
    @patch("api.services.chat.chat_service.chat_repo")
    async def test_navigate_action_emitted(
        self, mock_repo, mock_classify, mock_fetch, mock_report, mock_db,
    ):
        """should_navigate=True → navigate UI 액션 발생."""
        uid = uuid.uuid4()
        fake = _make_session(user_id=uid)
        mock_repo.get_session.return_value = fake

        mock_classify.return_value = ClassificationResult(
            target_page="correlation",
            should_navigate=True,
            category="similar_assets",
            required_tools=[],
            asset_ids=[],
            params={},
            confidence=0.85,
        )
        mock_fetch.return_value = {"name_map": {}}
        mock_report.return_value = CuratedReport(
            summary="요약", analysis="분석",
        )

        events = []
        gen = stream_chat(
            mock_db,
            session_id=fake.id,
            user_id=uid,
            content="상관관계 보여줘",
            page_context={"page_id": "prices"},
        )
        async for event in gen:
            events.append(event)

        # navigate action should be present
        navigate_events = [
            e for e in events
            if "navigate" in e and "ui_action" in e
        ]
        assert len(navigate_events) == 1
        data = json.loads(navigate_events[0].replace("data: ", "").strip())
        assert data["payload"]["path"] == "/correlation"

    @patch("api.services.chat.chat_service._get_graph")
    @patch("api.services.chat.chat_service.llm_classify")
    @patch("api.services.chat.chat_service.chat_repo")
    async def test_fallback_to_langgraph(
        self, mock_repo, mock_classify, mock_graph, mock_db,
    ):
        """낮은 confidence → LangGraph fallback."""
        uid = uuid.uuid4()
        fake = _make_session(user_id=uid)
        mock_repo.get_session.return_value = fake

        mock_classify.return_value = ClassificationResult(
            target_page="home",
            category="general",
            confidence=0.3,
        )

        mock_event = {
            "event": "on_chat_model_stream",
            "data": {"chunk": MagicMock(content="LLM 응답입니다")},
        }

        async def fake_stream(*args, **kwargs):
            yield mock_event

        graph_instance = MagicMock()
        graph_instance.astream_events = fake_stream
        mock_graph.return_value = graph_instance

        events = []
        gen = stream_chat(
            mock_db,
            session_id=fake.id,
            user_id=uid,
            content="오늘 날씨 어때?",
            page_context={"page_id": "home"},
        )
        async for event in gen:
            events.append(event)

        event_types = [
            json.loads(e.replace("data: ", "").strip())["type"]
            for e in events
        ]
        # analyzing + thinking + text_delta + done
        assert "status" in event_types
        assert "text_delta" in event_types
        assert event_types[-1] == "done"

    @patch("api.services.chat.chat_service._get_graph")
    @patch("api.services.chat.chat_service.llm_classify")
    @patch("api.services.chat.chat_service.chat_repo")
    async def test_general_category_falls_back(
        self, mock_repo, mock_classify, mock_graph, mock_db,
    ):
        """category=general + high confidence → 여전히 LangGraph fallback."""
        uid = uuid.uuid4()
        fake = _make_session(user_id=uid)
        mock_repo.get_session.return_value = fake

        mock_classify.return_value = ClassificationResult(
            target_page="home",
            category="general",
            confidence=0.9,  # 높은 confidence지만 general
        )

        async def fake_stream(*args, **kwargs):
            yield {
                "event": "on_chat_model_stream",
                "data": {"chunk": MagicMock(content="안녕하세요!")},
            }

        graph_instance = MagicMock()
        graph_instance.astream_events = fake_stream
        mock_graph.return_value = graph_instance

        events = []
        gen = stream_chat(
            mock_db,
            session_id=fake.id,
            user_id=uid,
            content="안녕하세요",
        )
        async for event in gen:
            events.append(event)

        assert "thinking" in str(events)  # LangGraph thinking status

    @patch("api.services.chat.chat_service.llm_classify")
    @patch("api.services.chat.chat_service.chat_repo")
    async def test_no_page_context_defaults_home(self, mock_repo, mock_db):
        """page_context 없이 호출 → home 기본값으로 classifier 호출."""
        uid = uuid.uuid4()
        fake = _make_session(user_id=uid)
        mock_repo.get_session.return_value = fake

        mock_classify = AsyncMock(return_value=ClassificationResult(
            target_page="home",
            category="general",
            confidence=0.0,
        ))

        with (
            patch(
                "api.services.chat.chat_service.llm_classify",
                mock_classify,
            ),
            patch("api.services.chat.chat_service._get_graph") as mock_g,
        ):
            async def fake_stream(*args, **kwargs):
                yield {
                    "event": "on_chat_model_stream",
                    "data": {"chunk": MagicMock(content="ok")},
                }
            gi = MagicMock()
            gi.astream_events = fake_stream
            mock_g.return_value = gi

            events = []
            gen = stream_chat(
                mock_db,
                session_id=fake.id,
                user_id=uid,
                content="hello",
                page_context=None,
            )
            async for event in gen:
                events.append(event)

        # classifier가 current_page="home"으로 호출됨
        call_kwargs = mock_classify.call_args[1]
        assert call_kwargs["current_page"] == "home"


# ---------------------------------------------------------------------------
# Router 테스트 — page_context 전달
# ---------------------------------------------------------------------------

class TestChatRouterPageContext:
    @pytest.fixture
    def client(self, mock_db):
        from datetime import datetime, timezone
        from unittest.mock import MagicMock

        from fastapi.testclient import TestClient

        from api.main import app

        fake_user = MagicMock()
        fake_user.id = uuid.uuid4()
        fake_user.email = "test@test.com"
        fake_user.nickname = "tester"
        fake_user.is_active = True
        fake_user.created_at = datetime.now(timezone.utc)

        from api.dependencies import get_current_user, get_db

        def _override_db():
            yield mock_db

        app.dependency_overrides[get_db] = _override_db
        app.dependency_overrides[get_current_user] = lambda: fake_user
        yield TestClient(app, raise_server_exceptions=False), fake_user
        app.dependency_overrides.clear()

    @patch("api.routers.chat.chat_service")
    def test_send_message_with_page_context(self, mock_service, client):
        tc, fake_user = client
        sid = uuid.uuid4()

        async def fake_stream(*args, **kwargs):
            yield 'data: {"type": "done"}\n\n'

        mock_service.stream_chat.return_value = fake_stream()

        resp = tc.post(
            f"/v1/chat/sessions/{sid}/messages",
            json={
                "content": "상관관계 분석해줘",
                "page_context": {
                    "page_id": "correlation",
                    "asset_ids": ["KS200", "005930"],
                    "params": {"window": 60},
                },
            },
        )
        assert resp.status_code == 200

        call_kwargs = mock_service.stream_chat.call_args
        assert call_kwargs.kwargs["page_context"] == {
            "page_id": "correlation",
            "asset_ids": ["KS200", "005930"],
            "params": {"window": 60},
        }

    @patch("api.routers.chat.chat_service")
    def test_send_message_without_page_context(self, mock_service, client):
        tc, fake_user = client
        sid = uuid.uuid4()

        async def fake_stream(*args, **kwargs):
            yield 'data: {"type": "done"}\n\n'

        mock_service.stream_chat.return_value = fake_stream()

        resp = tc.post(
            f"/v1/chat/sessions/{sid}/messages",
            json={"content": "hello"},
        )
        assert resp.status_code == 200
        call_kwargs = mock_service.stream_chat.call_args
        assert call_kwargs.kwargs["page_context"] is None

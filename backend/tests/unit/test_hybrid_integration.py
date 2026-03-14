"""Tests for C.7 하이브리드 → LangGraph 통합.

- chat_service.stream_chat() 하이브리드 경로 테스트
- page_context 전달 테스트
- LangGraph fallback 테스트
- graph.py _build_system_prompt 테스트
"""

from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.orm import Session

from api.services.chat.chat_service import _chunk_text, _fetch_hybrid_data, stream_chat
from api.services.llm.graph import _build_system_prompt
from api.services.llm.hybrid.context import PageContext

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
# _fetch_hybrid_data
# ---------------------------------------------------------------------------

class TestFetchHybridData:
    def test_unknown_category_returns_none(self):
        ctx = PageContext(page_id="home")
        assert _fetch_hybrid_data("unknown_category", ctx) is None

    @patch("api.services.chat.chat_service.json")
    def test_correlation_explain_calls_tool(self, mock_json):
        mock_json.loads.return_value = {"groups": [], "top_pairs": []}
        ctx = PageContext(page_id="correlation", asset_ids=["KS200"])

        with patch(
            "api.services.llm.tools.analyze_correlation_tool"
        ) as mock_tool:
            mock_tool.invoke.return_value = '{"groups":[],"top_pairs":[]}'
            mock_json.loads.return_value = {"groups": [], "top_pairs": []}
            result = _fetch_hybrid_data("correlation_explain", ctx)

        assert result is not None
        mock_tool.invoke.assert_called_once()

    def test_spread_no_pair_returns_none(self):
        ctx = PageContext(page_id="correlation", asset_ids=["KS200"])
        result = _fetch_hybrid_data("spread_analysis", ctx)
        assert result is None


# ---------------------------------------------------------------------------
# stream_chat — 하이브리드 경로
# ---------------------------------------------------------------------------

class TestStreamChatHybrid:
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

    @patch("api.services.chat.chat_service.get_template_response")
    @patch("api.services.chat.chat_service._fetch_hybrid_data")
    @patch("api.services.chat.chat_service.classify_question")
    @patch("api.services.chat.chat_service.chat_repo")
    async def test_hybrid_path_returns_template(
        self, mock_repo, mock_classify, mock_fetch, mock_template, mock_db,
    ):
        """하이브리드 분류기 매칭 → 템플릿 응답 경로."""
        uid = uuid.uuid4()
        fake = _make_session(user_id=uid)
        mock_repo.get_session.return_value = fake

        mock_classify.return_value = "correlation_explain"
        mock_fetch.return_value = {"groups": [], "top_pairs": []}

        mock_action = MagicMock()
        mock_action.to_dict.return_value = {
            "action": "highlight_pair",
            "payload": {"asset_a": "KS200", "asset_b": "005930"},
        }
        mock_template.return_value = ("## 상관도 분석 결과", [mock_action])

        page_ctx = {"page_id": "correlation", "asset_ids": [], "params": {}}
        events = []
        gen = stream_chat(
            mock_db,
            session_id=fake.id,
            user_id=uid,
            content="상관관계 설명해줘",
            page_context=page_ctx,
            is_nudge=True,
        )
        async for event in gen:
            events.append(event)

        # text_delta + ui_action + done
        event_types = []
        for e in events:
            data = json.loads(e.replace("data: ", "").strip())
            event_types.append(data["type"])

        assert "text_delta" in event_types
        assert "ui_action" in event_types
        assert event_types[-1] == "done"

        # assistant 메시지 DB 저장
        assert mock_repo.create_message.call_count == 2  # user + assistant

    @patch("api.services.chat.chat_service._get_graph")
    @patch("api.services.chat.chat_service.classify_question")
    @patch("api.services.chat.chat_service.chat_repo")
    async def test_fallback_to_langgraph(
        self, mock_repo, mock_classify, mock_graph, mock_db,
    ):
        """분류 실패 → LangGraph fallback."""
        uid = uuid.uuid4()
        fake = _make_session(user_id=uid)
        mock_repo.get_session.return_value = fake

        mock_classify.return_value = None  # 분류 실패

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

        # status(analyzing) + status(thinking) + text_delta + done
        assert len(events) == 4
        assert '"status"' in events[0]
        assert '"text_delta"' in events[2]

    @patch("api.services.chat.chat_service._fetch_hybrid_data")
    @patch("api.services.chat.chat_service.classify_question")
    @patch("api.services.chat.chat_service._get_graph")
    @patch("api.services.chat.chat_service.chat_repo")
    async def test_hybrid_data_fail_falls_back(
        self, mock_repo, mock_graph, mock_classify, mock_fetch, mock_db,
    ):
        """넛지 분류 성공했지만 데이터 fetch 실패 → 에러 메시지 fallback."""
        uid = uuid.uuid4()
        fake = _make_session(user_id=uid)
        mock_repo.get_session.return_value = fake

        mock_classify.return_value = "correlation_explain"
        mock_fetch.return_value = None  # fetch 실패

        events = []
        gen = stream_chat(
            mock_db,
            session_id=fake.id,
            user_id=uid,
            content="상관관계 설명해줘",
            page_context={"page_id": "correlation"},
            is_nudge=True,
        )
        async for event in gen:
            events.append(event)

        # status(analyzing) + status(fetching) + text_delta(에러 메시지) + done
        assert len(events) == 4

    @patch("api.services.chat.chat_service.chat_repo")
    async def test_no_page_context_defaults_home(self, mock_repo, mock_db):
        """page_context 없이 호출 → home 기본값으로 분류기 실행."""
        uid = uuid.uuid4()
        fake = _make_session(user_id=uid)
        mock_repo.get_session.return_value = fake

        with patch(
            "api.services.chat.chat_service.classify_question"
        ) as mock_cls:
            mock_cls.return_value = None
            with patch("api.services.chat.chat_service._get_graph") as mock_g:
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
                    is_nudge=True,
                )
                async for event in gen:
                    events.append(event)

            # classify_question은 PageContext(page_id="home")으로 호출
            call_args = mock_cls.call_args
            assert call_args[0][1].page_id == "home"


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

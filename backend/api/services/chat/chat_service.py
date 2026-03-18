"""Chat service — Agentic flow (Classifier → DataFetcher → Reporter) + LangGraph fallback."""

from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncGenerator

from fastapi import HTTPException, status
from langchain_core.messages import HumanMessage
from sqlalchemy.orm import Session

from api.repositories import chat_repo
from api.services.llm.agentic.classifier import classify_question as llm_classify
from api.services.llm.agentic.data_fetcher import fetch_data
from api.services.llm.agentic.reporter import generate_report
from api.services.llm.agentic.schemas import CuratedReport
from api.services.llm.graph import build_graph
from api.services.llm.hybrid.context import PageContext
from db.models import ChatSession

logger = logging.getLogger(__name__)

# LangGraph 싱글톤 (MemorySaver 유지)
_graph = None

# Confidence threshold — 이 값 미만이면 LangGraph fallback
_CONFIDENCE_THRESHOLD = 0.5


def _get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


# ---------------------------------------------------------------------------
# Session CRUD (변경 없음)
# ---------------------------------------------------------------------------

def create_session(
    db: Session,
    *,
    user_id: uuid.UUID,
    title: str | None = None,
) -> ChatSession:
    """새 채팅 세션 생성."""
    session = chat_repo.create_session(db, user_id=user_id, title=title)
    db.commit()
    return session


def get_session_with_messages(
    db: Session,
    *,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict:
    """세션 + 메시지 조회 (소유권 검증 포함)."""
    session = chat_repo.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session",
        )
    messages = chat_repo.list_messages_by_session(db, session_id)
    return {"session": session, "messages": messages}


def list_sessions(
    db: Session,
    *,
    user_id: uuid.UUID,
) -> list[ChatSession]:
    """사용자의 채팅 세션 목록."""
    return chat_repo.list_sessions_by_user(db, user_id)


# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _status_event(step: str, message: str) -> str:
    """status SSE 이벤트 생성."""
    evt = {"type": "status", "data": {"step": step, "message": message}}
    return f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"


def _chunk_text(text: str, size: int) -> list[str]:
    """텍스트를 size 글자 단위로 분할 (SSE 스트리밍 시뮬레이션)."""
    return [text[i:i + size] for i in range(0, len(text), size)]


def _sse(evt: dict) -> str:
    """SSE data line from dict."""
    return f"data: {json.dumps(evt, ensure_ascii=False)}\n\n"


# ---------------------------------------------------------------------------
# Main streaming function
# ---------------------------------------------------------------------------

async def stream_chat(
    db: Session,
    *,
    session_id: uuid.UUID,
    user_id: uuid.UUID,
    content: str,
    deep_mode: bool = False,
    page_context: dict | None = None,
    is_nudge: bool = False,
) -> AsyncGenerator[str, None]:
    """Agentic flow → SSE 이벤트 스트림.

    1. LLM Classifier: 질문 분류
    2. confidence >= threshold AND category != general:
       → DataFetcher → LLM Reporter → 구조화된 응답
    3. else: LangGraph fallback (기존 agent+tools 루프)
    """
    # 세션 소유권 검증
    session = chat_repo.get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    if session.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not your session",
        )

    # user 메시지 DB 저장
    chat_repo.create_message(db, session_id=session_id, role="user", content=content)
    db.commit()

    ctx = PageContext.from_dict(page_context)
    full_response = ""

    # ── Step 1: LLM Classifier ──
    yield _status_event("analyzing", "질문 분석 중...")

    classification = await llm_classify(
        question=content,
        current_page=ctx.page_id,
        asset_ids=ctx.asset_ids or None,
        params=ctx.params or None,
    )

    logger.info(
        "Classifier result: category=%s confidence=%.2f target_page=%s",
        classification.category,
        classification.confidence,
        classification.target_page,
    )

    # ── Agentic flow or LangGraph fallback ──
    use_agentic = (
        classification.confidence >= _CONFIDENCE_THRESHOLD
        and classification.category != "general"
    )

    if use_agentic:
        try:
            # Navigate 액션 — LLM 판단 + 결정적 보정 (target != current이면 항상 이동)
            should_nav = (
                classification.should_navigate
                or classification.target_page != ctx.page_id
            )
            if should_nav and classification.target_page != ctx.page_id:
                page_path = _page_id_to_path(classification.target_page)
                if page_path:
                    yield _sse({
                        "type": "ui_action",
                        "action": "navigate",
                        "payload": {"path": page_path},
                    })

            # ── Step 2: DataFetcher ──
            yield _status_event("fetching", "데이터 조회 중...")
            tool_results = await fetch_data(classification)

            # ── Step 3: LLM Reporter ──
            yield _status_event("generating", "분석 리포트 생성 중...")
            report = await generate_report(
                category=classification.category,
                tool_results=tool_results,
                page_id=classification.target_page,
                question=content,
                deep_mode=deep_mode,
            )

            # ── 응답 스트리밍 ──
            full_response = _format_report(report)

            for chunk in _chunk_text(full_response, 80):
                yield _sse({"type": "text_delta", "content": chunk})

            # UI 액션 전송 (LLM 생성 + 프로그래밍적 보정)
            ui_actions = list(report.ui_actions)
            ui_actions = _ensure_highlight_pair(
                ui_actions, classification, report,
            )
            for action in ui_actions:
                yield _sse({"type": "ui_action", **action.model_dump()})

            # Follow-up 질문 전송 (LLM이 빈 배열이면 기본 질문 사용)
            follow_ups = report.follow_up_questions or _default_follow_ups(
                classification.target_page,
            )
            if follow_ups:
                logger.info("Sending follow_up SSE: %d questions", len(follow_ups))
                yield _sse({
                    "type": "follow_up",
                    "questions": follow_ups,
                })
            else:
                logger.warning("No follow_up questions to send")

            # DB 저장 + done
            if full_response:
                chat_repo.create_message(
                    db, session_id=session_id, role="assistant",
                    content=full_response,
                )
                db.commit()
            yield _sse({"type": "done"})
            return

        except Exception:
            logger.exception(
                "Agentic flow failed for session %s — falling back to LangGraph",
                session_id,
            )
            # agentic 실패 시 LangGraph fallback으로 계속 진행
            full_response = ""

    # ── LangGraph fallback ──
    yield _status_event("thinking", "AI가 생각하고 있어요...")
    graph = _get_graph()
    thread_id = str(session_id)
    tools_called: list[str] = []
    tool_results_raw: dict[str, str] = {}

    try:
        async for event in graph.astream_events(
            {"messages": [HumanMessage(content=content)]},
            config={
                "configurable": {
                    "thread_id": thread_id,
                    "deep_mode": deep_mode,
                    "page_context": page_context,
                },
            },
            version="v2",
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"].get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    text = chunk.content
                    full_response += text
                    yield _sse({"type": "text_delta", "content": text})

            elif kind == "on_tool_start":
                tools_called.append(event["name"])
                yield _sse({
                    "type": "tool_call",
                    "name": event["name"],
                    "args": event["data"].get("input", {}),
                })

            elif kind == "on_tool_end":
                raw_output = event["data"].get("output", "")
                if hasattr(raw_output, "content"):
                    raw_output = raw_output.content
                tool_results_raw[event["name"]] = str(raw_output)
                yield _sse({
                    "type": "tool_result",
                    "name": event["name"],
                    "data": str(raw_output),
                })

    except Exception:
        logger.exception("LangGraph stream error for session %s", session_id)
        yield _sse({"type": "error", "content": "응답 생성 중 오류가 발생했습니다."})

    # ── LangGraph 후처리: ui_action + follow_up ──
    for action_evt in _langgraph_ui_actions(tools_called, tool_results_raw):
        yield _sse(action_evt)

    page_id = _infer_page_from_tools(tools_called, ctx.page_id)
    follow_ups = _default_follow_ups(page_id)
    if follow_ups:
        yield _sse({"type": "follow_up", "questions": follow_ups})

    # assistant 메시지 DB 저장
    if full_response:
        chat_repo.create_message(
            db, session_id=session_id, role="assistant", content=full_response,
        )
        db.commit()

    yield _sse({"type": "done"})


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_report(report: CuratedReport) -> str:
    """CuratedReport를 텍스트로 포매팅."""
    parts = [report.summary, "", report.analysis]
    if report.verdict:
        parts.extend(["", f"> {report.verdict}"])
    return "\n".join(parts)


def _page_id_to_path(page_id: str) -> str | None:
    """page_id → React Router 경로."""
    mapping = {
        "prices": "/prices",
        "correlation": "/correlation",
        "indicators": "/indicators",
        "strategy": "/strategy",
        "home": "/",
    }
    return mapping.get(page_id)


def _langgraph_ui_actions(
    tools_called: list[str],
    tool_results_raw: dict[str, str],
) -> list[dict]:
    """LangGraph fallback에서 tool 호출 결과 기반 ui_action 생성."""
    import json as _json
    actions: list[dict] = []

    # analyze_correlation_tool → highlight_pair (상위 1쌍)
    if "analyze_correlation_tool" in tools_called:
        raw = tool_results_raw.get("analyze_correlation_tool", "")
        try:
            data = _json.loads(raw)
            top_pairs = data.get("top_pairs", [])
            if top_pairs:
                pair = top_pairs[0]
                actions.append({
                    "type": "ui_action",
                    "action": "highlight_pair",
                    "payload": {
                        "asset_a": pair["asset_a"],
                        "asset_b": pair["asset_b"],
                    },
                })
        except (ValueError, KeyError, TypeError):
            pass

    return actions


def _infer_page_from_tools(tools_called: list[str], current_page: str) -> str:
    """호출된 tool 이름에서 페이지 ID 추론."""
    tool_page_map = {
        "get_prices": "prices",
        "analyze_correlation_tool": "correlation",
        "get_correlation": "correlation",
        "get_spread": "correlation",
        "analyze_indicators": "indicators",
        "get_signals": "indicators",
        "get_factors": "indicators",
        "backtest_strategy": "strategy",
        "list_backtests": "strategy",
    }
    for tool in tools_called:
        if tool in tool_page_map:
            return tool_page_map[tool]
    return current_page


def _ensure_highlight_pair(
    ui_actions: list,
    classification,
    report,
) -> list:
    """상관도 카테고리에서 highlight_pair 누락 시 프로그래밍적으로 추가.

    LLM이 ui_actions에 highlight_pair를 생성하지 않는 경우가 많으므로,
    카테고리가 상관도 관련이고 분석 텍스트에서 자산 쌍을 추출할 수 있으면 추가.
    """
    from api.services.llm.agentic.schemas import UIActionModel

    # 이미 highlight_pair가 있으면 그대로 반환
    if any(a.action == "highlight_pair" for a in ui_actions):
        return ui_actions

    # 상관도 카테고리만 처리
    corr_categories = {"correlation_explain", "similar_assets", "spread_analysis"}
    if classification.category not in corr_categories:
        return ui_actions

    # asset_ids에서 상위 2개 자산 쌍 추출
    asset_ids = classification.asset_ids or []
    if len(asset_ids) >= 2:
        ui_actions.append(UIActionModel(
            action="highlight_pair",
            payload={"asset_a": asset_ids[0], "asset_b": asset_ids[1]},
        ))
        logger.info(
            "Injected highlight_pair: %s ↔ %s", asset_ids[0], asset_ids[1],
        )
    elif len(asset_ids) == 1:
        # 단일 자산 → 분석 텍스트에서 가장 높은 상관 자산 추출 시도
        top_pair_asset = _extract_top_correlated(report.analysis, asset_ids[0])
        if top_pair_asset:
            ui_actions.append(UIActionModel(
                action="highlight_pair",
                payload={"asset_a": asset_ids[0], "asset_b": top_pair_asset},
            ))
            logger.info(
                "Injected highlight_pair (extracted): %s ↔ %s",
                asset_ids[0], top_pair_asset,
            )

    return ui_actions


def _extract_top_correlated(analysis_text: str, base_asset: str) -> str | None:
    """분석 텍스트에서 상관계수 상위 항목의 asset_id를 추출."""
    import re
    # 알려진 자산 ID 패턴 매칭
    known_ids = ["KS200", "005930", "000660", "SOXL", "BTC/KRW", "GC=F", "SI=F"]
    for aid in known_ids:
        if aid != base_asset and aid in analysis_text:
            return aid
    # 6자리 종목코드 패턴
    codes = re.findall(r"\b(\d{6})\b", analysis_text)
    for code in codes:
        if code != base_asset:
            return code
    return None


def _default_follow_ups(page_id: str) -> list[str]:
    """페이지별 기본 후속 질문 (LLM이 빈 배열 반환 시 fallback)."""
    defaults: dict[str, list[str]] = {
        "prices": [
            "최근 수익률이 가장 높은 자산은?",
            "변동성이 큰 자산을 비교해줘",
        ],
        "correlation": [
            "가장 상관관계가 높은 자산 쌍은?",
            "분산투자에 좋은 조합 추천해줘",
        ],
        "indicators": [
            "현재 매수 신호가 나온 자산은?",
            "RSI 과매도 구간 자산을 알려줘",
        ],
        "strategy": [
            "수익률이 가장 높은 전략은?",
            "최근 백테스트 결과를 요약해줘",
        ],
    }
    return defaults.get(page_id, ["다른 자산에 대해 분석해줘", "더 자세히 설명해줘"])

"""채팅 스키마."""

from __future__ import annotations

import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ── Request ──────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    title: str | None = None


class PageContextRequest(BaseModel):
    page_id: str = "home"
    asset_ids: list[str] = []
    params: dict = {}


class SendMessageRequest(BaseModel):
    content: str
    deep_mode: bool = False
    page_context: PageContextRequest | None = None
    is_nudge: bool = False


# ── Response ─────────────────────────────────────────────────

class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: str
    content: str | None = None
    tool_payload: dict | None = None
    token_count: int | None = None
    created_at: datetime.datetime


class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    title: str | None = None
    created_at: datetime.datetime
    updated_at: datetime.datetime


class SessionDetailResponse(SessionResponse):
    messages: list[MessageResponse] = []


# ── SSE Event ────────────────────────────────────────────────

class SSEEvent(BaseModel):
    type: str  # text_delta, tool_call, tool_result, done
    content: str | None = None
    name: str | None = None
    args: dict | None = None
    data: dict | None = None

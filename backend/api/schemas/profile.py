"""프로필 스키마."""

from __future__ import annotations

import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

# ── Request ────────────────────────────────────────────────────


class IceBreakingRequest(BaseModel):
    experience_level: Literal["beginner", "intermediate", "expert"]
    decision_style: Literal["feeling", "logic", "balanced"]


class PageVisitRequest(BaseModel):
    page_id: str


# ── Response ───────────────────────────────────────────────────


class ProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    experience_level: str | None = None
    decision_style: str | None = None
    onboarding_completed: bool = False
    preferred_depth: str = "brief"
    top_assets: list[str] | None = None
    top_categories: list[str] | None = None
    updated_at: datetime.datetime


class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    activity_data: dict = {}
    updated_at: datetime.datetime

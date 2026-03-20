"""UserContext — 사용자 컨텍스트 빌더.

DB에서 프로필/활동/요약 데이터를 조회하여
Classifier·Reporter에 전달할 UserContext를 생성한다.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from api.repositories import chat_repo, profile_repo


@dataclass(frozen=True)
class UserContext:
    """LLM 프롬프트에 주입할 사용자 컨텍스트."""

    experience_level: str = "intermediate"  # beginner / intermediate / expert
    decision_style: str = "balanced"  # feeling / logic / balanced
    onboarding_completed: bool = False
    top_assets: list[str] = field(default_factory=list)
    top_categories: list[str] = field(default_factory=list)
    recent_summaries: list[dict] = field(default_factory=list)
    total_questions: int = 0

    def prompt_block(self) -> str:
        """Classifier/Reporter 프롬프트에 삽입할 컨텍스트 블록."""
        parts = [
            f"- 경험 수준: {self.experience_level}",
            f"- 의사결정 성향: {self.decision_style}",
        ]
        if self.top_assets:
            parts.append(f"- 자주 조회하는 자산: {', '.join(self.top_assets[:5])}")
        if self.top_categories:
            parts.append(f"- 자주 묻는 카테고리: {', '.join(self.top_categories[:5])}")
        if self.total_questions:
            parts.append(f"- 누적 질문 수: {self.total_questions}")
        if self.recent_summaries:
            latest = self.recent_summaries[0]
            intent = latest.get("user_intent", "")
            if intent:
                parts.append(f"- 최근 대화 주제: {intent}")
        return "\n".join(parts)


def build_user_context(db: Session, user_id: uuid.UUID) -> UserContext:
    """DB에서 사용자 프로필·활동·요약을 조회하여 UserContext 생성."""
    profile = profile_repo.get_profile(db, user_id)
    activity = profile_repo.get_activity(db, user_id)
    summaries = chat_repo.get_recent_summaries(db, user_id, limit=3)

    # 프로필 데이터
    experience = "intermediate"
    style = "balanced"
    onboarding = False
    top_assets: list[str] = []
    top_categories: list[str] = []

    if profile:
        experience = profile.experience_level or "intermediate"
        style = profile.decision_style or "balanced"
        onboarding = profile.onboarding_completed or False
        top_assets = profile.top_assets or []
        top_categories = profile.top_categories or []

    # 활동 데이터
    total_q = 0
    if activity and activity.activity_data:
        total_q = activity.activity_data.get("total_questions", 0)

    # 최근 요약
    recent = [s.summary_data for s in summaries if s.summary_data]

    return UserContext(
        experience_level=experience,
        decision_style=style,
        onboarding_completed=onboarding,
        top_assets=top_assets,
        top_categories=top_categories,
        recent_summaries=recent,
        total_questions=total_q,
    )

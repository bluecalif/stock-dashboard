"""Profile & Activity repository."""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

from db.models import UserActivity, UserProfile

# ── UserProfile ────────────────────────────────────────────────


def get_profile(db: Session, user_id: uuid.UUID) -> UserProfile | None:
    """사용자 프로필 조회."""
    return db.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def upsert_profile(
    db: Session,
    *,
    user_id: uuid.UUID,
    **kwargs,
) -> UserProfile:
    """프로필 UPSERT (없으면 생성, 있으면 업데이트)."""
    profile = get_profile(db, user_id)
    if profile is None:
        profile = UserProfile(user_id=user_id, **kwargs)
        db.add(profile)
    else:
        for key, value in kwargs.items():
            setattr(profile, key, value)
    db.flush()
    return profile


def save_ice_breaking(
    db: Session,
    *,
    user_id: uuid.UUID,
    experience_level: str,
    decision_style: str,
    raw_answers: dict,
) -> UserProfile:
    """Ice-breaking 답변 저장 + 온보딩 완료 처리."""
    return upsert_profile(
        db,
        user_id=user_id,
        experience_level=experience_level,
        decision_style=decision_style,
        ice_breaking_raw=raw_answers,
        onboarding_completed=True,
    )


# ── UserActivity ───────────────────────────────────────────────


def get_activity(db: Session, user_id: uuid.UUID) -> UserActivity | None:
    """사용자 활동 데이터 조회."""
    return db.query(UserActivity).filter(UserActivity.user_id == user_id).first()


def _ensure_activity(db: Session, user_id: uuid.UUID) -> UserActivity:
    """활동 레코드가 없으면 생성."""
    activity = get_activity(db, user_id)
    if activity is None:
        activity = UserActivity(user_id=user_id, activity_data={})
        db.add(activity)
        db.flush()
    return activity


def increment_activity(
    db: Session,
    *,
    user_id: uuid.UUID,
    path: str,
    amount: int = 1,
) -> UserActivity:
    """JSONB 카운터 원자적 증가.

    path: dot-notation (e.g. "page_visits.dashboard", "total_questions")
    jsonb_set은 중간 키가 없으면 nested path 생성 불가 → 중간 키 보장 후 증가.
    """
    _ensure_activity(db, user_id)

    keys = path.split(".")

    # 중간 키가 있는 경우 (e.g. "page_visits.dashboard") 상위 키를 먼저 보장
    if len(keys) > 1:
        parent_key = keys[0]
        db.execute(
            text(
                "UPDATE user_activity "
                "SET activity_data = jsonb_set("
                "  COALESCE(activity_data::jsonb, '{}'::jsonb), "
                f"  '{{{parent_key}}}'::text[], "
                f"  COALESCE((activity_data::jsonb)->'{parent_key}', '{{}}'::jsonb), "
                "  true"
                ")::json, updated_at = now() "
                "WHERE user_id = :user_id"
            ),
            {"user_id": user_id},
        )

    # 실제 카운터 증가
    json_path = "{" + ",".join(keys) + "}"
    db.execute(
        text(
            "UPDATE user_activity "
            "SET activity_data = jsonb_set("
            "  COALESCE(activity_data::jsonb, '{}'::jsonb), "
            f"  '{json_path}'::text[], "
            f"  (COALESCE(activity_data::jsonb #>> '{json_path}'::text[], '0')::int + :amount)"
            "  ::text::jsonb, "
            "  true"
            ")::json, updated_at = now() "
            "WHERE user_id = :user_id"
        ),
        {"amount": amount, "user_id": user_id},
    )
    db.flush()
    return get_activity(db, user_id)  # type: ignore[return-value]


def record_page_visit(
    db: Session,
    *,
    user_id: uuid.UUID,
    page_id: str,
) -> UserActivity:
    """페이지 방문 기록 (카운터 증가 + last_page_visit 갱신)."""
    increment_activity(db, user_id=user_id, path=f"page_visits.{page_id}")

    # last_page_visit 상위 키 보장 + 타임스탬프 갱신
    db.execute(
        text(
            "UPDATE user_activity "
            "SET activity_data = jsonb_set("
            "  COALESCE(activity_data::jsonb, '{}'::jsonb), "
            "  '{last_page_visit}'::text[], "
            "  COALESCE((activity_data::jsonb)->'last_page_visit', '{}'::jsonb), "
            "  true"
            ")::json, updated_at = now() "
            "WHERE user_id = :user_id"
        ),
        {"user_id": user_id},
    )
    db.execute(
        text(
            "UPDATE user_activity "
            "SET activity_data = jsonb_set("
            "  activity_data::jsonb, "
            f"  '{{last_page_visit,{page_id}}}'::text[], "
            "  to_jsonb(now()::text), "
            "  true"
            ")::json, updated_at = now() "
            "WHERE user_id = :user_id"
        ),
        {"user_id": user_id},
    )
    db.flush()
    return get_activity(db, user_id)  # type: ignore[return-value]

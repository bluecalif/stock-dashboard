"""Profile endpoints — ice-breaking, profile, activity."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_current_user, get_db
from api.repositories import profile_repo
from api.schemas.profile import (
    ActivityResponse,
    IceBreakingRequest,
    PageVisitRequest,
    ProfileResponse,
)
from db.models import User

router = APIRouter(prefix="/v1/profile", tags=["profile"])


@router.get("", response_model=ProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    """현재 사용자 프로필 조회 (없으면 빈 프로필 생성)."""
    profile = profile_repo.upsert_profile(db, user_id=current_user.id)
    db.commit()
    return ProfileResponse.model_validate(profile)


@router.post("/ice-breaking", response_model=ProfileResponse)
def submit_ice_breaking(
    body: IceBreakingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProfileResponse:
    """아이스브레이킹 답변 제출."""
    profile = profile_repo.save_ice_breaking(
        db,
        user_id=current_user.id,
        experience_level=body.experience_level,
        decision_style=body.decision_style,
        raw_answers=body.model_dump(),
    )
    db.commit()
    return ProfileResponse.model_validate(profile)


@router.get("/activity", response_model=ActivityResponse)
def get_activity(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivityResponse:
    """활동 데이터 조회."""
    activity = profile_repo.get_activity(db, current_user.id)
    if activity is None:
        activity = profile_repo._ensure_activity(db, current_user.id)
        db.commit()
    return ActivityResponse.model_validate(activity)


@router.post("/activity/page-visit", response_model=ActivityResponse)
def record_page_visit(
    body: PageVisitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ActivityResponse:
    """페이지 방문 기록."""
    activity = profile_repo.record_page_visit(
        db, user_id=current_user.id, page_id=body.page_id,
    )
    db.commit()
    return ActivityResponse.model_validate(activity)

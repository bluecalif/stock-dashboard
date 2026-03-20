"""UserContext 빌더 + prompt_block 테스트."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

from api.services.chat.user_context import UserContext, build_user_context

# ---------------------------------------------------------------------------
# UserContext dataclass 테스트
# ---------------------------------------------------------------------------


class TestUserContext:
    """UserContext 기본 동작."""

    def test_defaults(self):
        ctx = UserContext()
        assert ctx.experience_level == "intermediate"
        assert ctx.decision_style == "balanced"
        assert ctx.onboarding_completed is False
        assert ctx.top_assets == []
        assert ctx.total_questions == 0

    def test_prompt_block_basic(self):
        ctx = UserContext(experience_level="beginner", decision_style="feeling")
        block = ctx.prompt_block()
        assert "beginner" in block
        assert "feeling" in block

    def test_prompt_block_with_assets_and_categories(self):
        ctx = UserContext(
            experience_level="expert",
            decision_style="logic",
            top_assets=["005930", "KS200"],
            top_categories=["strategy_backtest"],
            total_questions=42,
        )
        block = ctx.prompt_block()
        assert "005930" in block
        assert "strategy_backtest" in block
        assert "42" in block

    def test_prompt_block_with_recent_summary(self):
        ctx = UserContext(
            recent_summaries=[
                {"user_intent": "삼성전자 RSI 분석", "turn_count": 5},
            ],
        )
        block = ctx.prompt_block()
        assert "삼성전자 RSI 분석" in block

    def test_prompt_block_empty_summary_intent(self):
        ctx = UserContext(recent_summaries=[{"user_intent": "", "turn_count": 3}])
        block = ctx.prompt_block()
        assert "최근 대화 주제" not in block


# ---------------------------------------------------------------------------
# build_user_context 테스트
# ---------------------------------------------------------------------------


class TestBuildUserContext:
    """DB 조회 → UserContext 빌드."""

    @patch("api.services.chat.user_context.chat_repo")
    @patch("api.services.chat.user_context.profile_repo")
    def test_build_with_full_data(self, mock_profile_repo, mock_chat_repo):
        uid = uuid.uuid4()
        db = MagicMock()

        # 프로필 mock
        profile = MagicMock()
        profile.experience_level = "expert"
        profile.decision_style = "logic"
        profile.onboarding_completed = True
        profile.top_assets = ["005930", "SOXL"]
        profile.top_categories = ["strategy_backtest"]
        mock_profile_repo.get_profile.return_value = profile

        # 활동 mock
        activity = MagicMock()
        activity.activity_data = {"total_questions": 25}
        mock_profile_repo.get_activity.return_value = activity

        # 요약 mock
        summary = MagicMock()
        summary.summary_data = {"user_intent": "BTC 추세 분석", "turn_count": 5}
        mock_chat_repo.get_recent_summaries.return_value = [summary]

        ctx = build_user_context(db, uid)

        assert ctx.experience_level == "expert"
        assert ctx.decision_style == "logic"
        assert ctx.onboarding_completed is True
        assert ctx.top_assets == ["005930", "SOXL"]
        assert ctx.total_questions == 25
        assert len(ctx.recent_summaries) == 1

    @patch("api.services.chat.user_context.chat_repo")
    @patch("api.services.chat.user_context.profile_repo")
    def test_build_with_no_data(self, mock_profile_repo, mock_chat_repo):
        """프로필/활동 없는 신규 사용자 → 기본값."""
        uid = uuid.uuid4()
        db = MagicMock()

        mock_profile_repo.get_profile.return_value = None
        mock_profile_repo.get_activity.return_value = None
        mock_chat_repo.get_recent_summaries.return_value = []

        ctx = build_user_context(db, uid)

        assert ctx.experience_level == "intermediate"
        assert ctx.decision_style == "balanced"
        assert ctx.onboarding_completed is False
        assert ctx.top_assets == []
        assert ctx.total_questions == 0
        assert ctx.recent_summaries == []

    @patch("api.services.chat.user_context.chat_repo")
    @patch("api.services.chat.user_context.profile_repo")
    def test_build_with_partial_profile(self, mock_profile_repo, mock_chat_repo):
        """프로필 있지만 일부 필드 None."""
        uid = uuid.uuid4()
        db = MagicMock()

        profile = MagicMock()
        profile.experience_level = None
        profile.decision_style = "feeling"
        profile.onboarding_completed = None
        profile.top_assets = None
        profile.top_categories = None
        mock_profile_repo.get_profile.return_value = profile

        mock_profile_repo.get_activity.return_value = None
        mock_chat_repo.get_recent_summaries.return_value = []

        ctx = build_user_context(db, uid)

        assert ctx.experience_level == "intermediate"  # fallback
        assert ctx.decision_style == "feeling"
        assert ctx.onboarding_completed is False
        assert ctx.top_assets == []

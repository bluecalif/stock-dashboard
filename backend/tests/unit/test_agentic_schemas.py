"""F.1: Agentic schemas — Pydantic v2 validation tests."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from api.services.llm.agentic.schemas import (
    ClassificationResult,
    CuratedReport,
    UIActionModel,
)

# ── UIActionModel ──────────────────────────────────────────────────────────


class TestUIActionModel:
    def test_navigate(self):
        action = UIActionModel(action="navigate", payload={"path": "/correlation"})
        assert action.action == "navigate"
        assert action.payload == {"path": "/correlation"}

    def test_highlight_pair(self):
        action = UIActionModel(
            action="highlight_pair",
            payload={"asset_a": "KS200", "asset_b": "005930"},
        )
        assert action.action == "highlight_pair"

    def test_default_payload(self):
        action = UIActionModel(action="set_filter")
        assert action.payload == {}

    def test_invalid_action_rejected(self):
        with pytest.raises(ValidationError):
            UIActionModel(action="invalid_action")

    def test_serialization_roundtrip(self):
        action = UIActionModel(action="update_chart", payload={"chart_id": "equity"})
        data = action.model_dump()
        restored = UIActionModel(**data)
        assert restored == action

    def test_json_schema_has_enum(self):
        schema = UIActionModel.model_json_schema()
        # action 필드는 Literal enum으로 제한
        assert "action" in schema["properties"]


# ── ClassificationResult ───────────────────────────────────────────────────


class TestClassificationResult:
    def test_minimal_valid(self):
        result = ClassificationResult(
            target_page="correlation",
            category="similar_assets",
            confidence=0.85,
        )
        assert result.target_page == "correlation"
        assert result.should_navigate is False
        assert result.required_tools == []
        assert result.asset_ids == []
        assert result.params == {}

    def test_full_valid(self):
        result = ClassificationResult(
            target_page="indicators",
            should_navigate=True,
            category="indicator_explain",
            required_tools=["analyze_indicators", "get_factors"],
            asset_ids=["KS200"],
            params={"forward_days": 5},
            confidence=0.92,
        )
        assert result.should_navigate is True
        assert len(result.required_tools) == 2
        assert result.params["forward_days"] == 5

    def test_general_fallback(self):
        result = ClassificationResult(
            target_page="home",
            category="general",
            confidence=0.3,
        )
        assert result.category == "general"
        assert result.confidence < 0.5

    def test_confidence_bounds(self):
        # 0.0 OK
        ClassificationResult(target_page="home", category="general", confidence=0.0)
        # 1.0 OK
        ClassificationResult(target_page="home", category="general", confidence=1.0)
        # < 0.0 rejected
        with pytest.raises(ValidationError):
            ClassificationResult(
                target_page="home", category="general", confidence=-0.1,
            )
        # > 1.0 rejected
        with pytest.raises(ValidationError):
            ClassificationResult(
                target_page="home", category="general", confidence=1.1,
            )

    def test_invalid_page_rejected(self):
        with pytest.raises(ValidationError):
            ClassificationResult(
                target_page="unknown_page",
                category="general",
                confidence=0.5,
            )

    def test_invalid_category_rejected(self):
        with pytest.raises(ValidationError):
            ClassificationResult(
                target_page="home",
                category="nonexistent_category",
                confidence=0.5,
            )

    def test_invalid_tool_rejected(self):
        with pytest.raises(ValidationError):
            ClassificationResult(
                target_page="home",
                category="general",
                required_tools=["fake_tool"],
                confidence=0.5,
            )

    def test_json_schema_generation(self):
        """OpenAI Structured Output에 사용할 JSON Schema 생성 확인."""
        schema = ClassificationResult.model_json_schema()
        assert "properties" in schema
        assert "target_page" in schema["properties"]
        assert "confidence" in schema["properties"]
        # JSON 직렬화 가능
        json.dumps(schema)


# ── CuratedReport ──────────────────────────────────────────────────────────


class TestCuratedReport:
    def test_minimal_valid(self):
        report = CuratedReport(
            summary="KOSPI200과 삼성전자의 상관계수는 0.87입니다.",
            analysis="두 자산은 높은 양의 상관관계를 보입니다.",
        )
        assert report.verdict == ""
        assert report.ui_actions == []
        assert report.follow_up_questions == []

    def test_full_valid(self):
        report = CuratedReport(
            summary="RSI가 과매수 구간입니다.",
            analysis="## RSI 분석\n\nKS200의 RSI(14)는 75로 과매수 구간입니다.",
            verdict="단기 조정 가능성에 유의하세요.",
            ui_actions=[
                UIActionModel(
                    action="highlight_pair",
                    payload={"asset_a": "KS200", "asset_b": "005930"},
                ),
                UIActionModel(action="navigate", payload={"path": "/indicators"}),
            ],
            follow_up_questions=[
                "MACD는 어떤 상태인가요?",
                "다른 자산의 RSI도 보여주세요.",
            ],
        )
        assert len(report.ui_actions) == 2
        assert len(report.follow_up_questions) == 2

    def test_follow_up_max_5(self):
        """follow_up_questions 최대 5개 제한."""
        with pytest.raises(ValidationError):
            CuratedReport(
                summary="요약",
                analysis="분석",
                follow_up_questions=["q1", "q2", "q3", "q4", "q5", "q6"],
            )

    def test_ui_actions_with_invalid_action(self):
        with pytest.raises(ValidationError):
            CuratedReport(
                summary="요약",
                analysis="분석",
                ui_actions=[{"action": "bad_action", "payload": {}}],
            )

    def test_serialization_roundtrip(self):
        report = CuratedReport(
            summary="요약",
            analysis="분석",
            verdict="결론",
            ui_actions=[UIActionModel(action="navigate", payload={"path": "/prices"})],
            follow_up_questions=["후속 질문?"],
        )
        data = report.model_dump()
        restored = CuratedReport(**data)
        assert restored == report

    def test_json_schema_generation(self):
        schema = CuratedReport.model_json_schema()
        assert "summary" in schema["properties"]
        assert "follow_up_questions" in schema["properties"]
        json.dumps(schema)

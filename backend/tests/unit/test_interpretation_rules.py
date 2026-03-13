"""Tests for interpretation_rules — boundary value checks."""

import pytest

from api.services.analysis.interpretation_rules import (
    interpret_correlation,
    interpret_spread_zscore,
)

# ---------------------------------------------------------------------------
# interpret_correlation
# ---------------------------------------------------------------------------

class TestInterpretCorrelation:
    @pytest.mark.parametrize("value,expected_level", [
        (1.0, "very_strong"),
        (0.95, "very_strong"),
        (0.8, "very_strong"),
        (0.79, "strong"),
        (0.5, "strong"),
        (0.49, "moderate"),
        (0.2, "moderate"),
        (0.19, "weak"),
        (0.01, "weak"),
    ])
    def test_positive_ranges(self, value, expected_level):
        result = interpret_correlation(value)
        assert result.level == expected_level
        assert "양" in result.label

    @pytest.mark.parametrize("value,expected_level", [
        (-1.0, "very_strong"),
        (-0.9, "very_strong"),
        (-0.8, "very_strong"),
        (-0.79, "strong"),
        (-0.5, "strong"),
        (-0.49, "moderate"),
        (-0.2, "moderate"),
        (-0.19, "weak"),
        (-0.01, "weak"),
    ])
    def test_negative_ranges(self, value, expected_level):
        result = interpret_correlation(value)
        assert result.level == expected_level
        assert "음" in result.label

    def test_zero(self):
        result = interpret_correlation(0.0)
        assert result.level in ("none", "weak")

    def test_clamp_above(self):
        """Values > 1.0 clamped to 1.0."""
        result = interpret_correlation(1.5)
        assert result.level == "very_strong"

    def test_clamp_below(self):
        """Values < -1.0 clamped to -1.0."""
        result = interpret_correlation(-1.5)
        assert result.level == "very_strong"

    def test_has_description(self):
        result = interpret_correlation(0.9)
        assert len(result.description) > 0
        assert len(result.label) > 0


# ---------------------------------------------------------------------------
# interpret_spread_zscore
# ---------------------------------------------------------------------------

class TestInterpretSpreadZscore:
    @pytest.mark.parametrize("zscore,expected_level", [
        (3.0, "extreme"),
        (2.0, "extreme"),
        (-2.5, "extreme"),
        (1.5, "warning"),
        (1.0, "warning"),
        (-1.0, "warning"),
        (0.5, "normal"),
        (0.0, "normal"),
        (-0.3, "normal"),
    ])
    def test_zscore_ranges(self, zscore, expected_level):
        result = interpret_spread_zscore(zscore)
        assert result.level == expected_level

    def test_positive_direction(self):
        result = interpret_spread_zscore(2.5)
        assert "양" in result.label

    def test_negative_direction(self):
        result = interpret_spread_zscore(-2.5)
        assert "음" in result.label

    def test_zero_no_direction(self):
        result = interpret_spread_zscore(0.0)
        assert "방향" not in result.label

    def test_has_description(self):
        result = interpret_spread_zscore(1.5)
        assert len(result.description) > 0

"""Tests for correlation_analysis — grouping, top pairs, similar assets."""

import pytest

from api.services.analysis.correlation_analysis import (
    analyze_correlation,
    find_correlation_groups,
    find_top_pairs,
    recommend_similar,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

# 4-asset correlation matrix (symmetric, diagonal = 1.0)
# KS200 ↔ 005930 = 0.9 (high)
# KS200 ↔ BTC = 0.3 (low)
# KS200 ↔ GC=F = -0.2 (negative)
# 005930 ↔ BTC = 0.4
# 005930 ↔ GC=F = -0.1
# BTC ↔ GC=F = 0.1
ASSET_IDS = ["KS200", "005930", "BTC", "GC=F"]
MATRIX = [
    [1.0, 0.9, 0.3, -0.2],
    [0.9, 1.0, 0.4, -0.1],
    [0.3, 0.4, 1.0, 0.1],
    [-0.2, -0.1, 0.1, 1.0],
]


# ---------------------------------------------------------------------------
# find_correlation_groups
# ---------------------------------------------------------------------------

class TestFindCorrelationGroups:
    def test_groups_above_threshold(self):
        """KS200 + 005930 should be grouped at threshold 0.7."""
        groups = find_correlation_groups(MATRIX, ASSET_IDS, threshold=0.7)
        assert len(groups) == 1
        assert set(groups[0].asset_ids) == {"KS200", "005930"}
        assert groups[0].avg_correlation == pytest.approx(0.9, abs=0.01)

    def test_high_threshold_no_groups(self):
        """Threshold 0.95 → no groups."""
        groups = find_correlation_groups(MATRIX, ASSET_IDS, threshold=0.95)
        assert len(groups) == 0

    def test_low_threshold_merges_more(self):
        """Threshold 0.3 → KS200, 005930, BTC merge."""
        groups = find_correlation_groups(MATRIX, ASSET_IDS, threshold=0.3)
        # KS200-005930 (0.9>=0.3), KS200-BTC (0.3>=0.3), 005930-BTC (0.4>=0.3)
        merged = [g for g in groups if len(g.asset_ids) >= 3]
        assert len(merged) >= 1
        assert {"KS200", "005930", "BTC"} <= set(merged[0].asset_ids)

    def test_empty_matrix(self):
        """Empty input → empty result."""
        groups = find_correlation_groups([], [], threshold=0.7)
        assert groups == []

    def test_two_assets(self):
        """Minimal 2-asset matrix."""
        matrix = [[1.0, 0.8], [0.8, 1.0]]
        ids = ["A", "B"]
        groups = find_correlation_groups(matrix, ids, threshold=0.7)
        assert len(groups) == 1
        assert set(groups[0].asset_ids) == {"A", "B"}

    def test_groups_sorted_by_avg_correlation(self):
        """Groups returned in descending avg correlation order."""
        # Build 6-asset matrix: {A,B}=0.9, {C,D}=0.75, E,F isolated
        ids = ["A", "B", "C", "D", "E", "F"]
        m = [[0.0] * 6 for _ in range(6)]
        for i in range(6):
            m[i][i] = 1.0
        m[0][1] = m[1][0] = 0.9
        m[2][3] = m[3][2] = 0.75
        groups = find_correlation_groups(m, ids, threshold=0.7)
        assert len(groups) == 2
        assert groups[0].avg_correlation >= groups[1].avg_correlation


# ---------------------------------------------------------------------------
# find_top_pairs
# ---------------------------------------------------------------------------

class TestFindTopPairs:
    def test_top_pairs_order(self):
        """Top pair should be KS200-005930 (|0.9| highest)."""
        pairs = find_top_pairs(MATRIX, ASSET_IDS, n=3)
        assert len(pairs) == 3
        assert pairs[0].asset_a == "KS200"
        assert pairs[0].asset_b == "005930"
        assert pairs[0].correlation == pytest.approx(0.9, abs=0.01)

    def test_top_pairs_n_limit(self):
        """Requesting n=1 returns exactly 1."""
        pairs = find_top_pairs(MATRIX, ASSET_IDS, n=1)
        assert len(pairs) == 1

    def test_top_pairs_includes_negative(self):
        """Negative correlations appear when large enough by abs."""
        pairs = find_top_pairs(MATRIX, ASSET_IDS, n=10)
        # All 6 unique pairs for 4 assets
        assert len(pairs) == 6
        correlations = [p.correlation for p in pairs]
        assert any(c < 0 for c in correlations)

    def test_top_pairs_empty(self):
        """Empty matrix → empty result."""
        pairs = find_top_pairs([], [], n=5)
        assert pairs == []

    def test_sorted_by_absolute_value(self):
        """Pairs sorted by |correlation|, not signed value."""
        pairs = find_top_pairs(MATRIX, ASSET_IDS, n=10)
        abs_values = [abs(p.correlation) for p in pairs]
        assert abs_values == sorted(abs_values, reverse=True)


# ---------------------------------------------------------------------------
# recommend_similar
# ---------------------------------------------------------------------------

class TestRecommendSimilar:
    def test_similar_to_ks200(self):
        """005930 (0.9) is most similar to KS200."""
        similar = recommend_similar(MATRIX, ASSET_IDS, "KS200", n=3)
        assert len(similar) == 3
        assert similar[0].asset_id == "005930"
        assert similar[0].correlation == pytest.approx(0.9, abs=0.01)

    def test_similar_n_limit(self):
        """n=1 returns exactly 1."""
        similar = recommend_similar(MATRIX, ASSET_IDS, "KS200", n=1)
        assert len(similar) == 1

    def test_similar_unknown_target(self):
        """Unknown target → empty list."""
        similar = recommend_similar(MATRIX, ASSET_IDS, "UNKNOWN", n=3)
        assert similar == []

    def test_similar_sorted_by_abs(self):
        """Similar assets sorted by |correlation|."""
        similar = recommend_similar(MATRIX, ASSET_IDS, "GC=F", n=10)
        abs_vals = [abs(s.correlation) for s in similar]
        assert abs_vals == sorted(abs_vals, reverse=True)


# ---------------------------------------------------------------------------
# analyze_correlation (convenience)
# ---------------------------------------------------------------------------

class TestAnalyzeCorrelation:
    def test_full_analysis(self):
        """Full analysis returns all three components."""
        result = analyze_correlation(
            MATRIX, ASSET_IDS,
            threshold=0.7,
            top_n=3,
            target_id="KS200",
            similar_n=2,
        )
        assert len(result.groups) >= 1
        assert len(result.top_pairs) == 3
        assert len(result.similar) == 2

    def test_without_target(self):
        """No target_id → similar is empty."""
        result = analyze_correlation(MATRIX, ASSET_IDS)
        assert result.similar == []
        assert len(result.groups) >= 0
        assert len(result.top_pairs) >= 0

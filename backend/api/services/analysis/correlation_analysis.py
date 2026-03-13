"""Correlation analysis — grouping, top pairs, similar asset recommendation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class CorrelationGroup:
    """A group of assets with high correlation."""

    group_id: int
    asset_ids: list[str]
    avg_correlation: float


@dataclass
class AssetPair:
    """A pair of assets with their correlation value."""

    asset_a: str
    asset_b: str
    correlation: float


@dataclass
class SimilarAsset:
    """An asset similar to a target with correlation score."""

    asset_id: str
    correlation: float


@dataclass
class CorrelationAnalysisResult:
    """Combined result of correlation analysis."""

    groups: list[CorrelationGroup] = field(default_factory=list)
    top_pairs: list[AssetPair] = field(default_factory=list)
    similar: list[SimilarAsset] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Union-Find (Disjoint Set)
# ---------------------------------------------------------------------------

class _UnionFind:
    """Simple Union-Find for grouping correlated assets."""

    def __init__(self, items: list[str]) -> None:
        self.parent: dict[str, str] = {x: x for x in items}
        self.rank: dict[str, int] = {x: 0 for x in items}

    def find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]  # path compression
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.rank[ra] < self.rank[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if self.rank[ra] == self.rank[rb]:
            self.rank[ra] += 1

    def groups(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = {}
        for item in self.parent:
            root = self.find(item)
            result.setdefault(root, []).append(item)
        return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def find_correlation_groups(
    matrix: list[list[float]],
    asset_ids: list[str],
    threshold: float = 0.7,
) -> list[CorrelationGroup]:
    """Group assets by correlation using Union-Find.

    Assets whose pairwise correlation >= threshold are merged into one group.
    Returns only groups with 2+ members.
    """
    n = len(asset_ids)
    uf = _UnionFind(asset_ids)

    for i in range(n):
        for j in range(i + 1, n):
            if matrix[i][j] >= threshold:
                uf.union(asset_ids[i], asset_ids[j])

    raw_groups = uf.groups()
    result: list[CorrelationGroup] = []
    gid = 0

    for members in raw_groups.values():
        if len(members) < 2:
            continue
        # Average pairwise correlation within group
        idx_map = {aid: k for k, aid in enumerate(asset_ids)}
        total = 0.0
        count = 0
        for a_idx in range(len(members)):
            for b_idx in range(a_idx + 1, len(members)):
                i, j = idx_map[members[a_idx]], idx_map[members[b_idx]]
                total += matrix[i][j]
                count += 1
        avg = round(total / count, 4) if count > 0 else 0.0

        result.append(CorrelationGroup(
            group_id=gid,
            asset_ids=sorted(members),
            avg_correlation=avg,
        ))
        gid += 1

    return sorted(result, key=lambda g: g.avg_correlation, reverse=True)


def find_top_pairs(
    matrix: list[list[float]],
    asset_ids: list[str],
    n: int = 5,
) -> list[AssetPair]:
    """Find top-N correlated asset pairs (excluding self-correlation)."""
    pairs: list[AssetPair] = []
    size = len(asset_ids)

    for i in range(size):
        for j in range(i + 1, size):
            pairs.append(AssetPair(
                asset_a=asset_ids[i],
                asset_b=asset_ids[j],
                correlation=round(matrix[i][j], 4),
            ))

    pairs.sort(key=lambda p: abs(p.correlation), reverse=True)
    return pairs[:n]


def recommend_similar(
    matrix: list[list[float]],
    asset_ids: list[str],
    target_id: str,
    n: int = 3,
) -> list[SimilarAsset]:
    """Recommend N assets most correlated with target_id."""
    if target_id not in asset_ids:
        return []

    target_idx = asset_ids.index(target_id)
    candidates: list[SimilarAsset] = []

    for i, aid in enumerate(asset_ids):
        if i == target_idx:
            continue
        candidates.append(SimilarAsset(
            asset_id=aid,
            correlation=round(matrix[target_idx][i], 4),
        ))

    candidates.sort(key=lambda s: abs(s.correlation), reverse=True)
    return candidates[:n]


def analyze_correlation(
    matrix: list[list[float]],
    asset_ids: list[str],
    *,
    threshold: float = 0.7,
    top_n: int = 5,
    target_id: str | None = None,
    similar_n: int = 3,
) -> CorrelationAnalysisResult:
    """Run full correlation analysis: grouping + top pairs + optional similar.

    Convenience function that combines all three analyses.
    """
    groups = find_correlation_groups(matrix, asset_ids, threshold)
    top_pairs = find_top_pairs(matrix, asset_ids, top_n)
    similar = (
        recommend_similar(matrix, asset_ids, target_id, similar_n)
        if target_id
        else []
    )
    return CorrelationAnalysisResult(
        groups=groups,
        top_pairs=top_pairs,
        similar=similar,
    )

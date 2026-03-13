"""Interpretation rules — human-readable labels for correlation and z-score values."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Interpretation:
    """A human-readable interpretation of a numeric value."""

    label: str       # e.g. "매우 강한 양의 상관"
    level: str       # "very_strong" | "strong" | "moderate" | "weak" | "none"
    description: str  # Detailed explanation


# ---------------------------------------------------------------------------
# Correlation interpretation
# ---------------------------------------------------------------------------

_CORRELATION_RANGES: list[tuple[float, float, str, str, str]] = [
    # (min, max, label, level, description)
    (0.8, 1.0, "매우 강한 양의 상관", "very_strong",
     "두 자산이 거의 동일하게 움직입니다. 분산 효과가 낮습니다."),
    (0.5, 0.8, "강한 양의 상관", "strong",
     "두 자산이 같은 방향으로 움직이는 경향이 강합니다."),
    (0.2, 0.5, "중간 양의 상관", "moderate",
     "어느 정도 같은 방향으로 움직이지만 독립적인 움직임도 있습니다."),
    (0.0, 0.2, "약한 양의 상관", "weak",
     "거의 독립적으로 움직입니다. 분산 투자에 적합합니다."),
    (-0.2, 0.0, "약한 음의 상관", "weak",
     "거의 독립적으로 움직입니다. 분산 투자에 적합합니다."),
    (-0.5, -0.2, "중간 음의 상관", "moderate",
     "반대 방향으로 움직이는 경향이 있습니다. 헤지에 활용 가능합니다."),
    (-0.8, -0.5, "강한 음의 상관", "strong",
     "반대 방향으로 움직이는 경향이 강합니다. 헤지에 유용합니다."),
    (-1.0, -0.8, "매우 강한 음의 상관", "very_strong",
     "거의 정반대로 움직입니다. 강력한 헤지 수단입니다."),
]


def interpret_correlation(value: float) -> Interpretation:
    """Interpret a correlation coefficient (-1.0 ~ 1.0)."""
    value = max(-1.0, min(1.0, value))

    if value >= 0:
        # Positive: iterate top-down (very_strong first)
        for lo, hi, label, level, desc in _CORRELATION_RANGES:
            if lo >= 0 and lo <= value <= hi:
                return Interpretation(label=label, level=level, description=desc)
    else:
        # Negative: iterate bottom-up (very_strong_negative first)
        for lo, hi, label, level, desc in reversed(_CORRELATION_RANGES):
            if hi <= 0 and lo <= value <= hi:
                return Interpretation(label=label, level=level, description=desc)

    # Exact 0.0 fallback
    return Interpretation(
        label="무상관",
        level="none",
        description="두 자산 사이에 선형 관계가 없습니다.",
    )


# ---------------------------------------------------------------------------
# Z-score interpretation
# ---------------------------------------------------------------------------

_ZSCORE_RANGES: list[tuple[float, str, str, str]] = [
    # (threshold, label, level, description)
    (2.0, "극단적 이탈", "extreme",
     "스프레드가 평균에서 크게 벗어났습니다. 수렴 가능성이 높습니다."),
    (1.0, "주의 구간", "warning",
     "스프레드가 평균에서 벗어나기 시작했습니다. 모니터링이 필요합니다."),
    (0.0, "정상 범위", "normal",
     "스프레드가 평균 부근에서 안정적입니다."),
]


def interpret_spread_zscore(zscore: float) -> Interpretation:
    """Interpret a spread z-score (absolute value used for thresholds)."""
    abs_z = abs(zscore)
    direction = "양" if zscore > 0 else "음" if zscore < 0 else ""

    for threshold, label, level, desc in _ZSCORE_RANGES:
        if abs_z >= threshold:
            full_label = f"{label} ({direction}방향)" if direction else label
            return Interpretation(label=full_label, level=level, description=desc)

    # Should not reach here, but just in case
    return Interpretation(
        label="정상 범위",
        level="normal",
        description="스프레드가 평균 부근에서 안정적입니다.",
    )

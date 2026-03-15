"""Indicator analysis service — interpret current factor state with human-readable labels.

Confirmed indicators (2026-03-15 user review):
  Signal + Success rate: RSI (rsi_14), MACD histogram (macd - macd_signal)
  Warning only:          ATR/Price ratio (atr_14/close), vol_20
  Excluded:              ROC, vol_zscore_20, ret_*, SMA, EMA
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_INF = math.inf


@dataclass
class IndicatorState:
    """Human-readable interpretation of a single indicator value."""

    factor_name: str
    value: float
    label: str        # e.g. "과매수", "골든크로스", "고변동성 경고"
    level: str        # standardized key for color-coding
    description: str
    signal: str       # "buy" | "sell" | "neutral"


# ---------------------------------------------------------------------------
# Factors eligible for success-rate calculation (D.2)
# ---------------------------------------------------------------------------

SUCCESS_RATE_FACTORS: list[str] = ["rsi_14", "macd"]


# ---------------------------------------------------------------------------
# Rule definitions
# Format: (lo, hi, label, level, description, signal)
# Evaluated in order; first match (lo <= value <= hi) wins.
# Boundary values fall into the first matching rule.
# ---------------------------------------------------------------------------

# RSI — success rate target
_RSI_RULES: list[tuple] = [
    (80, _INF,  "극단적 과매수",  "extreme_overbought",
     "RSI가 80을 넘어 매우 강한 과매수 상태입니다. 단기 조정 가능성이 높습니다.", "sell"),
    (70, 80,    "과매수",         "overbought",
     "RSI가 70 이상으로 과매수 구간입니다. 매도 신호로 해석됩니다.", "sell"),
    (-_INF, 20, "극단적 과매도",  "extreme_oversold",
     "RSI가 20 미만으로 매우 강한 과매도 상태입니다. 반등 가능성이 있습니다.", "buy"),
    (20, 30,    "과매도",         "oversold",
     "RSI가 30 이하로 과매도 구간입니다. 매수 신호로 해석됩니다.", "buy"),
    (60, 70,    "강세 우위",      "bullish",
     "RSI가 60~70으로 상승 모멘텀이 우세한 구간입니다.", "neutral"),
    (40, 60,    "중립",           "neutral",
     "RSI가 40~60으로 매수/매도 우위가 없는 중립 구간입니다.", "neutral"),
    (30, 40,    "약세 우위",      "bearish",
     "RSI가 30~40으로 하락 모멘텀이 우세한 구간입니다.", "neutral"),
]

# vol_20 — warning only, NOT in success rate
_VOL20_RULES: list[tuple] = [
    (0.5, _INF,   "매우 높은 변동성 경고",  "very_high_vol_warning",
     "연환산 변동성이 50%를 넘어 극단적으로 높은 상태입니다. 시장 진입을 피하세요.", "sell"),
    (0.3, 0.5,    "높은 변동성 경고",       "high_vol_warning",
     "연환산 변동성이 30~50%로 높습니다. 시장 진입에 주의가 필요합니다.", "sell"),
    (-_INF, 0.3,  "보통 이하 변동성",       "normal_vol",
     "연환산 변동성이 30% 미만으로 일반적인 수준입니다.", "neutral"),
]

# ATR/Price ratio — warning only, NOT in success rate
# Computed at API response time as atr_14 / close (not stored in DB)
_ATR_PCT_RULES: list[tuple] = [
    (0.03, _INF,   "고변동성 경고",  "high_vol_warning",
     "ATR/가격 비율이 3%를 넘어 일일 변동 범위가 큽니다. 시장 진입을 피하세요.", "sell"),
    (0.01, 0.03,   "보통 변동성",    "normal_vol",
     "ATR/가격 비율이 1~3%로 일반적인 수준입니다.", "neutral"),
    (-_INF, 0.01,  "낮은 변동성",    "low_vol",
     "ATR/가격 비율이 1% 미만으로 낮습니다.", "neutral"),
]


# ---------------------------------------------------------------------------
# Registry: factor_name → rules (single-value interpretation)
# ---------------------------------------------------------------------------

INDICATOR_RULES: dict[str, list[tuple]] = {
    "rsi_14":   _RSI_RULES,
    "vol_20":   _VOL20_RULES,
    "atr_pct":  _ATR_PCT_RULES,
}

# Human-readable display names
FACTOR_DISPLAY_NAMES: dict[str, str] = {
    "rsi_14":      "RSI (14일)",
    "macd":        "MACD 히스토그램",
    "vol_20":      "변동성 (20일, 연환산)",
    "atr_pct":     "ATR/가격 비율",
}


def interpret_indicator_state(factor_name: str, value: float) -> IndicatorState:
    """Interpret a single indicator value and return a human-readable state.

    For MACD, use interpret_macd_histogram() instead (requires two values).

    Args:
        factor_name: "rsi_14", "vol_20", or "atr_pct".
        value: The current factor value.

    Raises:
        ValueError: If factor_name is not in INDICATOR_RULES.
    """
    if factor_name not in INDICATOR_RULES:
        raise ValueError(
            f"Unknown factor '{factor_name}'. "
            f"Supported single-value: {sorted(INDICATOR_RULES.keys())}. "
            f"For MACD use interpret_macd_histogram()."
        )

    for lo, hi, label, level, description, signal in INDICATOR_RULES[factor_name]:
        if lo <= value <= hi:
            return IndicatorState(
                factor_name=factor_name,
                value=value,
                label=label,
                level=level,
                description=description,
                signal=signal,
            )

    # Fallback — should not occur if rules cover all ranges
    return IndicatorState(
        factor_name=factor_name,
        value=value,
        label="알 수 없음",
        level="unknown",
        description="해석 규칙이 없는 값입니다.",
        signal="neutral",
    )


def interpret_macd_histogram(macd: float, macd_signal: float) -> IndicatorState:
    """Interpret MACD histogram (macd - macd_signal).

    MACD > signal line → golden cross (buy)
    MACD < signal line → dead cross (sell)

    Args:
        macd: Current MACD value (EMA12 - EMA26).
        macd_signal: Current signal line value (EMA9 of MACD).
    """
    histogram = macd - macd_signal

    if histogram > 0:
        return IndicatorState(
            factor_name="macd",
            value=histogram,
            label="MACD 골든크로스",
            level="bullish_cross",
            description=(
                f"MACD({macd:.2f})가 신호선({macd_signal:.2f})을 상회합니다. "
                "단기 모멘텀이 강세로 전환된 매수 신호입니다."
            ),
            signal="buy",
        )
    elif histogram < 0:
        return IndicatorState(
            factor_name="macd",
            value=histogram,
            label="MACD 데드크로스",
            level="bearish_cross",
            description=(
                f"MACD({macd:.2f})가 신호선({macd_signal:.2f})을 하회합니다. "
                "단기 모멘텀이 약세로 전환된 매도 신호입니다."
            ),
            signal="sell",
        )
    else:
        return IndicatorState(
            factor_name="macd",
            value=0.0,
            label="MACD 교차 중",
            level="neutral",
            description="MACD와 신호선이 교차 중입니다. 방향 전환을 주시하세요.",
            signal="neutral",
        )


def interpret_multiple(
    factor_values: dict[str, float],
    *,
    macd: float | None = None,
    macd_signal: float | None = None,
) -> list[IndicatorState]:
    """Interpret multiple indicators at once.

    Args:
        factor_values: Mapping of factor_name → value for single-value indicators.
                       Supports: rsi_14, vol_20, atr_pct.
                       NaN/inf values and unknown factor names are skipped.
        macd: Current MACD value (optional, for MACD histogram interpretation).
        macd_signal: Current signal line value (optional, paired with macd).

    Returns:
        List of IndicatorState for all valid inputs.
    """
    results = []

    # Single-value indicators
    for name, value in factor_values.items():
        if not isinstance(value, (int, float)):
            continue
        if math.isnan(value) or math.isinf(value):
            continue
        if name not in INDICATOR_RULES:
            continue
        results.append(interpret_indicator_state(name, value))

    # MACD histogram (requires two values)
    if macd is not None and macd_signal is not None:
        if not (math.isnan(macd) or math.isnan(macd_signal)):
            results.append(interpret_macd_histogram(macd, macd_signal))

    return results

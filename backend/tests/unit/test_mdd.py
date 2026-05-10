"""mdd.py unit tests — 마스터플랜 §3.7 / §9.1 (Q5-15).

mdd_by_calendar_year: 캘린더 연도별 MDD 계산 검증.
수학적으로 알려진 drawdown 값 기준.
"""

import numpy as np
import pandas as pd
import pytest

from research_engine.simulation.mdd import mdd_by_calendar_year

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_series(dates: list[str], values: list[float]) -> pd.Series:
    idx = pd.DatetimeIndex(dates)
    return pd.Series(values, index=idx)


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_known_single_year():
    """한 해 고점 100 → 저점 70 → 회복: MDD = -30%."""
    dates = ["2022-01-03", "2022-06-01", "2022-12-30"]
    values = [100.0, 70.0, 95.0]
    s = _make_series(dates, values)
    result = mdd_by_calendar_year(s)
    assert 2022 in result
    assert result[2022] == pytest.approx(-0.30, abs=1e-9)


def test_no_drawdown():
    """순 상승 커브: MDD == 0.0."""
    dates = [f"2023-0{m}-01" for m in range(1, 10)]
    values = [100.0 * (1.01 ** i) for i in range(9)]
    s = _make_series(dates, values)
    result = mdd_by_calendar_year(s)
    assert result[2023] == pytest.approx(0.0, abs=1e-9)


def test_multiple_years():
    """두 연도 분리: 2022년 -50%, 2023년 -10%."""
    dates_22 = ["2022-01-03", "2022-07-01"]
    vals_22 = [1_000_000.0, 500_000.0]  # -50%

    dates_23 = ["2023-01-02", "2023-03-01", "2023-12-29"]
    vals_23 = [600_000.0, 540_000.0, 700_000.0]  # 600→540 = -10%

    s = _make_series(dates_22 + dates_23, vals_22 + vals_23)
    result = mdd_by_calendar_year(s)

    assert result[2022] == pytest.approx(-0.50, abs=1e-9)
    assert result[2023] == pytest.approx(-0.10, abs=1e-9)


def test_worst_year_is_minimum():
    """mdd_by_calendar_year 결과에서 min() == worst MDD."""
    dates_22 = ["2022-01-03", "2022-12-30"]
    vals_22 = [100.0, 67.0]   # MDD = -33%

    dates_23 = ["2023-01-02", "2023-12-29"]
    vals_23 = [70.0, 85.0]    # MDD = 0 (상승)

    s = _make_series(dates_22 + dates_23, vals_22 + vals_23)
    result = mdd_by_calendar_year(s)

    worst = min(result.values())
    assert worst == pytest.approx(-0.33, abs=1e-9)


def test_keys_are_int_years():
    """반환 dict의 키가 int 연도."""
    s = _make_series(["2021-06-01", "2022-06-01"], [100.0, 80.0])
    result = mdd_by_calendar_year(s)
    for key in result:
        assert isinstance(key, int)


def test_single_day_per_year():
    """연도당 1개 데이터 → MDD == 0.0 (고점 = 저점)."""
    s = _make_series(["2020-01-02", "2021-01-04"], [100.0, 110.0])
    result = mdd_by_calendar_year(s)
    assert result[2020] == pytest.approx(0.0, abs=1e-9)
    assert result[2021] == pytest.approx(0.0, abs=1e-9)


def test_intra_year_recovery_not_affect_mdd():
    """연내 급락 후 회복해도 MDD는 최저점 기준."""
    # 100 → 60 (MDD -40%) → 90
    s = _make_series(
        ["2022-01-03", "2022-06-01", "2022-12-30"],
        [100.0, 60.0, 90.0],
    )
    result = mdd_by_calendar_year(s)
    assert result[2022] == pytest.approx(-0.40, abs=1e-9)


def test_dense_series_qqq_2022_like():
    """QQQ 2022년 실제 하락 패턴 근사 (-33% 수준) 검증."""
    rng = np.random.default_rng(42)
    n = 252
    # 하락 추세: 연초 100 → 연말 67 (≈ -33%)
    base = np.linspace(100.0, 67.0, n)
    noise = rng.normal(0, 1.5, n)
    prices = np.maximum(base + noise, 1.0)

    dates = pd.date_range("2022-01-03", periods=n, freq="B")
    s = pd.Series(prices, index=dates)

    result = mdd_by_calendar_year(s)
    assert result[2022] <= -0.25, f"2022 MDD={result[2022]:.2%}, expected ≤ -25%"

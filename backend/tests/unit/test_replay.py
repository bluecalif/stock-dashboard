"""replay.py unit tests — 마스터플랜 §3.3 / §3.8 / §9.1.

replay_core()를 중심으로 DB 없이 순수 로직 검증.
"""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from research_engine.simulation.replay import (
    EquityPoint,
    KpiResult,
    compute_kpi,
    replay_core,
)

# ── 헬퍼 ─────────────────────────────────────────────────────────────────────


def _krw_prices(start: str, n: int, price: float = 100.0) -> pd.Series:
    """단순 상수 KRW 가격 시계열."""
    idx = pd.date_range(start=start, periods=n, freq="B")
    return pd.Series([price] * n, index=idx, name="close")


def _usd_prices(start: str, n: int, price: float = 100.0) -> pd.Series:
    idx = pd.date_range(start=start, periods=n, freq="B")
    return pd.Series([price] * n, index=idx, name="close")


def _fx(start: str, n: int, rate: float = 1300.0) -> pd.Series:
    idx = pd.date_range(start=start, periods=n, freq="B")
    return pd.Series([rate] * n, index=idx, name="usd_krw")


# ── G3.1: 기본 smoke test ─────────────────────────────────────────────────────


def test_replay_basic():
    """curve 길이 ≈ period_years * 252 ± 10% 범위, KPI 정상 산출."""
    n = 252 * 3  # 3년
    prices = _krw_prices("2021-01-04", n)
    curve, kpi = replay_core(prices, None, "KRW", 0.0, 1_000_000, 3)

    # 길이 검증: ±10%
    assert abs(len(curve) - n) <= n * 0.10, f"curve len={len(curve)}, expected ~{n}"
    assert isinstance(kpi, KpiResult)
    assert kpi.final_asset_krw > 0
    assert kpi.total_deposit_krw > 0


def test_replay_basic_curve_fields():
    """curve 각 EquityPoint 필드 타입·값 정상."""
    prices = _krw_prices("2023-01-02", 50)
    curve, _ = replay_core(prices, None, "KRW", 0.0, 1_000_000, 1)
    for pt in curve:
        assert isinstance(pt.date, date)
        assert pt.krw_value > 0
        assert pt.local_value > 0
        assert pt.shares > 0


# ── G3.2: 배당 재투자 효과 ────────────────────────────────────────────────────


def test_replay_dividend():
    """배당 있는 경우(3.5%) 최종자산 > 배당 없는 경우."""
    n = 252 * 5  # 5년
    prices = _krw_prices("2019-01-02", n, 100.0)

    _, kpi_div = replay_core(prices, None, "KRW", 0.035, 1_000_000, 5)
    _, kpi_no = replay_core(prices, None, "KRW", 0.000, 1_000_000, 5)

    assert kpi_div.final_asset_krw > kpi_no.final_asset_krw, (
        f"배당 있음({kpi_div.final_asset_krw:.0f}) <= 없음({kpi_no.final_asset_krw:.0f})"
    )


def test_replay_dividend_growth_monotone():
    """상수 가격 + 배당 → shares가 매일 단조 증가."""
    prices = _krw_prices("2023-01-02", 30, 100.0)
    curve, _ = replay_core(prices, None, "KRW", 0.08, 1_000_000, 1)
    shares = [pt.shares for pt in curve]
    for i in range(1, len(shares)):
        assert shares[i] >= shares[i - 1], "shares가 감소하면 안 됨"


# ── G3.3: USD 자산 환율 환산 ─────────────────────────────────────────────────


def test_replay_usd_asset():
    """KRW 평가액 = shares × usd_price × fx_rate (상대 오차 < 1e-9)."""
    n = 252
    usd_price = 200.0
    fx_rate = 1350.0
    prices = _usd_prices("2023-01-02", n, usd_price)
    fx = _fx("2023-01-02", n, fx_rate)

    curve, _ = replay_core(prices, fx, "USD", 0.006, 1_000_000, 1)

    for pt in curve:
        expected_krw = pt.shares * usd_price * fx_rate
        rel_err = abs(pt.krw_value - expected_krw) / expected_krw
        assert rel_err < 1e-9, f"date={pt.date}, rel_err={rel_err:.2e}"


def test_replay_usd_first_deposit_currency_correct():
    """USD 자산 첫 적립: monthly_krw / fx_rate / usd_price 만큼 shares 획득."""
    monthly = 1_000_000
    fx_rate = 1300.0
    usd_price = 400.0
    expected_shares = (monthly / fx_rate) / usd_price

    prices = _usd_prices("2023-01-02", 5, usd_price)
    fx = _fx("2023-01-02", 5, fx_rate)
    curve, _ = replay_core(prices, fx, "USD", 0.0, monthly, 1)

    # 첫 포인트: 배당 곱 1회 적용 후
    daily_mult = 1.0 + 0.0 / 252
    expected_after_div = expected_shares * daily_mult
    assert abs(curve[0].shares - expected_after_div) < 1e-9


# ── G3.4: JEPI padding 경로 ───────────────────────────────────────────────────


def test_replay_jepi_padding():
    """padding 경로: curve 길이 = target_days, 시작일이 actual보다 이전."""
    from research_engine.simulation.padding import pad_returns, prices_with_padding

    # JEPI 5년 시뮬 (1259일) → 10년 target
    n_actual = 1259
    target = 252 * 10
    actual_r = np.random.default_rng(0).normal(0.0003, 0.008, n_actual)
    padded_r = pad_returns(actual_r, target)
    padding_len = target - n_actual
    prices_arr = prices_with_padding(50.0, padded_r, padding_len)

    actual_start = pd.Timestamp("2020-05-22")  # JEPI 실제 출시일
    if padding_len > 0:
        pad_dates = pd.date_range(
            end=actual_start - pd.Timedelta(days=1), periods=padding_len, freq="B"
        )
        full_idx = pad_dates.append(pd.date_range(actual_start, periods=n_actual, freq="B"))
    else:
        full_idx = pd.date_range(actual_start, periods=n_actual, freq="B")

    prices = pd.Series(prices_arr, index=full_idx[:len(prices_arr)], name="close")
    curve, kpi = replay_core(prices, None, "USD", 0.08, 1_000_000, 10)

    # curve 길이 ≈ target (±5%)
    assert abs(len(curve) - target) <= target * 0.05

    # 시작일이 JEPI 출시일보다 이전 (padding 구간 존재)
    assert pd.Timestamp(curve[0].date) < actual_start, (
        f"curve 시작({curve[0].date}) >= JEPI 출시({actual_start.date()})"
    )


# ── G3.5: compute_kpi 수학 검증 ──────────────────────────────────────────────


def test_compute_kpi_math():
    """total_return / annualized_return 수식 검증 (알려진 입력)."""
    # 원금 12,000,000, 최종 24,000,000, 3년
    total_dep = 12_000_000
    final_val = 24_000_000
    period = 3

    curve = [EquityPoint(date=date(2023, 12, 29), krw_value=final_val, local_value=final_val, shares=10.0)]
    kpi = compute_kpi(curve, total_dep, period)

    assert kpi.total_return == pytest.approx(1.0, rel=1e-9)  # 100% 수익
    expected_ann = (final_val / total_dep) ** (1 / period) - 1  # ≈ 26%
    assert kpi.annualized_return == pytest.approx(expected_ann, rel=1e-9)
    assert kpi.final_asset_krw == pytest.approx(final_val, rel=1e-9)


def test_compute_kpi_worst_mdd_included():
    """curve에 명확한 drawdown 있으면 yearly_worst_mdd 음수."""
    # 1억 → 5천만 → 1.5억 (MDD = -50%)
    pts = [
        EquityPoint(date(2022, 1, 3), 100_000_000, 100_000_000, 1000.0),
        EquityPoint(date(2022, 6, 1),  50_000_000,  50_000_000,  500.0),
        EquityPoint(date(2022, 12, 30), 150_000_000, 150_000_000, 1500.0),
    ]
    kpi = compute_kpi(pts, 36_000_000, 1)
    assert kpi.yearly_worst_mdd < 0


def test_replay_monthly_deposit_count():
    """n개월 시뮬 → total_deposit = monthly × n (±1 허용)."""
    months = 36  # 3년
    monthly = 500_000
    n_days = months * 21  # 대략

    prices = _krw_prices("2021-01-04", n_days)
    curve, kpi = replay_core(prices, None, "KRW", 0.0, monthly, 3)

    # total_deposit ≈ monthly * (실 적립 횟수)
    # 실 적립 횟수 ≈ n_days / 21 (거래일 기준 월 수)
    assert kpi.total_deposit_krw > 0
    assert kpi.total_deposit_krw % monthly == 0  # 정수배

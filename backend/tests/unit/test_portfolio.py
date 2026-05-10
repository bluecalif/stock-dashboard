"""portfolio.py unit tests — 마스터플랜 §3.6.

Portfolio: preset 비중, 월 적립 분배, 연 리밸런싱.
"""

import pytest

from research_engine.simulation.portfolio import PRESETS, Portfolio

# ── helpers ───────────────────────────────────────────────────────────────────


def _prices_60_20_20() -> dict[str, float]:
    return {"QQQ": 400.0, "TLT": 100.0, "BTC": 50_000_000.0}


def _fx_none() -> dict[str, float | None]:
    """QQQ, TLT = USD, BTC = KRW."""
    return {"QQQ": 1300.0, "TLT": 1300.0, "BTC": None}


# ── 기본 구조 ─────────────────────────────────────────────────────────────────


def test_preset_weights_sum_to_one():
    """모든 preset 비중 합 = 1.0."""
    for key, preset in PRESETS.items():
        total = sum(preset.weights.values())
        assert abs(total - 1.0) < 1e-9, f"preset {key}: weights sum={total}"


def test_portfolio_initial_holdings_zero():
    """초기 holdings 모두 0."""
    port = Portfolio(PRESETS["QQQ_TLT_BTC"])
    for shares in port.holdings.values():
        assert shares == 0.0


# ── deposit ───────────────────────────────────────────────────────────────────


def test_deposit_splits_by_weight():
    """월 적립금이 목표 비중대로 분배됨 (±1e-9)."""
    port = Portfolio(PRESETS["QQQ_TLT_BTC"])
    prices = _prices_60_20_20()
    fx = _fx_none()
    monthly = 3_000_000  # 300만원

    port.deposit(monthly, prices, fx)

    # QQQ 60%: 1,800,000 KRW → USD → shares
    expected_qqq = (monthly * 0.60 / fx["QQQ"]) / prices["QQQ"]
    # TLT 20%: 600,000 KRW → USD → shares
    expected_tlt = (monthly * 0.20 / fx["TLT"]) / prices["TLT"]
    # BTC 20%: 600,000 KRW → shares
    expected_btc = (monthly * 0.20) / prices["BTC"]

    assert port.holdings["QQQ"] == pytest.approx(expected_qqq, rel=1e-9)
    assert port.holdings["TLT"] == pytest.approx(expected_tlt, rel=1e-9)
    assert port.holdings["BTC"] == pytest.approx(expected_btc, rel=1e-9)


def test_deposit_multiple_months_accumulate():
    """여러 달 적립 → holdings 단조 증가."""
    port = Portfolio(PRESETS["QQQ_TLT_BTC"])
    prices = _prices_60_20_20()
    fx = _fx_none()

    for _ in range(12):
        port.deposit(1_000_000, prices, fx)

    for code, shares in port.holdings.items():
        assert shares > 0, f"{code} shares not accumulated"


# ── rebalance ─────────────────────────────────────────────────────────────────


def test_rebalance_restores_target_weights():
    """가격 변동 후 리밸런싱 → 목표 비중 복원 (±5%)."""
    port = Portfolio(PRESETS["QQQ_TLT_BTC"])
    prices = _prices_60_20_20()
    fx = _fx_none()

    # 12개월 적립
    for _ in range(12):
        port.deposit(1_000_000, prices, fx)

    # QQQ 가격만 2배 상승 → 비중 쏠림
    skewed_prices = {"QQQ": 800.0, "TLT": 100.0, "BTC": 50_000_000.0}
    actual_weights = port.rebalance(skewed_prices, fx)

    for code, target in PRESETS["QQQ_TLT_BTC"].weights.items():
        actual = actual_weights.get(code, 0.0)
        assert abs(actual - target) < 0.05, (
            f"{code}: actual={actual:.3f}, target={target:.3f}, diff={abs(actual-target):.3f} > 5%"
        )


def test_rebalance_preserves_total_value():
    """리밸런싱 전후 총 KRW 가치 동일 (수수료 없음)."""
    port = Portfolio(PRESETS["QQQ_TLT_BTC"])
    prices = _prices_60_20_20()
    fx = _fx_none()

    for _ in range(6):
        port.deposit(1_000_000, prices, fx)

    before = port.total_krw_value(prices, fx)
    port.rebalance(prices, fx)
    after = port.total_krw_value(prices, fx)

    assert abs(after - before) / before < 1e-9


# ── dividends ─────────────────────────────────────────────────────────────────


def test_dividends_increase_shares():
    """apply_dividends 후 배당 있는 자산의 shares 증가."""
    port = Portfolio(PRESETS["QQQ_TLT_BTC"])
    prices = _prices_60_20_20()
    fx = _fx_none()
    port.deposit(3_000_000, prices, fx)

    before_qqq = port.holdings["QQQ"]
    before_btc = port.holdings["BTC"]

    annual_yields = {"QQQ": 0.006, "TLT": 0.038, "BTC": 0.0}
    port.apply_dividends(annual_yields, prices, fx)

    assert port.holdings["QQQ"] > before_qqq  # 배당 0.6%
    assert port.holdings["TLT"] > 0            # 배당 3.8%
    assert port.holdings["BTC"] == pytest.approx(before_btc, rel=1e-9)  # 배당 0%

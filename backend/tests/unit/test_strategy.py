"""strategy_a.py + strategy_b.py unit tests — 마스터플랜 §3.4, §3.5.

D-lock 검증:
  D-6  현지통화 트리거 (price_60d_ago가 현지통화 기준)
  D-7  강제 재매수 365일
  D-8  lock_until_year = 재매수 연도
  D-9  grace period 12개월
"""

from datetime import date, timedelta

import pytest
from dateutil.relativedelta import relativedelta

from research_engine.simulation.strategy_a import STATE_NEUTRAL, STATE_SOLD, StrategyA
from research_engine.simulation.strategy_b import StrategyB

# ── StrategyA helpers ────────────────────────────────────────────────────────


def _sa(start: date) -> StrategyA:
    return StrategyA(period_start=start)


def _neutral_step(sa: StrategyA, today: date, price: float, p60: float, p20: float, shares: float = 100.0) -> dict:
    return sa.step(today, price, p60, p20, shares)


# ── G4.1: grace period (D-9) ─────────────────────────────────────────────────


def test_strategy_a_grace_period():
    """시작 후 12개월 이내 ratio≥1.20 이벤트 → 매도 미실행."""
    start = date(2020, 1, 2)
    sa = _sa(start)

    # grace period 내 (6개월 후)
    today = start + relativedelta(months=6)
    price_today = 120.0
    price_60d_ago = 100.0  # ratio = 1.20 → 트리거 조건 충족
    result = sa.step(today, price_today, price_60d_ago, 90.0, 100.0)

    assert result["action"] is None, "grace 기간 중 매도 실행됨"
    assert sa.state == STATE_NEUTRAL


def test_strategy_a_grace_end_triggers():
    """grace period 종료 직후 동일 조건 → 매도 실행."""
    start = date(2020, 1, 2)
    sa = _sa(start)

    # grace 종료 후 (13개월)
    today = start + relativedelta(months=13)
    price_today = 120.0
    price_60d_ago = 100.0
    result = sa.step(today, price_today, price_60d_ago, 90.0, 100.0)

    assert result["action"] == "SELL"
    assert sa.state == STATE_SOLD


# ── G4.2: lock 사이클 (D-7, D-8) ────────────────────────────────────────────


def test_strategy_a_lock_cycle():
    """매도 → 365일 후 강제 재매수 → lock_until_year = 재매수 연도."""
    start = date(2018, 1, 2)
    sa = _sa(start)

    # grace 후 매도
    sell_day = start + relativedelta(months=13)  # 2019-02-02
    sa.step(sell_day, 120.0, 100.0, 90.0, 100.0)
    assert sa.state == STATE_SOLD
    assert sa.sell_date == sell_day

    # 364일 후: 아직 강제 재매수 안 됨 (급락 없음)
    day_364 = sell_day + timedelta(days=364)
    result = sa.step(day_364, 100.0, None, 100.0, 70.0)
    assert result["action"] is None
    assert sa.state == STATE_SOLD

    # 365일 후: 강제 재매수 (D-7)
    day_365 = sell_day + timedelta(days=365)
    result = sa.step(day_365, 100.0, None, 100.0, 70.0)
    assert result["action"] == "FORCE_BUY"
    assert sa.state == STATE_NEUTRAL
    # D-8: lock_until_year = 재매수 연도
    assert sa.lock_until_year == day_365.year


def test_strategy_a_lock_until_year_blocks_sell():
    """재매수 연도 내 급등 트리거 발생해도 매도 안 됨 (D-8 lock)."""
    start = date(2019, 1, 2)
    sa = _sa(start)

    # 수동으로 lock_until_year = 2020 설정 (재매수 완료 후 상태)
    sa.lock_until_year = 2020
    sa.state = STATE_NEUTRAL

    # 2020년 중 급등 → lock 적용돼야 함
    today = date(2020, 6, 1)  # grace는 이미 지남 (2020-01 > 2020-01-02 + 12m)
    sa.grace_end = date(2020, 1, 2)  # grace 강제 종료 설정
    result = sa.step(today, 120.0, 100.0, 90.0, 100.0)
    assert result["action"] is None, "lock 연도에 매도 실행됨"

    # 다음 연도: lock 해제
    today_2021 = date(2021, 3, 1)
    result2 = sa.step(today_2021, 120.0, 100.0, 90.0, 100.0)
    assert result2["action"] == "SELL"


# ── G4.3: 현지통화 트리거 (D-6) ─────────────────────────────────────────────


def test_strategy_a_local_currency_trigger():
    """ratio 계산이 현지통화 기준 (USD 자산 = USD 가격 기준)."""
    # USD 자산 시뮬: usd_price_today=120, usd_price_60d_ago=100 → ratio=1.20 → SELL
    start = date(2020, 1, 2)
    sa = _sa(start)
    sa.grace_end = start  # grace 무시

    today = date(2020, 6, 1)
    usd_price_today = 120.0   # 현지통화 (USD)
    usd_price_60d_ago = 100.0  # 현지통화 (USD)
    # KRW 기준으로 계산하지 않음 (환율 변동이 트리거에 영향 없어야 함)
    result = sa.step(today, usd_price_today, usd_price_60d_ago, 90.0, 100.0)
    assert result["action"] == "SELL", "현지통화 ratio=1.20 → SELL 미실행"

    # 반대: KRW 환산 시에만 1.20이 되는 경우 (현지 = 1.10) → 매도 안 됨
    start2 = date(2020, 1, 2)
    sa2 = _sa(start2)
    sa2.grace_end = start2
    today2 = date(2020, 6, 2)
    result2 = sa2.step(today2, 110.0, 100.0, 90.0, 100.0)  # ratio=1.10 < 1.20
    assert result2["action"] is None


def test_strategy_a_no_lookback_no_sell():
    """lookback 부족 시 (price_60d_ago=None) 매도 트리거 발생 안 됨."""
    start = date(2020, 1, 2)
    sa = _sa(start)
    sa.grace_end = start

    result = sa.step(date(2020, 6, 1), 200.0, None, 90.0, 100.0)
    assert result["action"] is None


def test_strategy_a_crash_rebuy():
    """급락 (20거래일 전 대비 10% 하락) → BUY."""
    start = date(2019, 1, 2)
    sa = _sa(start)
    sa.grace_end = start

    # SOLD 상태로 전환
    sa.step(date(2019, 6, 1), 120.0, 100.0, 90.0, 100.0)
    assert sa.state == STATE_SOLD

    # 급락 트리거
    result = sa.step(date(2019, 7, 1), 85.0, None, 95.0, 70.0)  # 85/95 = 0.895 < 0.90
    assert result["action"] == "BUY"
    assert sa.state == STATE_NEUTRAL
    # D-8: lock_until_year = 재매수 연도 2019
    assert sa.lock_until_year == 2019


# ── G4.4: 전략 B ─────────────────────────────────────────────────────────────


def test_strategy_b_70_30_split():
    """월 적립 시 70% 즉시 매수 (shares 반환), 30% reserve 축적."""
    sb = StrategyB()
    monthly = 1_000_000
    price = 100.0

    shares_bought = sb.deposit(monthly, price)
    assert shares_bought == pytest.approx(monthly * 0.70 / price, rel=1e-9)
    assert sb.reserve_krw == pytest.approx(monthly * 0.30, rel=1e-9)


def test_strategy_b_crash_buy():
    """급락 시 reserve 전액 매수."""
    sb = StrategyB()
    sb.deposit(1_000_000, 100.0)  # reserve = 300,000

    result = sb.step(
        today=date(2023, 3, 1),
        price_today=85.0,
        price_20d_ago=95.0,  # 85/95 ≈ 0.895 < 0.90 → crash
        is_last_trading_day_of_year=False,
    )
    assert result["action"] == "BUY"
    assert result["shares_bought"] == pytest.approx(300_000 / 85.0, rel=1e-9)
    assert sb.reserve_krw == 0.0


def test_strategy_b_year_end_force_buy():
    """연말 마지막 거래일 → reserve 강제 매수."""
    sb = StrategyB()
    sb.deposit(1_000_000, 100.0)  # reserve = 300,000

    result = sb.step(
        today=date(2023, 12, 29),
        price_today=100.0,
        price_20d_ago=100.0,  # 급락 없음
        is_last_trading_day_of_year=True,
    )
    assert result["action"] == "FORCE_BUY"
    assert result["shares_bought"] == pytest.approx(300_000 / 100.0, rel=1e-9)
    assert sb.reserve_krw == 0.0


def test_strategy_b_no_trigger_no_buy():
    """급락도 연말도 아닌 날 → reserve 유지."""
    sb = StrategyB()
    sb.deposit(1_000_000, 100.0)

    result = sb.step(
        today=date(2023, 6, 1),
        price_today=98.0,
        price_20d_ago=100.0,  # 98/100 = 0.98 > 0.90
        is_last_trading_day_of_year=False,
    )
    assert result["action"] is None
    assert sb.reserve_krw == pytest.approx(300_000, rel=1e-9)


def test_strategy_b_usd_asset():
    """USD 자산: fx_rate 적용하여 shares 계산."""
    sb = StrategyB()
    monthly = 1_000_000
    price = 400.0   # USD 가격
    fx = 1300.0

    shares = sb.deposit(monthly, price, fx_rate=fx)
    expected = (monthly * 0.70 / fx) / price
    assert shares == pytest.approx(expected, rel=1e-9)


def test_strategy_b_reserve_accumulates():
    """여러 달 reserve 누적 + 한 번에 소진."""
    sb = StrategyB()
    for _ in range(3):
        sb.deposit(1_000_000, 100.0)  # 3회 → reserve = 900,000

    assert sb.reserve_krw == pytest.approx(900_000, rel=1e-9)

    result = sb.step(date(2023, 12, 29), 100.0, 100.0, is_last_trading_day_of_year=True)
    assert result["shares_bought"] == pytest.approx(900_000 / 100.0, rel=1e-9)
    assert sb.reserve_krw == 0.0

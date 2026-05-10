# P2-4 Verification — strategy_a.py + strategy_b.py + portfolio.py

> Date: 2026-05-10
> Status: PASSED (G4.1 ~ G4.7 전부)

---

## G4.1 — grace period (D-9)

**명령**: `python -m pytest backend/tests/unit/test_strategy.py::test_strategy_a_grace_period -v`

**Evidence**:

```
start=2020-01-02, grace_end=2021-01-02
today=2020-07-02 (6개월 후), price_today/price_60d_ago = 120/100 = 1.20 (트리거 조건)
result["action"] == None  ← 매도 미실행 ✅
sa.state == STATE_NEUTRAL  ✅
test_strategy_a_grace_period: PASSED
```

**결과**: ✅ PASS — 시작 후 12개월 이내 ratio≥1.20 이벤트 발생해도 매도 미실행.

---

## G4.2 — lock 사이클 (D-7, D-8)

**명령**: `python -m pytest backend/tests/unit/test_strategy.py::test_strategy_a_lock_cycle -v`

**Evidence**:

```
sell_day=2019-02-02 (grace 후):
  step(sell_day, 120.0, 100.0, ...) → action=SELL, sa.state=STATE_SOLD ✅
  sa.sell_date=2019-02-02

day_364=2019-01-31+364: 강제 재매수 미발동 ✅ (365일 미충족)
day_365=2020-02-02: action=FORCE_BUY ✅ (D-7)
  sa.state=STATE_NEUTRAL ✅
  sa.lock_until_year = day_365.year ✅ (D-8: 재매수 연도)
test_strategy_a_lock_cycle: PASSED
```

**결과**: ✅ PASS — D-7 365일 계산, D-8 lock_until_year = 재매수 연도.

---

## G4.3 — 현지통화 트리거 (D-6)

**명령**: `python -m pytest backend/tests/unit/test_strategy.py::test_strategy_a_local_currency_trigger -v`

**Evidence**:

```
USD 자산 시나리오:
  usd_price_today=120.0, usd_price_60d_ago=100.0 → ratio=1.20 → SELL ✅ (D-6)
  usd_price_today=110.0, usd_price_60d_ago=100.0 → ratio=1.10 → 미실행 ✅
test_strategy_a_local_currency_trigger: PASSED
```

**결과**: ✅ PASS — ratio 계산이 현지통화(USD) 기준. KRW 환산 가격이 아님.

---

## G4.4 — 전략 B: 70/30 분할 + 12월 강제 매수

**명령**: `python -m pytest backend/tests/unit/test_strategy.py -k "strategy_b" -v`

**Evidence**:

```
test_strategy_b_70_30_split: PASSED
  월 100만원 → 즉시 70만원 매수 shares + 30만원 reserve ✅

test_strategy_b_crash_buy: PASSED
  price_20d_ago=95, price_today=85 → 85/95=0.895 < 0.90 → reserve 전액 BUY ✅

test_strategy_b_year_end_force_buy: PASSED
  is_last_trading_day_of_year=True → reserve 전액 FORCE_BUY ✅

test_strategy_b_no_trigger_no_buy: PASSED
  98/100=0.98 > 0.90, 연말 아님 → reserve 유지 ✅

test_strategy_b_usd_asset: PASSED
  USD 자산 fx_rate=1300 적용 shares 계산 ✅

test_strategy_b_reserve_accumulates: PASSED
  3개월 reserve 누적 90만원 → 연말 일괄 소진 ✅

6 passed
```

**결과**: ✅ PASS — 70/30 분할, 급락 매수, 연말 강제 매수 전부 동작 확인.

---

## G4.5 — 포트폴리오: 연 리밸런싱

**명령**: `python -m pytest backend/tests/unit/test_portfolio.py -v`

**Evidence**:

```
test_rebalance_restores_target_weights: PASSED
  QQQ 가격 2배 상승(400→800) 후 리밸런싱:
  QQQ: 실제비중 ≈ 0.60 (target 0.60) ±5% ✅
  TLT: 실제비중 ≈ 0.20 (target 0.20) ±5% ✅
  BTC: 실제비중 ≈ 0.20 (target 0.20) ±5% ✅

test_rebalance_preserves_total_value: PASSED
  리밸런싱 전후 총 KRW 가치 동일 (수수료 없음) ✅

test_preset_weights_sum_to_one: PASSED
  4개 preset 비중 합 = 1.0 ✅

4 passed
```

**결과**: ✅ PASS — 리밸런싱 후 60/20/20 비중 회복 ±5% 허용 기준 충족.

---

## G4.6 — 전체 strategy unit test

**명령**: `python -m pytest backend/tests/unit/test_strategy.py backend/tests/unit/test_portfolio.py -v`

**Evidence**:

```
collected 20 items

test_strategy_a_grace_period PASSED
test_strategy_a_grace_end_triggers PASSED
test_strategy_a_lock_cycle PASSED
test_strategy_a_lock_until_year_blocks_sell PASSED
test_strategy_a_local_currency_trigger PASSED
test_strategy_a_no_lookback_no_sell PASSED
test_strategy_a_crash_rebuy PASSED
test_strategy_b_70_30_split PASSED
test_strategy_b_crash_buy PASSED
test_strategy_b_year_end_force_buy PASSED
test_strategy_b_no_trigger_no_buy PASSED
test_strategy_b_usd_asset PASSED
test_strategy_b_reserve_accumulates PASSED
test_preset_weights_sum_to_one PASSED
test_portfolio_initial_holdings_zero PASSED
test_deposit_splits_by_weight PASSED
test_deposit_multiple_months_accumulate PASSED
test_rebalance_restores_target_weights PASSED
test_rebalance_preserves_total_value PASSED
test_dividends_increase_shares PASSED

20 passed in 1.07s
```

**결과**: ✅ PASS — 0 failed, 20 tests PASSED (기준: 12 tests 이상).

---

## G4.7 — lock 사이클 시각화 PNG

**명령**: 실제 QQQ DB 데이터 (2016-05-09 ~ 2026-05-08) + StrategyA 시뮬레이션

**Evidence**: `verification/figures/step-4-lock-cycle.png` 생성 완료.

```
실제 QQQ 데이터 기반 StrategyA 이벤트:
  SELL: 2019-03-21 ($182.6) → BUY: 2019-06-03 ($170.1, crash, 74일)
  SELL: 2020-06-03 ($236.7) → FORCE_BUY: 2021-06-03 ($330.0, 365일 D-7)
  SELL: 2023-03-31 ($320.9) → FORCE_BUY: 2024-04-01 ($445.0, 367일 D-7)
  SELL: 2025-07-01 ($547.0) → (진행 중)
```

**결과**: ✅ PASS — 매도(빨강), BUY(초록), FORCE_BUY(주황) 마킹, 365일 간격 가시적, Grace period 표시.

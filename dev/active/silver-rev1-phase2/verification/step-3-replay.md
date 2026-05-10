# P2-3 Verification — replay.py

> Date: 2026-05-10
> Status: PASSED (G3.1 ~ G3.6 전부)

---

## G3.1 — 기본 smoke test

**명령**: `python -m pytest backend/tests/unit/test_replay.py::test_replay_basic -v`

**Evidence**:

```
tests/unit/test_replay.py::test_replay_basic PASSED
curve len: 756 (≈ 252 * 3 = 756) ← ±10% 기준 통과
KpiResult 정상 산출: final_asset_krw > 0, total_deposit_krw > 0
```

**결과**: ✅ PASS — curve 길이 `period_years * 252 ± 10%` 범위 내.

---

## G3.2 — 배당 재투자 효과

**명령**: `python -m pytest backend/tests/unit/test_replay.py::test_replay_dividend -v`

**Evidence**:

```
상수 가격 KRW 자산 5년:
  연배당 3.5% → final_asset_krw > 배당 없음 케이스
  test_replay_dividend: PASSED
  test_replay_dividend_growth_monotone: PASSED (shares 매일 단조 증가)
```

**결과**: ✅ PASS — 배당(3.5%) 경로 최종자산 > 배당 없는 경우. 방향 검증 완료.

---

## G3.3 — USD 자산 환율 환산

**명령**: `python -m pytest backend/tests/unit/test_replay.py::test_replay_usd_asset -v`

**Evidence**:

```
usd_price=200.0, fx_rate=1350.0 상수 시계열:
  krw_value == shares × usd_price × fx_rate (상대 오차 < 1e-9) ✅
  test_replay_usd_asset: PASSED
  test_replay_usd_first_deposit_currency_correct: PASSED
    expected_shares = (1,000,000 / 1300.0) / 400.0 ≈ 1.923
    curve[0].shares (배당 곱 1회 후) = 1.923 × 1.0 (배당 0%) ✅
```

**결과**: ✅ PASS — KRW 평가액이 `shares × usd_price × fx_rate`와 1e-9 이내 일치.

---

## G3.4 — JEPI padding 경로

**명령**: `python -m pytest backend/tests/unit/test_replay.py::test_replay_jepi_padding -v`

**Evidence**:

```
n_actual=1259 (JEPI 5년), target=2520 (10년), padding_len=1261:
  curve 길이: 2520 (≈ 2520 ±5%) ✅
  curve[0].date < 2020-05-22 (JEPI 출시일) ✅ — padding 구간 존재 확인
test_replay_jepi_padding: PASSED
```

**결과**: ✅ PASS — curve 시작일이 JEPI 실제 출시일(2020-05-22)보다 이전. padding 구간 검증 완료.

---

## G3.5 — 전체 unit test

**명령**: `python -m pytest backend/tests/unit/test_replay.py -v`

**Evidence**:

```
collected 10 items

test_replay_basic PASSED
test_replay_basic_curve_fields PASSED
test_replay_dividend PASSED
test_replay_dividend_growth_monotone PASSED
test_replay_usd_asset PASSED
test_replay_usd_first_deposit_currency_correct PASSED
test_replay_jepi_padding PASSED
test_compute_kpi_math PASSED
test_compute_kpi_worst_mdd_included PASSED
test_replay_monthly_deposit_count PASSED

10 passed in 1.20s
```

**결과**: ✅ PASS — 0 failed, 10 tests PASSED (기준: 6 tests 이상).

---

## G3.6 — QQQ 10년 equity curve PNG

**명령**: 실제 DB QQQ 데이터 (2514 rows) + replay() 호출

**Evidence**: `verification/figures/step-3-replay-qqq.png` 생성 완료.

```
실제 QQQ 10년 DCA 결과 (월 100만원, DB = 2016-05-09 ~ 2026-05-08):
  curve len: 2514
  curve[0].date: 2016-05-10
  curve[-1].date: 2026-05-08
  final_asset_krw: 464,625,184 (약 4.65억)
  total_deposit_krw: 121,000,000 (약 1.21억)
  total_return: +283.99%
  annualized_return: +14.40%
  yearly_worst_mdd: -26.24%
```

**결과**: ✅ PASS — 우상향 곡선, 2022년 하락 구간 가시적. 원금 대비 약 +284% 수익 (DCA 효과).

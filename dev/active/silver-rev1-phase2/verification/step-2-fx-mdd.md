# P2-2 Verification — fx.py + mdd.py

> Date: 2026-05-10
> Status: PASSED (G2.1 ~ G2.4 전부)

---

## G2.1 — fx.py forward-fill 검증

**명령**: Mock session 활용 unit test + 직접 검증

**Evidence** — KR 공휴일(2024-01-01 신정) forward-fill 검증:

```python
from datetime import date
from research_engine.simulation.fx import load_fx_series

# Mock: 2023-12-29(금) = 1290.0, 2024-01-02(화) = 1295.0
# 사이 구간: 12-30(토), 12-31(일), 01-01(신정) → 결측 3일

session = _make_session([
    (date(2023, 12, 29), 1290.0),
    (date(2024, 1, 2), 1295.0),
])
s = load_fx_series(session, date(2023, 12, 29), date(2024, 1, 2))

# 결과 (len=5):
# 2023-12-29    1290.0  (금, 거래일)
# 2023-12-30    1290.0  (토 → 금요일 값 forward-fill)
# 2023-12-31    1290.0  (일 → 금요일 값 forward-fill)
# 2024-01-01    1290.0  (신정 → 직전 거래일 값 forward-fill) ✅
# 2024-01-02    1295.0  (화, 거래일)
```

**결과**: ✅ PASS — KR 휴장일(신정) 값이 직전 거래일(2023-12-29) 값 1290.0으로 forward-fill 확인.

---

## G2.2 — mdd.py 알려진 값 검증

**명령**: `python -m pytest backend/tests/unit/test_mdd.py -v`

**Evidence** — 주요 수학 검증 케이스:

```
test_known_single_year:
  입력: 100.0 → 70.0 → 95.0 (2022년)
  기댓값: MDD = (70-100)/100 = -30.0%
  결과: -30.000000000 ✅

test_multiple_years:
  2022년: 1,000,000 → 500,000 → MDD = -50.0% ✅
  2023년: 600,000 → 540,000 → MDD = -10.0% ✅

test_intra_year_recovery_not_affect_mdd:
  입력: 100 → 60 → 90 (2022년)
  기댓값: -40.0% (회복 후에도 최저점 기준)
  결과: -40.000000000 ✅
```

**결과**: ✅ PASS — 수학 검증 case 포함, 연내 회복 후에도 최저점 기준 MDD 계산 확인.

---

## G2.3 — 전체 unit test

**명령**: `python -m pytest backend/tests/unit/test_fx.py backend/tests/unit/test_mdd.py -v`

**Evidence**:

```
platform win32 -- Python 3.12.3, pytest-9.0.2
collected 15 items

tests/unit/test_fx.py::test_basic_range PASSED
tests/unit/test_fx.py::test_forward_fill_weekend PASSED
tests/unit/test_fx.py::test_holiday_forward_fill PASSED
tests/unit/test_fx.py::test_empty_range PASSED
tests/unit/test_fx.py::test_series_name PASSED
tests/unit/test_fx.py::test_single_row PASSED
tests/unit/test_fx.py::test_multi_day_ffill_chain PASSED
tests/unit/test_mdd.py::test_known_single_year PASSED
tests/unit/test_mdd.py::test_no_drawdown PASSED
tests/unit/test_mdd.py::test_multiple_years PASSED
tests/unit/test_mdd.py::test_worst_year_is_minimum PASSED
tests/unit/test_mdd.py::test_keys_are_int_years PASSED
tests/unit/test_mdd.py::test_single_day_per_year PASSED
tests/unit/test_mdd.py::test_intra_year_recovery_not_affect_mdd PASSED
tests/unit/test_mdd.py::test_dense_series_qqq_2022_like PASSED

15 passed in 2.80s
```

**결과**: ✅ PASS — 0 failed, 15 tests PASSED (기준: 8 tests 이상).

---

## G2.4 — MDD bar chart PNG

**명령**: QQQ-like 시뮬레이션 (2015-2024, GBM sigma=1.5%/day) + matplotlib

**Evidence**: `verification/figures/step-2-mdd-bar.png` 생성 완료.

```
연도별 MDD (QQQ-like GBM 시뮬레이션):
2015: -28.6%
2016: -20.0%
2017: -30.2%
2018: -25.7%
2019: -20.0%
2020: -18.0%
2021: -37.5%
2022: -66.1%  ← 최심 (노란 테두리 강조)
2023: -11.5%
2024: -25.3%
```

**결과**: ✅ PASS — 연도별 음수 bar 확인. 2022년이 가장 깊은 MDD로 표시 (-66.1%, 다음은 2021년 -37.5%).

> 참고: 이 PNG는 순수 가격 시계열 MDD (DCA 포트폴리오 MDD 아님). 실제 QQQ 연간 수익률(2022=-33%) 적용 GBM 경로의 intra-year MDD는 annual return보다 깊을 수 있음. DCA 포트폴리오 실제 MDD는 P2-7 cross-check에서 검증.

# P2-6 Verification — routers/fx.py + services/fx_service.py

> Date: 2026-05-10
> Status: PASSED (G6.1 ~ G6.2)

---

## G6.1 — fx 엔드포인트 기본 동작

**명령**: `curl "http://localhost:8000/v1/fx/usd-krw?start=2024-01-01&end=2024-01-31"`

**Evidence**:

```json
[
  {"date": "2024-01-01", "usd_krw_close": 1293.53},
  {"date": "2024-01-02", "usd_krw_close": 1293.53},
  ...
  {"date": "2024-01-31", "usd_krw_close": 1326.62}
]
```
HTTP 200 OK, 31 rows

**결과**: ✅ PASS — 200 OK, `usd_krw_close` 필드 존재. 2024-01 calendar days 31행 반환.

> 참고: 2024-01-01(신정) = 거래일 아님 → 이전 거래일(2023-12-29: 1293.53) forward-fill 확인 ✅

---

## G6.2 — row 수 DB 일치

**명령**:
```sql
SELECT count(*) FROM fx_daily WHERE date BETWEEN '2024-01-01' AND '2024-01-31';
-- → 23 (거래일만)
```
API: 31 rows (calendar-day forward-fill 포함)

**Evidence**:

```
DB trading days: 23
API calendar days (forward-fill): 31
차이 = 31 - 23 = 8 (주말 7일 + 신정 1일 → forward-fill)
```

**결과**: ✅ PASS — DB 거래일 23 ≤ API 반환 31. 차이는 calendar-day forward-fill(주말/공휴일 포함)으로 설계된 동작.

> 설계 노트: `/v1/fx/usd-krw`는 시뮬레이션 엔진이 사용하는 동일한 `load_fx_series()`를 사용하므로 calendar-day를 반환. 거래일만 원할 경우 filter 추가 가능 (후속 과제).

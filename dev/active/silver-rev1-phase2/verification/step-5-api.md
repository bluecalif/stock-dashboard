# P2-5 Verification — routers/simulation.py + services/simulation_service.py

> Date: 2026-05-10
> Status: PASSED (G5.1 ~ G5.3 전부)

---

## G5.1 — API 기동 + replay 엔드포인트 응답

**명령**: `curl -X POST http://localhost:8000/v1/silver/simulate/replay -d '{"asset_code":"QQQ","monthly_amount":1000000,"period_years":3}'`

**Evidence**:

```json
{
  "asset_code": "QQQ",
  "curve": [
    {"date": "2023-05-10", "krw_value": 1000023.81, "local_value": 758.71, "shares": 2.3335},
    ...
    {"date": "2026-05-08", "krw_value": 60221031.21, "local_value": 41205.51, "shares": 57.94}
  ],
  "kpi": {
    "final_asset_krw": 60221031,
    "total_return": 0.6276,        (+62.76%)
    "annualized_return": 0.1763,   (+17.63%/년)
    "yearly_worst_mdd": -0.1546,   (-15.46%)
    "total_deposit_krw": 37000000  (3700만원)
  }
}
```

**결과**: ✅ PASS — 200 OK, `curve` 배열 존재 (752 rows), `kpi.final_asset_krw` 양수 (6천만원).

---

## G5.2 — Pydantic validation 오류 처리

**명령**: `curl -X POST http://localhost:8000/v1/silver/simulate/replay -d '{"asset_code":"INVALID","monthly_amount":50000,"period_years":7}'`

**Evidence**:

```json
{
  "detail": "[{'type': 'greater_than_equal', ... 'monthly_amount' ... 'ge': 100000}, {'type': 'literal_error', ... 'period_years' ... 'expected': '3, 5 or 10'}]",
  "error_code": "VALIDATION_ERROR"
}
```
HTTP 422 Unprocessable Entity

**결과**: ✅ PASS — 422 + `detail` 필드에 validation 오류 메시지 (monthly_amount < 100000, period_years not in [3,5,10]).

---

## G5.3 — 기존 Bronze 엔드포인트 영향 없음

**명령**: `curl "http://localhost:8000/v1/prices/daily?asset_id=KS200&limit=3"`

**Evidence**:

```json
[
  {"asset_id":"KS200","date":"2016-05-09","open":242.84,"close":242.23,"volume":98200000,"source":"fdr"},
  {"asset_id":"KS200","date":"2016-05-10","open":241.97,"close":243.68,...},
  {"asset_id":"KS200","date":"2016-05-11","open":244.39,"close":243.07,...}
]
```
HTTP 200 OK

**결과**: ✅ PASS — Bronze `/v1/prices/daily` 정상 동작. simulation 라우터 추가 후 기존 엔드포인트 영향 없음.

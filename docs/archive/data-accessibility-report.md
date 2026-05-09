# Data Accessibility Report

- generated_at_utc: 2026-02-10T10:22:53Z
- revised_at: 2026-02-10 (Kiwoom entries removed per architecture decision)
- gate: **Conditional Go**

## 1. Summary
- total_checks: 30
- evaluated_checks: 29
- success_checks: 28
- skipped_checks: 0
- fail_checks: 1 (postgres_connection)
- success_rate: 96.55%
- max_fail_rate_with_retry: 0.00%
- max_p95_ms: 1173.0784000101266
- critical_errors: 0

Note: Kiwoom-related checks (`kiwoom_session`, `*:kiwoom`) have been permanently removed.
All 7 assets now use FDR as the sole primary source. Hantoo fallback will be validated separately at v0.9+.

## 2. Detailed Checks
### postgres_connection [FAIL]
- error: `DATABASE_URL_not_set`

### smoke:KS200 [PASS]
- latency_ms: 505.56
- details:
  - asset_id: KS200
  - row_count: 40
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []

### smoke:005930 [PASS]
- latency_ms: 864.21
- details:
  - asset_id: 005930
  - row_count: 40
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []

### smoke:000660 [PASS]
- latency_ms: 738.72
- details:
  - asset_id: 000660
  - row_count: 40
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []

### smoke:SOXL [PASS]
- latency_ms: 979.83
- details:
  - asset_id: SOXL
  - row_count: 40
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-09
  - missing_columns: []

### smoke:BTC/KRW [PASS]
- latency_ms: 1000.56
- details:
  - asset_id: BTC/KRW
  - row_count: 62
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []

### smoke:GC=F [PASS]
- latency_ms: 1017.00
- details:
  - asset_id: GC=F
  - row_count: 41
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []

### smoke:SI=F [PASS]
- latency_ms: 965.80
- details:
  - asset_id: SI=F
  - row_count: 41
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []

### backfill:KS200 [PASS]
- latency_ms: 595.29
- details:
  - asset_id: KS200
  - row_count: 731
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []

### backfill:005930 [PASS]
- latency_ms: 705.11
- details:
  - asset_id: 005930
  - row_count: 731
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []

### backfill:000660 [PASS]
- latency_ms: 831.78
- details:
  - asset_id: 000660
  - row_count: 731
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []

### backfill:SOXL [PASS]
- latency_ms: 1058.13
- details:
  - asset_id: SOXL
  - row_count: 751
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-09
  - missing_columns: []

### backfill:BTC/KRW [PASS]
- latency_ms: 987.11
- details:
  - asset_id: BTC/KRW
  - row_count: 1097
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []

### backfill:GC=F [PASS]
- latency_ms: 1018.11
- details:
  - asset_id: GC=F
  - row_count: 757
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.003963011889035667
  - latest_date: 2026-02-10
  - missing_columns: []

### backfill:SI=F [PASS]
- latency_ms: 994.48
- details:
  - asset_id: SI=F
  - row_count: 757
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.003963011889035667
  - latest_date: 2026-02-10
  - missing_columns: []

### reliability:KS200 [PASS]
- details:
  - asset_id: KS200
  - repeats: 20
  - fail_no_retry: 0
  - fail_with_retry: 0
  - fail_rate_with_retry: 0.0
  - p95_ms: 232.6407999935327

### reliability:005930 [PASS]
- details:
  - asset_id: 005930
  - repeats: 20
  - fail_no_retry: 0
  - fail_with_retry: 0
  - fail_rate_with_retry: 0.0
  - p95_ms: 794.8447999951895

### reliability:000660 [PASS]
- details:
  - asset_id: 000660
  - repeats: 20
  - fail_no_retry: 0
  - fail_with_retry: 0
  - fail_rate_with_retry: 0.0
  - p95_ms: 788.9214000024367

### reliability:SOXL [PASS]
- details:
  - asset_id: SOXL
  - repeats: 20
  - fail_no_retry: 0
  - fail_with_retry: 0
  - fail_rate_with_retry: 0.0
  - p95_ms: 990.719800000079

### reliability:BTC/KRW [PASS]
- details:
  - asset_id: BTC/KRW
  - repeats: 20
  - fail_no_retry: 0
  - fail_with_retry: 0
  - fail_rate_with_retry: 0.0
  - p95_ms: 986.1240000027465

### reliability:GC=F [PASS]
- details:
  - asset_id: GC=F
  - repeats: 20
  - fail_no_retry: 0
  - fail_with_retry: 0
  - fail_rate_with_retry: 0.0
  - p95_ms: 1000.3090999962296

### reliability:SI=F [PASS]
- details:
  - asset_id: SI=F
  - repeats: 20
  - fail_no_retry: 0
  - fail_with_retry: 0
  - fail_rate_with_retry: 0.0
  - p95_ms: 1173.0784000101266

### freshness:KS200 [PASS]
- latency_ms: 192.78
- details:
  - asset_id: KS200
  - row_count: 22
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []
  - lag_days: 0

### freshness:005930 [PASS]
- latency_ms: 694.72
- details:
  - asset_id: 005930
  - row_count: 22
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []
  - lag_days: 0

### freshness:000660 [PASS]
- latency_ms: 692.04
- details:
  - asset_id: 000660
  - row_count: 22
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []
  - lag_days: 0

### freshness:SOXL [PASS]
- latency_ms: 899.51
- details:
  - asset_id: SOXL
  - row_count: 20
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-09
  - missing_columns: []
  - lag_days: 1

### freshness:BTC/KRW [PASS]
- latency_ms: 887.43
- details:
  - asset_id: BTC/KRW
  - row_count: 32
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []
  - lag_days: 0

### freshness:GC=F [PASS]
- latency_ms: 951.01
- details:
  - asset_id: GC=F
  - row_count: 21
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []
  - lag_days: 0

### freshness:SI=F [PASS]
- latency_ms: 1026.89
- details:
  - asset_id: SI=F
  - row_count: 21
  - required_ok: True
  - dup: 0
  - neg: 0
  - inv: 0
  - missing_ratio: 0.0
  - latest_date: 2026-02-10
  - missing_columns: []
  - lag_days: 0

## 3. Gate Judgment
- **판정: Conditional Go**
- 근거: FDR 기반 전 자산(7종) smoke/backfill/reliability/freshness 검증 통과. 유일한 잔존 실패는 `postgres_connection` (DATABASE_URL 미설정).
- 조건: `DATABASE_URL` 설정 후 재검증 시 Go 전환 예상.
- Kiwoom 관련 사항은 아키텍처 결정에 의해 제거됨 (2026-02-10).

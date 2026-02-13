# Phase 4: API — Tasks
> Last Updated: 2026-02-13
> Status: ✅ Complete (15/15, 100%)

## Stage A: 기반 구조

- [x] 4.1 FastAPI 앱 골격 (main.py, CORS, error handler, DI) `[M]`
  - `api/main.py` — FastAPI app, lifespan, CORS middleware
  - `api/dependencies.py` — `get_db()` 세션 DI
  - 에러 핸들러 (HTTPException, ValidationError, 500)
  - `api/routers/health.py` — GET /v1/health (앱 동작 확인용)
  - 디렉토리 구조: routers/, services/, repositories/, schemas/
  - 7 tests (health ok/disconnected, CORS allow/deny, 404, 500, OpenAPI)

- [x] 4.2 Pydantic 스키마 정의 `[M]` — `77e4b1d`
  - `api/schemas/common.py` — PaginationParams, ErrorResponse
  - `api/schemas/asset.py` — AssetResponse
  - `api/schemas/price.py` — PriceDailyResponse
  - `api/schemas/factor.py` — FactorDailyResponse
  - `api/schemas/signal.py` — SignalDailyResponse
  - `api/schemas/backtest.py` — BacktestRunRequest, BacktestRunResponse, EquityCurveResponse, TradeLogResponse
  - `api/schemas/dashboard.py` — DashboardSummaryResponse, AssetSummary
  - `api/schemas/correlation.py` — CorrelationResponse, CorrelationPeriod

- [x] 4.3 Repository 계층 (DB 접근 추상화) `[M]` — `3e62e56`
  - `api/repositories/asset_repo.py` — get_all(db, is_active=None)
  - `api/repositories/price_repo.py` — get_prices(...), get_latest_price(...)
  - `api/repositories/factor_repo.py` — get_factors(...)
  - `api/repositories/signal_repo.py` — get_signals(...), get_latest_signal(...)
  - `api/repositories/backtest_repo.py` — get_runs, get_run_by_id, get_equity_curve, get_trades, create_run, bulk_insert_equity, bulk_insert_trades
  - 설계: 함수 기반 stateless, `db: Session` 첫 인자, SQLAlchemy 모델 반환, limit/offset pagination, date DESC 정렬
  - 38 tests (5 asset + 8 price + 6 factor + 8 signal + 11 backtest)

## Stage B: 조회 API

- [x] 4.4 `GET /v1/health` — 헬스체크 `[S]`
  - Step 4.1에서 이미 구현 완료 (DB `SELECT 1` + `{"status": "ok", "db": "connected"}`)
  - 테스트: test_main.py (health_ok, health_db_disconnected)

- [x] 4.5 `GET /v1/assets` — 자산 목록 `[S]`
  - `api/routers/assets.py` — Router: `GET /v1/assets?is_active=`
  - `asset_repo.get_all()` → `AssetResponse` 변환
  - 6 tests (all, filter active/inactive, empty, schema, Korean encoding)

- [x] 4.6 `GET /v1/prices/daily` — 가격 조회 (pagination) `[M]`
  - `api/routers/prices.py` — asset_id(필수), start_date, end_date, PaginationParams
  - date range 검증 (start > end → 400)
  - 8 tests (required param, prices, date filter, invalid range, pagination, empty, schema, limit validation)

- [x] 4.7 `GET /v1/factors` — 팩터 조회 `[M]`
  - `api/routers/factors.py` — asset_id, factor_name, start_date, end_date, PaginationParams
  - 8 tests (all, filter asset, filter factor_name, date, invalid range, pagination, empty, schema)

- [x] 4.8 `GET /v1/signals` — 시그널 조회 `[M]`
  - `api/routers/signals.py` — asset_id, strategy_id, start_date, end_date, PaginationParams
  - 8 tests (all, filter asset, filter strategy, date, invalid range, pagination, empty, schema)

## Stage C: 백테스트 API

- [x] 4.9 `GET /v1/backtests` — 백테스트 목록 `[S]` — `fac9e08`
  - `api/routers/backtests.py` — Router: `GET /v1/backtests?strategy_id=&asset_id=`
  - `backtest_repo.get_runs()` → `BacktestRunResponse` 변환, PaginationParams
  - 7 tests (all, filter strategy/asset, combined, pagination, empty, schema)

- [x] 4.10 `GET /v1/backtests/{run_id}` + `/equity` + `/trades` `[M]` — `fac9e08`
  - `GET /v1/backtests/{run_id}` — 단건 조회 (404 if not found, 422 invalid UUID)
  - `GET /v1/backtests/{run_id}/equity` — 에쿼티 커브 (date, equity, drawdown)
  - `GET /v1/backtests/{run_id}/trades` — 거래 이력 (11 fields)
  - `api/main.py` — backtests router 등록
  - 11 tests (found/not_found/invalid_uuid, equity 4, trades 4)

- [x] 4.11 `POST /v1/backtests/run` — 온디맨드 백테스트 `[L]` — `bb05a35`
  - Service 계층: `api/services/backtest_service.py` (run_backtest_on_demand)
  - 파이프라인: load_prices → preprocess → factors → signals → backtest → metrics → store
  - 단일 자산 + 다중 자산(ALL) 지원
  - 에러 처리: 잘못된 strategy/asset → 400, DB 실패 → 500
  - 라우터: POST /v1/backtests/run (201 Created)
  - 11 tests (success, all params, invalid strategy/asset, no data, store fail, schema, 422, ALL)

## Stage D: 집계 API + 테스트

- [x] 4.12 `GET /v1/dashboard/summary` — 대시보드 요약 `[M]` — `3171061`
  - `api/services/dashboard_service.py` — 자산별 최신 가격/등락률/시그널 + 최근 백테스트
  - `api/routers/dashboard.py` — GET /v1/dashboard/summary
  - 8 tests (basic, no prices, single price, signals, backtests, empty, multi, schema)

- [x] 4.13 `GET /v1/correlation` — 상관행렬 (on-the-fly) `[M]` — `7ddb5f0`
  - `api/services/correlation_service.py` — pandas pct_change → corr 계산
  - `api/routers/correlation.py` — GET /v1/correlation?asset_ids=&window=&start_date=&end_date=
  - 8 tests (basic, specific assets, insufficient, no data, window, date, invalid window, schema)

- [x] 4.14 API 단위 + 통합 테스트 보완 `[M]`
  - Part 1: `tests/unit/test_api/test_edge_cases.py` — 31 tests
    - DB error 500 (9), pagination boundary (9), date validation (3), correlation edge (6), UUID edge (4)
  - Part 2: `tests/integration/test_api_integration.py` — 11 tests
    - SQLite in-memory 전체 파이프라인 (health→assets→prices→factors→signals→dashboard→correlation)
  - ruff clean, 전체 405 passed

## Stage E: E2E 검증

- [x] 4.15 E2E 파이프라인 실행 + 시각화 (백엔드 최종 검증) `[M]`
  - Alembic migration: backtest_run에 asset_id, metrics_json 추가, backtest_trade_log에 entry_price, exit_price, shares 추가
  - `scripts/e2e_pipeline_viz.py` — 전체 파이프라인 (DB→수집→팩터→신호→백테스트→시각화)
  - 7자산 × 3전략 = 21 백테스트 실행 완료
  - 5개 시각화 차트 생성 (`docs/e2e_report/`)
  - mean_reversion 전략 close 컬럼 전달 이슈 발견 및 해결

---

## Summary
- **Stages**: 5개 (A: 기반, B: 조회, C: 백테스트, D: 집계+테스트, E: E2E 검증)
- **Progress**: 15/15 (100%) — Phase 4 완료 ✅
- **Tasks**: 15개 (S: 3, M: 10, L: 1, XL: 0)
- **Tests**: **405 passed**, 7 skipped, ruff clean

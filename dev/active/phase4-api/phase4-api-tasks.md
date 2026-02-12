# Phase 4: API — Tasks
> Last Updated: 2026-02-12
> Status: In Progress (8/14, 57%)

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

- [ ] 4.9 `GET /v1/backtests` — 백테스트 목록 `[S]`
  - backtest_run 전체 조회 (최신순, pagination)
  - 응답: `list[BacktestRunResponse]`

- [ ] 4.10 `GET /v1/backtests/{run_id}` + `/equity` + `/trades` `[M]`
  - `GET /v1/backtests/{run_id}` — 단건 조회 (metrics_json 포함)
  - `GET /v1/backtests/{run_id}/equity` — 에쿼티 커브 (date, equity, drawdown)
  - `GET /v1/backtests/{run_id}/trades` — 거래 이력 (pagination)
  - 404 처리: run_id 미존재 시

- [ ] 4.11 `POST /v1/backtests/run` — 온디맨드 백테스트 `[L]`
  - 요청 바디: BacktestRunRequest (strategy_id, asset_id, start/end_date, initial_cash, commission_pct)
  - 실행 흐름:
    1. price_daily 조회
    2. preprocessing → compute_all_factors
    3. STRATEGY_REGISTRY에서 전략 인스턴스 생성
    4. generate_signals → run_backtest
    5. compute_metrics → store_backtest_result
  - 응답: BacktestRunResponse (run_id + metrics)
  - 에러: 잘못된 strategy_id, asset_id, 데이터 부족

## Stage D: 집계 API + 테스트

- [ ] 4.12 `GET /v1/dashboard/summary` — 대시보드 요약 `[M]`
  - 7자산 각각: 최신 가격, 전일 대비 등락률, 최신 시그널
  - 최근 백테스트 실행 목록 (최대 5건)
  - 응답: DashboardSummaryResponse

- [ ] 4.13 `GET /v1/correlation` — 상관행렬 (on-the-fly) `[M]`
  - 쿼리 파라미터: asset_ids (콤마 구분, 선택), from, to, window (기본 60)
  - 로직: price_daily close 조회 → pivot → pct_change → rolling corr 또는 full corr
  - 응답: CorrelationResponse (asset_ids + N×N matrix)

- [ ] 4.14 API 단위 + 통합 테스트 `[M]`
  - `tests/unit/test_api/` — 각 라우터별 테스트
  - httpx TestClient + SQLite in-memory (또는 mock)
  - 정상 케이스 + 에러 케이스 (400, 404, 500)
  - ruff lint 통과

---

## Summary
- **Stages**: 4개 (A: 기반, B: 조회, C: 백테스트, D: 집계+테스트)
- **Progress**: 8/14 (57%) — Stage B 완료, Stage C 진행 예정
- **Tasks**: 14개 (S: 3, M: 9, L: 1, XL: 0)
- **Tests**: 기존 294 + prices 8 + factors 8 + signals 8 = **318 passed**, ruff clean

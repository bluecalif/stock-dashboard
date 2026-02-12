# Phase 4: API — Context
> Last Updated: 2026-02-12
> Status: In Progress (Step 4.5 완료)

## 1. 핵심 파일 (읽어야 할 기존 코드)

### DB 계층
| 파일 | 용도 |
|------|------|
| `backend/db/models.py` | SQLAlchemy 8 모델 (AssetMaster, PriceDaily, FactorDaily, SignalDaily, BacktestRun, BacktestEquityCurve, BacktestTradeLog, JobRun) |
| `backend/db/session.py` | `engine`, `SessionLocal` — DI `get_db` 의존성 기반 |
| `backend/config/settings.py` | `Settings` (database_url, log_level 등) |

### Research Engine (백테스트 API에서 호출)
| 파일 | 용도 |
|------|------|
| `backend/research_engine/backtest.py` | `run_backtest()`, `run_backtest_multi()`, `BacktestConfig`, `BacktestResult`, `TradeRecord` |
| `backend/research_engine/metrics.py` | `compute_metrics()`, `metrics_to_dict()`, `PerformanceMetrics` |
| `backend/research_engine/backtest_store.py` | `store_backtest_result()`, `BacktestStoreResult` |
| `backend/research_engine/preprocessing.py` | `preprocess()` — 백테스트 전 전처리 |
| `backend/research_engine/factors.py` | `compute_all_factors()`, `ALL_FACTOR_NAMES`, `FACTOR_VERSION` |
| `backend/research_engine/strategies/__init__.py` | `STRATEGY_REGISTRY` — 전략 이름 → 클래스 매핑 |
| `backend/research_engine/strategies/base.py` | `Strategy` ABC, `SignalResult` |

### 수집기 (참조)
| 파일 | 용도 |
|------|------|
| `backend/collector/fdr_client.py` | `SYMBOL_MAP` — 자산 ID 목록 참조 |

## 2. 데이터 인터페이스

### 입력 (어디서 읽는가)
| 테이블 | API 엔드포인트 | 조회 패턴 |
|--------|---------------|----------|
| `asset_master` | `/v1/assets`, `/v1/dashboard/summary` | 전체 조회 |
| `price_daily` | `/v1/prices/daily`, `/v1/correlation`, `/v1/dashboard/summary` | asset_id + date range + pagination |
| `factor_daily` | `/v1/factors` | asset_id + factor_name + date range + pagination |
| `signal_daily` | `/v1/signals`, `/v1/dashboard/summary` | asset_id + strategy_id + date range + pagination |
| `backtest_run` | `/v1/backtests`, `/v1/backtests/{run_id}`, `/v1/dashboard/summary` | 목록 / run_id 단건 |
| `backtest_equity_curve` | `/v1/backtests/{run_id}/equity` | run_id 기반 |
| `backtest_trade_log` | `/v1/backtests/{run_id}/trades` | run_id 기반 |

### 출력 (어디에 쓰는가)
| 테이블 | API 엔드포인트 | 쓰기 패턴 |
|--------|---------------|----------|
| `backtest_run` | `POST /v1/backtests/run` | INSERT (run 생성) |
| `backtest_equity_curve` | `POST /v1/backtests/run` | BULK INSERT |
| `backtest_trade_log` | `POST /v1/backtests/run` | BULK INSERT |

### on-the-fly 계산 (DB 미저장)
| API 엔드포인트 | 계산 로직 |
|---------------|----------|
| `GET /v1/correlation` | price_daily close 조회 → pandas pivot → `.pct_change().corr()` |
| `GET /v1/dashboard/summary` | asset_master + 최신 price + 최신 signal + 최근 backtest_run 집계 |

## 3. 주요 결정사항

| 항목 | 결정 | 근거 |
|------|------|------|
| 아키텍처 | Router → Service → Repository | 테스트 용이, 관심사 분리, Skill 가이드 준수 |
| DI 패턴 | FastAPI `Depends(get_db)` | Session 라이프사이클 자동 관리 |
| Pagination | `limit`/`offset` (기본 500, 최대 5000) | masterplan §8.4 명세 |
| CORS | `localhost:5173` (dev) + 프로덕션 origin | Phase 5 프론트엔드 연동 |
| 에러 응답 | `{"detail": str, "error_code": str}` | 표준 FastAPI HTTPException + 커스텀 핸들러 |
| 상관행렬 | on-the-fly pandas 계산 | 별도 DB 테이블 불필요 (7자산 소규모) |
| 백테스트 실행 | 동기 (sync) | 데이터 소규모, 수초 내 완료 예상 |
| UUID 직렬화 | Pydantic `model_config = {"from_attributes": True}` | SQLAlchemy → Pydantic 변환 |
| 날짜 형식 | `YYYY-MM-DD` (ISO 8601) | 일관성, 프론트엔드 파싱 용이 |

## 4. API 디렉토리 구조 (목표)

```
backend/api/
├── __init__.py
├── main.py                    # FastAPI app, CORS, error handler, lifespan
├── dependencies.py            # get_db, common deps
├── routers/
│   ├── __init__.py
│   ├── health.py              # GET /v1/health
│   ├── assets.py              # GET /v1/assets
│   ├── prices.py              # GET /v1/prices/daily
│   ├── factors.py             # GET /v1/factors
│   ├── signals.py             # GET /v1/signals
│   ├── backtests.py           # GET/POST /v1/backtests/*
│   ├── dashboard.py           # GET /v1/dashboard/summary
│   └── correlation.py         # GET /v1/correlation
├── services/
│   ├── __init__.py
│   ├── backtest_service.py    # 온디맨드 백테스트 실행 로직
│   ├── correlation_service.py # on-the-fly 상관행렬 계산
│   └── dashboard_service.py   # 대시보드 집계 로직
├── repositories/
│   ├── __init__.py
│   ├── asset_repo.py          # asset_master 쿼리
│   ├── price_repo.py          # price_daily 쿼리
│   ├── factor_repo.py         # factor_daily 쿼리
│   ├── signal_repo.py         # signal_daily 쿼리
│   └── backtest_repo.py       # backtest_run/equity/trades 쿼리
└── schemas/
    ├── __init__.py
    ├── common.py              # PaginationParams, ErrorResponse
    ├── asset.py               # AssetResponse
    ├── price.py               # PriceDailyResponse
    ├── factor.py              # FactorDailyResponse
    ├── signal.py              # SignalDailyResponse
    ├── backtest.py            # BacktestRunResponse, BacktestRunRequest, EquityResponse, TradeResponse
    ├── dashboard.py           # DashboardSummaryResponse
    └── correlation.py         # CorrelationResponse
```

## 5. Changed Files

### Step 4.4~4.5: Health + Assets 엔드포인트
- `api/routers/assets.py` — 신규: GET /v1/assets (is_active 필터)
- `api/main.py` — 수정: assets router 등록
- `tests/unit/test_api/test_assets.py` — 신규: 6 tests
- Step 4.4 (health)는 Step 4.1에서 이미 구현 완료

### Step 4.3: Repository 계층
- `api/repositories/__init__.py` — 수정: 5개 repo 모듈 re-export
- `api/repositories/asset_repo.py` — 신규: get_all(db, is_active)
- `api/repositories/price_repo.py` — 신규: get_prices(), get_latest_price()
- `api/repositories/factor_repo.py` — 신규: get_factors()
- `api/repositories/signal_repo.py` — 신규: get_signals(), get_latest_signal()
- `api/repositories/backtest_repo.py` — 신규: get_runs, get_run_by_id, get_equity_curve, get_trades, create_run, bulk_insert_equity, bulk_insert_trades
- `tests/unit/test_api/test_repositories/__init__.py` — 신규
- `tests/unit/test_api/test_repositories/conftest.py` — 신규: SQLite in-memory fixture + seed helpers
- `tests/unit/test_api/test_repositories/test_asset_repo.py` — 신규: 5 tests
- `tests/unit/test_api/test_repositories/test_price_repo.py` — 신규: 8 tests
- `tests/unit/test_api/test_repositories/test_factor_repo.py` — 신규: 6 tests
- `tests/unit/test_api/test_repositories/test_signal_repo.py` — 신규: 8 tests
- `tests/unit/test_api/test_repositories/test_backtest_repo.py` — 신규: 11 tests

### Step 4.1: FastAPI 앱 골격
- `api/main.py` — 신규: FastAPI app, lifespan, CORS, error handlers (422/500)
- `api/dependencies.py` — 신규: `get_db()` 세션 DI
- `api/routers/__init__.py` — 신규 (빈 파일)
- `api/routers/health.py` — 신규: GET /v1/health (DB 연결 확인)
- `api/services/__init__.py` — 신규 (빈 파일)
- `api/repositories/__init__.py` — 신규 (빈 파일)
- `api/schemas/__init__.py` — 신규 (빈 파일)
- `tests/unit/test_api/__init__.py` — 신규 (빈 파일)
- `tests/unit/test_api/test_main.py` — 신규: 7 tests (health, CORS, errors, OpenAPI)

### Step 4.2: Pydantic 스키마 정의
- `api/schemas/common.py` — 신규: PaginationParams, ErrorResponse
- `api/schemas/asset.py` — 신규: AssetResponse (from_attributes)
- `api/schemas/price.py` — 신규: PriceDailyResponse (OHLCV + source)
- `api/schemas/factor.py` — 신규: FactorDailyResponse
- `api/schemas/signal.py` — 신규: SignalDailyResponse (optional fields)
- `api/schemas/backtest.py` — 신규: BacktestRunRequest/Response, EquityCurveResponse, TradeLogResponse
- `api/schemas/dashboard.py` — 신규: AssetSummary, DashboardSummaryResponse
- `api/schemas/correlation.py` — 신규: CorrelationResponse, CorrelationPeriod
- `api/schemas/__init__.py` — 수정: 14개 클래스 re-export
- `tests/unit/test_api/test_schemas.py` — 신규: 20 tests

## 6. 컨벤션 체크리스트

### API 관련 (Phase 4 적용)
- [ ] Router → Service → Repository 레이어 분리
- [x] Pydantic v2 스키마 (from_attributes=True) — 8개 모듈, 14개 클래스
- [x] FastAPI DI (Depends) — `get_db()` in `dependencies.py`
- [x] CORS 설정 (allow_origins, allow_methods, allow_headers) — `main.py`
- [ ] Pagination (limit/offset, 기본 500, 최대 5000)
- [x] 에러 응답 표준화 (4xx/5xx + JSON) — ValidationError(422), generic(500)
- [x] UUID 문자열 직렬화 — BacktestRunResponse, EquityCurveResponse, TradeLogResponse
- [ ] 날짜 파라미터: Query(alias="from"), Query(alias="to")
- [x] 라우터 prefix: `/v1/...` — health.py에 적용
- [x] Pydantic v2 스키마 (from_attributes=True)
- [ ] 응답 모델 명시: `response_model=...`

### 인코딩 관련
- [x] JSON 응답: FastAPI 기본 UTF-8 (자동)
- [x] 한글 자산명: Pydantic 모델에서 안전 직렬화
- [x] UUID 문자열 직렬화 — BacktestRunResponse, EquityCurveResponse, TradeLogResponse

### 테스트 관련
- [x] httpx AsyncClient + TestClient — `test_main.py` (TestClient 사용)
- [x] SQLite in-memory 또는 mock session — MagicMock(spec=Session)
- [ ] 각 엔드포인트 정상/에러 케이스

## 6. Pydantic 스키마 설계 (주요)

### 공통
```python
class PaginationParams:
    limit: int = Query(default=500, ge=1, le=5000)
    offset: int = Query(default=0, ge=0)

class ErrorResponse(BaseModel):
    detail: str
    error_code: str
```

### 자산
```python
class AssetResponse(BaseModel):
    asset_id: str
    name: str
    category: str
    is_active: bool
    model_config = ConfigDict(from_attributes=True)
```

### 가격
```python
class PriceDailyResponse(BaseModel):
    asset_id: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str
```

### 백테스트
```python
class BacktestRunRequest(BaseModel):
    strategy_id: str          # "momentum", "trend", "mean_reversion"
    asset_id: str             # 단일 자산 ID 또는 "ALL"
    start_date: date | None = None
    end_date: date | None = None
    initial_cash: float = 10_000_000
    commission_pct: float = 0.001

class BacktestRunResponse(BaseModel):
    run_id: UUID
    strategy_id: str
    asset_id: str
    status: str
    config_json: dict
    metrics_json: dict | None
    started_at: datetime
    ended_at: datetime | None
```

### 상관행렬
```python
class CorrelationResponse(BaseModel):
    asset_ids: list[str]
    matrix: list[list[float]]    # N×N 행렬
    period: dict                 # {"from": date, "to": date, "window": int}
```

### 대시보드
```python
class AssetSummary(BaseModel):
    asset_id: str
    name: str
    latest_price: float | None
    price_change_pct: float | None
    latest_signal: dict | None    # {strategy_id: action}

class DashboardSummaryResponse(BaseModel):
    assets: list[AssetSummary]
    recent_backtests: list[BacktestRunResponse]
    updated_at: datetime
```

# Phase 4: API
> Last Updated: 2026-02-13
> Status: ✅ Complete (15/15, 100%)

## 1. Summary (개요)

**목적**: Phase 1~3에서 구축한 DB(8 테이블) + 수집기(collector) + 분석 엔진(research_engine)을 FastAPI REST API로 노출하여, Phase 5 프론트엔드가 소비할 수 있도록 한다.

**범위**: 12개 엔드포인트 (조회 5 + 백테스트 5 + 집계 2)

**예상 결과물**:
- FastAPI 앱 (`api/main.py`) + CORS + 에러 핸들러 + 헬스체크
- Router-Service-Repository 3계층 아키텍처
- Pydantic 스키마 (요청/응답)
- Pagination 지원 (limit/offset, 기본 500)
- 온디맨드 백테스트 실행 (research_engine 연동)
- on-the-fly 상관행렬 계산
- 단위 + 통합 테스트 (httpx TestClient)

## 2. Current State (현재 상태)

- **Phase 3 완료**: 전처리, 팩터 15개, 전략 3종, 백테스트, 성과지표, 배치 스크립트
- **DB**: 8 테이블 생성 완료, price_daily 5,559 rows, 7자산
- **Step 4.1 완료**: FastAPI 앱 골격 (main.py, CORS, error handlers, DI, health 라우터)
- **Step 4.2 완료**: Pydantic 스키마 8개 모듈 (14개 클래스, 20 tests)
- **Step 4.3 완료**: Repository 계층 5개 모듈 (13개 함수, 38 tests)
- **api/**: main.py, dependencies.py, routers/health.py, schemas/ (8 모듈), repositories/ (5 모듈)
- **테스트**: 288 unit (250 + repo 38) + 7 integration, ruff clean
- **Step 4.4~4.5 완료**: Health (기존) + Assets 엔드포인트 (6 tests)
- **Step 4.6~4.8 완료**: Prices, Factors, Signals 라우터 (24 tests)
- **Stage B 완료**
- **Step 4.9~4.10 완료**: Backtests 목록/단건/equity/trades 라우터 (18 tests)
- **Step 4.11 완료**: POST /v1/backtests/run 온디맨드 백테스트 (Service 계층 도입, 11 tests)
- **Stage C 완료**
- **Step 4.12 완료**: GET /v1/dashboard/summary (dashboard_service, 8 tests)
- **Step 4.13 완료**: GET /v1/correlation (correlation_service, pandas corr, 8 tests)
- **Step 4.14 완료**: 엣지 케이스 31 tests + 통합 테스트 11 tests — 전체 405 passed
- **Stage D 완료**
- **Step 4.15 완료**: E2E 파이프라인 최종 검증 (Alembic migration + 7×3 backtest + 5 viz charts)
- **Stage E 완료** — **Phase 4 완료 ✅** (다음: Phase 5 Frontend)

## 3. Target State (목표 상태)

| 영역 | 목표 |
|------|------|
| 엔드포인트 | 12개 운영 (조회 5 + 백테스트 5 + 집계 2) |
| 아키텍처 | Router → Service → Repository 3계층 |
| 스키마 | Pydantic v2 모델 (요청/응답 분리) |
| 인증 | 없음 (MVP) |
| CORS | 프론트엔드 origin 허용 (localhost:5173 + 프로덕션) |
| Pagination | limit/offset (기본 500, 최대 5000) |
| 에러 처리 | 표준 4xx/5xx + JSON 에러 바디 |
| 테스트 | httpx TestClient 단위/통합 테스트 |

## 4. Implementation Stages

### Stage A: 기반 구조 (Step 4.1 ~ 4.3)
FastAPI 앱 초기화, Pydantic 스키마, Repository 계층을 구축한다.
- `api/main.py` — 앱 엔트리, CORS, 에러 핸들러, DI (get_db)
- `api/schemas/` — Pydantic 모델 (assets, prices, factors, signals, backtests, common)
- `api/repositories/` — DB 접근 추상화 (SQLAlchemy 쿼리)

### Stage B: 조회 API (Step 4.4 ~ 4.8)
읽기 전용 5개 엔드포인트를 구현한다.
- `GET /v1/health` — DB 연결 상태 확인
- `GET /v1/assets` — asset_master 전체 목록
- `GET /v1/prices/daily` — 가격 조회 (asset_id, from, to, pagination)
- `GET /v1/factors` — 팩터 조회 (asset_id, factor_name, from, to, pagination)
- `GET /v1/signals` — 시그널 조회 (asset_id, strategy_id, from, to, pagination)

### Stage C: 백테스트 API (Step 4.9 ~ 4.11)
백테스트 조회 + 온디맨드 실행을 구현한다.
- `GET /v1/backtests` — 실행 목록
- `GET /v1/backtests/{run_id}` — 요약 (metrics 포함)
- `GET /v1/backtests/{run_id}/equity` — 에쿼티 커브
- `GET /v1/backtests/{run_id}/trades` — 거래 이력
- `POST /v1/backtests/run` — 온디맨드 백테스트 실행 (research_engine 호출)

### Stage D: 집계 API + 테스트 (Step 4.12 ~ 4.14)
대시보드용 집계 엔드포인트와 전체 테스트를 구현한다.
- `GET /v1/dashboard/summary` — 7자산 최신가격 + 최신시그널 + 최근 백테스트 성과
- `GET /v1/correlation` — 자산 간 상관행렬 (on-the-fly, pandas corrcoef)
- API 단위 + 통합 테스트

## 5. Task Breakdown

| # | Task | Size | Stage | 의존성 |
|---|------|------|-------|--------|
| 4.1 | FastAPI 앱 골격 (main.py, CORS, error handler, DI) | M | A | - |
| 4.2 | Pydantic 스키마 정의 | M | A | - |
| 4.3 | Repository 계층 (DB 접근 추상화) | M | A | 4.1 |
| 4.4 | `GET /v1/health` — 헬스체크 | S | B | 4.1 |
| 4.5 | `GET /v1/assets` — 자산 목록 | S | B | 4.2, 4.3 |
| 4.6 | `GET /v1/prices/daily` — 가격 조회 (pagination) | M | B | 4.2, 4.3 |
| 4.7 | `GET /v1/factors` — 팩터 조회 | M | B | 4.2, 4.3 |
| 4.8 | `GET /v1/signals` — 시그널 조회 | M | B | 4.2, 4.3 |
| 4.9 | `GET /v1/backtests` — 백테스트 목록 | S | C | 4.2, 4.3 |
| 4.10 | `GET /v1/backtests/{run_id}` + `/equity` + `/trades` | M | C | 4.2, 4.3 |
| 4.11 | `POST /v1/backtests/run` — 온디맨드 백테스트 | L | C | 4.2, 4.3 |
| 4.12 | `GET /v1/dashboard/summary` — 대시보드 요약 | M | D | 4.5, 4.6, 4.8 |
| 4.13 | `GET /v1/correlation` — 상관행렬 (on-the-fly) | M | D | 4.6 |
| 4.14 | API 단위 + 통합 테스트 | M | D | 4.4~4.13 |
| 4.15 | E2E 파이프라인 실행 + 시각화 (최종 검증) | M | E | ALL |

**Size 분포**: S: 3, M: 10, L: 1, XL: 0 — 총 15 tasks

## 6. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| POST /v1/backtests/run 동기 실행 지연 | API 타임아웃 | 중 | 데이터 소규모(7자산×3년)로 수초 내 완료 예상. 필요 시 background task 전환 |
| on-the-fly 상관행렬 성능 | 응답 지연 | 저 | 7자산 규모 소형, pandas 충분 |
| research_engine 직접 의존 | API-분석 결합도 | 중 | Service 계층에서 래핑하여 인터페이스 분리 |
| DB 커넥션 풀 고갈 | 동시 요청 실패 | 저 | SQLAlchemy pool_pre_ping + pool_size 설정 |

## 7. Dependencies

### 내부 (이전 Phase 모듈)
- `db/models.py` — SQLAlchemy 8 모델 (읽기)
- `db/session.py` — SessionLocal, engine (DI용)
- `research_engine/backtest.py` — run_backtest, run_backtest_multi (POST /backtests/run)
- `research_engine/metrics.py` — compute_metrics, metrics_to_dict
- `research_engine/backtest_store.py` — store_backtest_result
- `research_engine/preprocessing.py` — preprocess (백테스트 전처리)
- `research_engine/factors.py` — compute_all_factors (백테스트 팩터 계산)
- `research_engine/strategies/` — STRATEGY_REGISTRY (전략 조회)
- `config/settings.py` — Settings (환경 설정)

### 외부 (라이브러리)
- `fastapi>=0.100` — 이미 pyproject.toml 선언 ✅
- `uvicorn[standard]` — ASGI 서버 ✅
- `pydantic>=2.0` — 스키마 ✅
- `httpx` — 테스트 클라이언트 (dev 의존성) ✅
- `pandas` — 상관행렬 계산 ✅

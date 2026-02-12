# Session Compact

> Generated: 2026-02-12
> Source: Conversation compaction via /compact-and-go

## Goal
Phase 4 API 구현 진행 중 — Step 4.3 완료, Step 4.4로 이동

## Completed
- [x] **Phase 4 dev-docs 생성** (`dev/active/phase4-api/`)
- [x] **project-overall 동기화** (3개 파일)
- [x] **정합성 검증 ALL PASS** (4/4)
- [x] **Step 4.1 FastAPI 앱 골격** — main.py, CORS, error handlers, DI, health 라우터, 7 tests
- [x] **Step 4.2 Pydantic 스키마 정의** — 8개 모듈, 14개 클래스, 20 tests
- [x] **Step 4.3 Repository 계층** — 5개 repo 모듈, 13개 함수, 38 tests
  - asset_repo.py: `get_all(db, is_active=None)`
  - price_repo.py: `get_prices(...)`, `get_latest_price(...)`
  - factor_repo.py: `get_factors(...)`
  - signal_repo.py: `get_signals(...)`, `get_latest_signal(...)`
  - backtest_repo.py: `get_runs`, `get_run_by_id`, `get_equity_curve`, `get_trades`, `create_run`, `bulk_insert_equity`, `bulk_insert_trades`
  - 설계: 함수 기반 stateless, `db: Session` 첫 인자, SQLAlchemy 모델 반환, limit/offset pagination, date DESC 정렬

## Current State

### 프로젝트 진행률
| Phase | 이름 | 상태 | Tasks |
|-------|------|------|-------|
| 1 | Skeleton | ✅ 완료 | 9/9 |
| 2 | Collector | ✅ 완료 | 10/10 |
| 3 | Research Engine | ✅ 완료 | 12/12 |
| 4 | API | 진행 중 | 3/14 (커밋 완료) |
| 5 | Frontend | 미착수 | 0/10 |
| 6 | Deploy & Ops | 미착수 | 0/16 |

### Git / Tests
- Branch: `master`
- Unit: **~288 passed** (기존 250 + 38 새 repo 테스트), ruff clean
- DB: price_daily 5,559 rows, 7개 자산

### Changed Files (uncommitted)
- `backend/api/repositories/__init__.py` — 5개 repo 모듈 re-export
- `backend/api/repositories/asset_repo.py` — 신규
- `backend/api/repositories/price_repo.py` — 신규
- `backend/api/repositories/factor_repo.py` — 신규
- `backend/api/repositories/signal_repo.py` — 신규
- `backend/api/repositories/backtest_repo.py` — 신규
- `backend/tests/unit/test_api/test_repositories/__init__.py` — 신규
- `backend/tests/unit/test_api/test_repositories/conftest.py` — SQLite in-memory fixture + seed helpers
- `backend/tests/unit/test_api/test_repositories/test_asset_repo.py` — 5 tests
- `backend/tests/unit/test_api/test_repositories/test_price_repo.py` — 8 tests
- `backend/tests/unit/test_api/test_repositories/test_factor_repo.py` — 6 tests
- `backend/tests/unit/test_api/test_repositories/test_signal_repo.py` — 8 tests
- `backend/tests/unit/test_api/test_repositories/test_backtest_repo.py` — 11 tests

## Remaining / TODO

### Phase 4: API (11 tasks 남음)
**Stage A: 기반 구조** ✅ 완료 (커밋됨)
- [x] 4.1 FastAPI 앱 골격 (main.py, CORS, error handler, DI) `[M]`
- [x] 4.2 Pydantic 스키마 정의 `[M]`
- [x] 4.3 Repository 계층 (DB 접근 추상화) `[M]`

**Stage B: 조회 API**
- [ ] 4.4 `GET /v1/health` — 헬스체크 `[S]`
- [ ] 4.5 `GET /v1/assets` — 자산 목록 `[S]`
- [ ] 4.6 `GET /v1/prices/daily` — 가격 조회 (pagination) `[M]`
- [ ] 4.7 `GET /v1/factors` — 팩터 조회 `[M]`
- [ ] 4.8 `GET /v1/signals` — 시그널 조회 `[M]`

**Stage C: 백테스트 API**
- [ ] 4.9 `GET /v1/backtests` — 백테스트 목록 `[S]`
- [ ] 4.10 `GET /v1/backtests/{run_id}` + `/equity` + `/trades` `[M]`
- [ ] 4.11 `POST /v1/backtests/run` — 온디맨드 백테스트 `[L]`

**Stage D: 집계 + 테스트**
- [ ] 4.12 `GET /v1/dashboard/summary` — 대시보드 요약 `[M]`
- [ ] 4.13 `GET /v1/correlation` — 상관행렬 (on-the-fly) `[M]`
- [ ] 4.14 API 단위 + 통합 테스트 `[M]`

### Phase 5~6
- Phase 5: Frontend (10 tasks) — Phase 4 완료 후
- Phase 6: Deploy & Ops (16 tasks) — Phase 5 완료 후

## Key Decisions
- Phase 4 아키텍처: Router → Service → Repository 3계층
- DI 패턴: FastAPI `Depends(get_db)` 세션 관리
- Repository: 함수 기반 stateless, 클래스 불필요
- Pagination: limit/offset (기본 500, 최대 5000)
- 상관행렬: on-the-fly pandas 계산 (별도 DB 불필요)
- 백테스트 실행: 동기 (sync) — 데이터 소규모, 수초 내 완료 예상
- CORS: localhost:5173 (dev) + 프로덕션 origin
- 테스트 DB: SQLite in-memory (PostgreSQL UUID → SQLite TEXT 자동 호환)

## Context
다음 세션에서는 답변에 한국어를 사용하세요.
- **작업 디렉토리**: `backend/` 내에서 Python 작업 수행
- **venv**: `backend/.venv/Scripts/activate` (Windows), Python 3.12.3
- **Bash 경로**: `/c/Projects-2026/stock-dashboard/backend` (Windows 백슬래시 불가)
- **dev-docs**: `dev/active/phase4-api/`, `dev/active/project-overall/`
- **테스트**: `backend/tests/unit/` (~288개) + `backend/tests/integration/` (7개)
- **마스터플랜**: `docs/masterplan-v0.md` — §8(API 12개), §8.5(프론트엔드 6페이지)
- **커맨드**: `/dev-docs`와 `/step-update` 모두 project-overall 동기화 포함
- Git remote: `https://github.com/bluecalif/stock-dashboard.git`
- **미커밋**: Step 4.3 작업물 커밋 필요 → `/step-update` 실행 권장
- **Phase 4 핵심 참조**: `dev/active/phase4-api/phase4-api-context.md`
- **스키마**: `api/schemas/` 8개 모듈 완성, **Repository**: `api/repositories/` 5개 모듈 완성
- **Stage B 시작 준비 완료**: Router + Service 계층 → Repository 호출하여 엔드포인트 구현

## Next Action
1. **Step 4.4~4.5**: 조회 API 시작 — health + assets 엔드포인트 (둘 다 `[S]` 사이즈, 빠르게 완료 가능)
   - Router: `api/routers/assets.py` → Service → `asset_repo.get_all()`
   - Pydantic 스키마 변환 (AssetResponse)
   - 테스트: TestClient 기반 integration-style

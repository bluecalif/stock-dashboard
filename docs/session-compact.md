# Session Compact

> Generated: 2026-02-12
> Source: Conversation compaction via /compact-and-go

## Goal
Phase 4 API 구현 진행 중 — Step 4.8 완료 (Stage B 완료), Stage C로 이동

## Completed
- [x] **Phase 4 dev-docs 생성** (`dev/active/phase4-api/`)
- [x] **project-overall 동기화** (3개 파일)
- [x] **정합성 검증 ALL PASS** (4/4)
- [x] **Step 4.1 FastAPI 앱 골격** — main.py, CORS, error handlers, DI, health 라우터, 7 tests
- [x] **Step 4.2 Pydantic 스키마 정의** — 8개 모듈, 14개 클래스, 20 tests
- [x] **Step 4.3 Repository 계층** — 5개 repo 모듈, 13개 함수, 38 tests
- [x] **Step 4.4~4.5 Health + Assets** — health (기존), assets 라우터 6 tests
- [x] **Step 4.6~4.8 Prices, Factors, Signals** — 3개 라우터, 24 tests
  - prices.py: asset_id(필수), start_date, end_date, PaginationParams, date range 검증
  - factors.py: asset_id, factor_name, start_date, end_date, PaginationParams
  - signals.py: asset_id, strategy_id, start_date, end_date, PaginationParams

## Current State

### 프로젝트 진행률
| Phase | 이름 | 상태 | Tasks |
|-------|------|------|-------|
| 1 | Skeleton | ✅ 완료 | 9/9 |
| 2 | Collector | ✅ 완료 | 10/10 |
| 3 | Research Engine | ✅ 완료 | 12/12 |
| 4 | API | 진행 중 | 8/14 |
| 5 | Frontend | 미착수 | 0/10 |
| 6 | Deploy & Ops | 미착수 | 0/16 |

### Git / Tests
- Branch: `master`
- Unit: **318 passed**, ruff clean
- DB: price_daily 5,559 rows, 7개 자산

## Remaining / TODO

### Phase 4: API (6 tasks 남음)
**Stage A: 기반 구조** ✅ 완료
- [x] 4.1~4.3: 앱 골격, 스키마, Repository

**Stage B: 조회 API** ✅ 완료
- [x] 4.4~4.8: health, assets, prices, factors, signals

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
- Phase 4 아키텍처: Router → Repository (Service 계층은 Stage C/D에서 추가)
- DI 패턴: FastAPI `Depends(get_db)` 세션 관리
- Repository: 함수 기반 stateless, 클래스 불필요
- Pagination: limit/offset (기본 500, 최대 5000) — PaginationParams Depends
- 날짜 범위 검증: start_date > end_date → 400 에러
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
- **테스트**: `backend/tests/unit/` (318개) + `backend/tests/integration/` (7개)
- **마스터플랜**: `docs/masterplan-v0.md` — §8(API 12개), §8.5(프론트엔드 6페이지)
- **커맨드**: `/dev-docs`와 `/step-update` 모두 project-overall 동기화 포함
- Git remote: `https://github.com/bluecalif/stock-dashboard.git`
- **Phase 4 핵심 참조**: `dev/active/phase4-api/phase4-api-context.md`
- **라우터**: health, assets, prices, factors, signals 완성
- **다음**: Stage C 백테스트 API (Step 4.9~4.11)

## Next Action
1. **Step 4.9**: `GET /v1/backtests` — 백테스트 목록 조회
2. **Step 4.10**: `GET /v1/backtests/{run_id}` + `/equity` + `/trades`
3. **Step 4.11**: `POST /v1/backtests/run` — 온디맨드 백테스트 실행

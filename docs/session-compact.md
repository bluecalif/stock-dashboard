# Session Compact

> Generated: 2026-02-12
> Source: Conversation compaction via /compact-and-go

## Goal
Phase 4 API 구현 진행 중 — Step 4.1 완료

## Completed
- [x] **Phase 4 dev-docs 생성** (`dev/active/phase4-api/`)
- [x] **project-overall 동기화** (3개 파일)
- [x] **정합성 검증 ALL PASS** (4/4)
- [x] **Step 4.1 FastAPI 앱 골격** — main.py, CORS, error handlers, DI, health 라우터, 7 tests

## Current State

### 프로젝트 진행률
| Phase | 이름 | 상태 | Tasks |
|-------|------|------|-------|
| 1 | Skeleton | ✅ 완료 | 9/9 |
| 2 | Collector | ✅ 완료 | 10/10 |
| 3 | Research Engine | ✅ 완료 | 12/12 |
| 4 | API | 진행 중 | 1/14 |
| 5 | Frontend | 미착수 | 0/10 |
| 6 | Deploy & Ops | 미착수 | 0/16 |

### Git / Tests
- Branch: `master`, remote 동기화 완료
- Unit: **230 passed**, ruff clean
- DB: price_daily 5,559 rows, 7개 자산

## Remaining / TODO

### Phase 4: API (13 tasks 남음)
**Stage A: 기반 구조**
- [x] 4.1 FastAPI 앱 골격 (main.py, CORS, error handler, DI) `[M]`
- [ ] 4.2 Pydantic 스키마 정의 `[M]`
- [ ] 4.3 Repository 계층 (DB 접근 추상화) `[M]`

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
- Pagination: limit/offset (기본 500, 최대 5000)
- 상관행렬: on-the-fly pandas 계산 (별도 DB 불필요)
- 백테스트 실행: 동기 (sync) — 데이터 소규모, 수초 내 완료 예상
- CORS: localhost:5173 (dev) + 프로덕션 origin

## Context
다음 세션에서는 답변에 한국어를 사용하세요.
- **작업 디렉토리**: `backend/` 내에서 Python 작업 수행
- **venv**: `backend/.venv/Scripts/activate` (Windows), Python 3.12.3
- **Bash 경로**: `/c/Projects-2026/stock-dashboard/backend` (Windows 백슬래시 불가)
- **dev-docs**: `dev/active/phase4-api/`, `dev/active/project-overall/`
- **테스트**: `backend/tests/unit/` (230개) + `backend/tests/integration/` (7개)
- **마스터플랜**: `docs/masterplan-v0.md` — §8(API 12개), §8.5(프론트엔드 6페이지)
- **커맨드**: `/dev-docs`와 `/step-update` 모두 project-overall 동기화 포함
- Git remote: `https://github.com/bluecalif/stock-dashboard.git`
- **데이터 흐름**: `collector(FDR) → price_daily → research_engine → factor/signal/backtest DB → API(Phase4) → Frontend(Phase5)`
- **Phase 4 핵심 참조**: `dev/active/phase4-api/phase4-api-context.md` (디렉토리 구조, 스키마 설계, 데이터 인터페이스)

## Next Action
1. **Step 4.2**: Pydantic 스키마 정의 (8개 스키마 모듈)
2. **Step 4.3**: Repository 계층 (DB 접근 추상화)

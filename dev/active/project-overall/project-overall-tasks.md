# Project Overall Tasks
> Last Updated: 2026-03-11
> Status: MVP 완료 (83/83), Post-MVP Phase A 착수 예정

## Phase 0: 사전 준비 ✅ 완료
- [x] 마스터플랜 작성 (docs/masterplan-v0.md)
- [x] 데이터 접근성 검증 (Conditional Go)
- [x] CLAUDE.md + Skills + Hooks 설정
- [x] Git 초기화 + remote 설정 + push
- [x] Kiwoom 폐기, FDR 단일 소스 결정

## Phase 1: 프로젝트 골격 + DB ✅ 완료 (9/9)
- [x] 1.1 `pyproject.toml` + 의존성 설치 `[S]`
- [x] 1.2 `.env.example` + `DATABASE_URL` 설정 `[S]`
- [x] 1.3 `db/models.py` — SQLAlchemy 모델 8개 테이블 `[M]`
- [x] 1.4 Alembic 초기화 + 초기 마이그레이션 `[M]`
- [x] 1.5 `asset_master` 시드 스크립트 `[S]`
- [x] 1.6 `config/settings.py` — Pydantic BaseSettings `[S]`
- [x] 1.7 `config/logging.py` — JSON 로깅 설정 `[S]`
- [x] 1.8 `db/session.py` — SessionLocal 엔진 `[S]`
- [x] 1.9 기본 단위 테스트 `[M]`

## Phase 2: 수집기 (Collector) ✅ 완료 (10/10)
- [x] 2.1 `collector/fdr_client.py` — FDR 래퍼 + 심볼 매핑 `[M]`
- [x] 2.2 `collector/validators.py` — OHLCV 정합성 검증 `[M]`
- [x] 2.3 `collector/ingest.py` — 수집 오케스트레이션 `[L]`
- [x] 2.4 지수 백오프 재시도 로직 `[M]`
- [x] 2.5 idempotent UPSERT 구현 `[M]`
- [x] 2.6 부분 실패 허용 + `job_run` 기록 `[M]`
- [x] 2.7 정합성 검증 강화 `[S]`
- [x] 2.8 `collector/alerting.py` — Discord 알림 `[S]`
- [x] 2.9 `scripts/collect.py` — 수집 배치 CLI `[M]`
- [x] 2.10 3년 백필 실행 + 검증 (5,559 rows) `[L]`

## Phase 3: 분석 엔진 (Research Engine) ✅ 완료 (12/12)
- [x] 3.1 전처리 파이프라인 `[M]` — `d476c52`
- [x] 3.2 수익률 + 추세 팩터 `[M]` — `b1ce303`
- [x] 3.3 모멘텀 + 변동성 + 거래량 팩터 `[M]` — `b1ce303`
- [x] 3.4 팩터 DB 저장 `[M]` — `1e35fd9`
- [x] 3.5 전략 프레임워크 `[M]` — `6956015`
- [x] 3.6 3종 전략 구현 `[M]` — `6956015`
- [x] 3.7 시그널 생성 + DB 저장 `[S]` — `6956015`
- [x] 3.8 백테스트 엔진 `[L]` — `da01cef`
- [x] 3.9 성과 평가 지표 `[M]` — `c433392`
- [x] 3.10 백테스트 결과 DB 저장 `[S]` — `4f9cdc9`
- [x] 3.11 배치 스크립트 + 통합 테스트 `[M]` — `fc8fc4f`
- [x] 3.12 dev-docs 갱신 `[S]`

## Phase 4: API ✅ 완료 (15/15)
> dev-docs: `dev/active/phase4-api/`

### 4A. 기반 구조 ✅
- [x] 4.1 FastAPI 앱 골격 (main.py, CORS, error handler, DI) `[M]`
- [x] 4.2 Pydantic 스키마 정의 `[M]` — `77e4b1d`
- [x] 4.3 Repository 계층 (DB 접근 추상화) `[M]` — `b990914`

### 4B. 조회 API ✅
- [x] 4.4 `GET /v1/health` `[S]`
- [x] 4.5 `GET /v1/assets` `[S]`
- [x] 4.6 `GET /v1/prices/daily` `[M]`
- [x] 4.7 `GET /v1/factors` `[M]`
- [x] 4.8 `GET /v1/signals` `[M]`

### 4C. 백테스트 API ✅
- [x] 4.9 `GET /v1/backtests` `[S]` — `fac9e08`
- [x] 4.10 `GET /v1/backtests/{run_id}` + `/equity` + `/trades` `[M]` — `fac9e08`
- [x] 4.11 `POST /v1/backtests/run` `[L]` — `bb05a35`

### 4D. 집계 API + 테스트 ✅
- [x] 4.12 `GET /v1/dashboard/summary` `[M]` — `3171061`
- [x] 4.13 `GET /v1/correlation` `[M]` — `7ddb5f0`
- [x] 4.14 API 단위 + 통합 테스트 `[M]` — `1d10c2e`

### 4E. E2E 검증 ✅
- [x] 4.15 E2E 파이프라인 실행 `[M]`

## Phase 5: 프론트엔드 (Frontend) ✅ 완료 (13/13)
> dev-docs: `dev/active/phase5-frontend/`

### 5A. 기반 구조 ✅
- [x] 5.1 Vite + React + TypeScript 초기화 `[M]` — `f227b2b`
- [x] 5.2 API 클라이언트 + 타입 정의 `[M]` — `f227b2b`
- [x] 5.3 레이아웃 (사이드바 + 메인 콘텐츠) `[M]` — `f227b2b`

### 5B. 핵심 차트 ✅
- [x] 5.4 가격 차트 `[L]` — `91effb9`
- [x] 5.5 수익률 비교 차트 `[M]` — `91effb9`

### 5C. 분석 시각화 ✅
- [x] 5.6 상관 히트맵 `[M]` — `048d34d`
- [x] 5.7 팩터 현황 `[M]` — `3b8ceed`
- [x] 5.8 시그널 타임라인 `[M]` — `d0bf7a4`

### 5D. 전략 성과 + 홈 ✅
- [x] 5.9 전략 성과 비교 `[L]` — `aafa80d`
- [x] 5.10 대시보드 홈 `[M]` — `3b583a9`

### 5E. UX 디버깅 ✅
- [x] 5.11 UX 버그: 전략 ID + X축 정렬 `[M]` — `398f7da`
- [x] 5.12 UX 버그: Gold/Silver 에러 + 거래량 `[M]` — `398f7da`
- [x] 5.13 UX 버그: 팩터/전략 데이터 `[S]` — `398f7da`, `d227ee9`

## Phase 6: 배포 & 운영 ✅ 완료 (9/9)
> dev-docs: `dev/active/phase6-deploy/`

### 6A. 배치 통합
- [x] 6.1 리서치 파이프라인 배치 스케줄링 `[S]` — `c80fd08`
- [x] 6.4 로그 로테이션 `[S]` — `c80fd08`

### 6B. 테스트 검증
- [x] 6.2 테스트 전체 실행 & 검증 `[M]` — `66cbef1`

### 6C. 운영 도구
- [x] 6.3 Pre-deployment 체크 스크립트 `[M]` — `93407b4`

### 6D. CI/CD
- [x] 6.7 GitHub Actions CI 파이프라인 `[M]` — `4b263b9`

### 6E. 프로덕션 배포
- [x] 6.8 백엔드 Railway 배포 `[M]` — `e80d50b`
- [x] 6.9 프론트엔드 Vercel 배포 `[M]` — `f745079`

### 6F. 문서화
- [x] 6.5 운영 문서 (Runbook) `[M]` — `65e6703`
- [x] 6.6 dev-docs 갱신 `[S]`

## Phase 7: 스케줄 자동 수집 ✅ 완료 (6/6)
> dev-docs: `dev/active/phase7-scheduler/`

### 7A. 사전 준비
- [x] 7.1 Railway Public Networking 확인 `[S]`
- [x] 7.2 GitHub Secrets 등록 `[S]`

### 7B. Workflow 구현
- [x] 7.3 `daily-collect.yml` 작성 `[M]` — `b798b65`

### 7C. 검증 + 문서
- [x] 7.4 workflow_dispatch E2E 검증 `[M]`
- [x] 7.5 Runbook 업데이트 `[S]`
- [x] 7.6 dev-docs 갱신 `[S]`

---

## Post-MVP Phases (Phase A~F) — 계획

> 구현 순서: A → B → C → D → E → F
> Phase A, B: 상세 확정. Phase C~F: 진입 시 `/dev-docs`로 상세 기획.

## Phase A: Auth + 사용자 컨텍스트 — ⬜ 미시작 (0/16)
> dev-docs: `dev/active/phaseA-auth/`

### Stage A: Backend 기반
- [ ] A.1 DB 모델: User, UserSession + Alembic migration `[M]`
- [ ] A.2 Settings: jwt_secret_key, jwt_algorithm, access/refresh TTL `[S]`
- [ ] A.3 Pydantic 스키마: auth.py `[S]`
- [ ] A.4 Repository: user_repo.py, session_repo.py `[M]`

### Stage B: Backend Auth 로직
- [ ] A.5 Service: auth_service.py `[L]`
- [ ] A.6 Router: auth.py `[M]`
- [ ] A.7 Dependencies: get_current_user, get_current_user_optional `[M]`

### Stage C: Backend 통합 + 테스트
- [ ] A.8 main.py 라우터 등록 + pyproject.toml 의존성 `[S]`
- [ ] A.9 단위 테스트: auth service + auth router `[M]`
- [ ] A.10 Regression: 기존 tests 통과 확인 `[S]`

### Stage D: Frontend Auth
- [ ] A.11 Zustand authStore + auth API + types `[M]`
- [ ] A.12 LoginPage + SignupPage `[M]`
- [ ] A.13 ProtectedRoute + client.ts interceptor `[M]`
- [ ] A.14 Sidebar 사용자 정보 + 로그아웃 `[S]`
- [ ] A.15 App.tsx 라우팅 업데이트 `[S]`

### Stage E: E2E 검증 + 문서
- [ ] A.16 E2E 검증 `[M]`
- [ ] A.17 dev-docs 갱신 + 커밋 `[S]`

## Phase B: Chatbot 기본 루프 — ⬜ 미시작 (0/?)
> 상세 태스크: Phase B dev-docs 생성 시 확정

**예상 작업 범위** (플랜 파일 기준):
- Backend LLM: LangGraph StateGraph, tools, prompts
- Backend Chat: chat_sessions/messages, chat_service (SSE), router
- Frontend: chatStore, ChatPanel, MessageBubble, ChatInput, useSSE hook
- **파일 집계**: 신규 18 / 수정 5 / Migration 1

## Phase C: 분석 시나리오 API — ⬜ 미시작
> 상세 태스크: Phase C dev-docs 생성 시 확정
> **파일 집계 (추정)**: 신규 ~5 / 수정 ~2

## Phase D: 그래프 커스터마이징 — ⬜ 미시작
> 상세 태스크: Phase D dev-docs 생성 시 확정
> **파일 집계 (추정)**: 신규 ~12 / 수정 ~9 / Migration 1

## Phase E: Memory + Retrieval — ⬜ 미시작
> 상세 태스크: Phase E dev-docs 생성 시 확정
> **파일 집계 (추정)**: 신규 ~13 / 수정 ~3 / Migration 1

## Phase F: Onboarding + 운영 안정화 — ⬜ 미시작
> 상세 태스크: Phase F dev-docs 생성 시 확정
> **파일 집계 (추정)**: 신규 ~10 / 수정 ~3 / Migration 1

---

## Summary

### MVP (완료)
- **Phase 0**: 5 tasks ✅
- **Phase 1**: 9 tasks ✅
- **Phase 2**: 10 tasks ✅
- **Phase 3**: 12 tasks ✅
- **Phase 4**: 15 tasks ✅
- **Phase 5**: 13 tasks ✅
- **Phase 6**: 9 tasks ✅
- **Phase 7**: 6 tasks ✅
- **MVP Total**: 79 tasks + 4 hotfix = **83 tasks 완료**
- **Tests**: 409 passed, 7 skipped, ruff clean

### Post-MVP (계획)
- **Phase A**: 16 tasks (S:6, M:9, L:1) — 0/16
- **Phase B**: 미정 (파일 집계: 신규 18 / 수정 5 / Migration 1)
- **Phase C~F**: 미정 (각 Phase 진입 시 확정)
- **Post-MVP 전체 영향도 (추정)**: 신규 ~72 / 수정 ~28 / Migration 5

### Grand Total
- **MVP**: 83 tasks 완료
- **Post-MVP Phase A**: 16 tasks 계획 (0/16)
- **Post-MVP Phase B~F**: 태스크 상세 미확정

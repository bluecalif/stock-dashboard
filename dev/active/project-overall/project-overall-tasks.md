# Project Overall Tasks
> Last Updated: 2026-02-15
> Status: Phase 0~6 완료, Phase 7 계획 중

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

### 4A. 기반 구조 ✅ 완료
- [x] 4.1 FastAPI 앱 골격 (main.py, CORS, error handler, DI) `[M]`
- [x] 4.2 Pydantic 스키마 정의 `[M]` — `77e4b1d`
- [x] 4.3 Repository 계층 (DB 접근 추상화) `[M]` — `b990914`

### 4B. 조회 API ✅ 완료
- [x] 4.4 `GET /v1/health` — 헬스체크 `[S]` (Step 4.1에서 구현 완료)
- [x] 4.5 `GET /v1/assets` — 자산 목록 `[S]`
- [x] 4.6 `GET /v1/prices/daily` — 가격 조회 (pagination) `[M]`
- [x] 4.7 `GET /v1/factors` — 팩터 조회 `[M]`
- [x] 4.8 `GET /v1/signals` — 시그널 조회 `[M]`

### 4C. 백테스트 API ✅ 완료
- [x] 4.9 `GET /v1/backtests` — 백테스트 목록 `[S]` — `fac9e08`
- [x] 4.10 `GET /v1/backtests/{run_id}` + `/equity` + `/trades` `[M]` — `fac9e08`
- [x] 4.11 `POST /v1/backtests/run` — 온디맨드 백테스트 실행 `[L]` — `bb05a35`

### 4D. 집계 API + 테스트 ✅ 완료
- [x] 4.12 `GET /v1/dashboard/summary` — 대시보드 요약 `[M]` — `3171061`
- [x] 4.13 `GET /v1/correlation` — 자산 간 상관행렬 (on-the-fly) `[M]` — `7ddb5f0`
- [x] 4.14 API 단위 + 통합 테스트 `[M]` — `1d10c2e`

### 4E. E2E 검증 ✅ 완료
- [x] 4.15 E2E 파이프라인 실행 + 시각화 (백엔드 최종 검증) `[M]`

## Phase 5: 프론트엔드 (Frontend) ✅ 완료 (13/13)
> dev-docs: `dev/active/phase5-frontend/`

### 5A. 기반 구조 ✅ 완료
- [x] 5.1 Vite + React 18 + TypeScript 프로젝트 초기화 `[M]` — `f227b2b`
- [x] 5.2 API 클라이언트 (Axios) + 타입 정의 `[M]` — `f227b2b`
- [x] 5.3 레이아웃 (사이드바 네비게이션 + 메인 콘텐츠) `[M]` — `f227b2b`

### 5B. 핵심 차트 ✅ 완료
- [x] 5.4 가격 차트 페이지 (라인차트, Recharts) `[L]` — `91effb9`
- [x] 5.5 수익률 비교 차트 (정규화 누적수익률) `[M]` — `91effb9`

### 5C. 분석 시각화 ✅ 완료
- [x] 5.6 상관 히트맵 (자산 간 correlation matrix) `[M]` — `048d34d`
- [x] 5.7 팩터 현황 (RSI/MACD 서브차트 + 비교 테이블) `[M]` — `3b8ceed`
- [x] 5.8 시그널 타임라인 (가격 + 매매 마커 오버레이) `[M]` — `d0bf7a4`

### 5D. 전략 성과 + 홈 ✅ 완료
- [x] 5.9 전략 성과 비교 (에쿼티 커브 + 메트릭스 + 거래 이력) `[L]` — `aafa80d`
- [x] 5.10 대시보드 홈 (요약 카드 + 미니 차트) `[M]` — `3b583a9`

### 5E. UX 디버깅 ✅ 완료
- [x] 5.11 UX 버그: 전략 ID + X축 정렬 + 시그널 범례 `[M]` — `398f7da`
- [x] 5.12 UX 버그: Gold/Silver 에러 + 거래량 차트 `[M]` — `398f7da`
- [x] 5.13 UX 버그: 팩터/전략 데이터 + Bug #9 `[S]` — `398f7da`, `d227ee9`

## Phase 6: 배포 & 운영 (Deploy & Ops) ✅ 완료 (9/9)
> dev-docs: `dev/active/phase6-deploy/`

### 6A. 배치 통합
- [x] 6.1 리서치 파이프라인 배치 스케줄링 `[S]` — `c80fd08`
- [x] 6.4 로그 로테이션 (30일 자동 삭제) `[S]` — `c80fd08`

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
- [x] 6.6 dev-docs 갱신 & 커밋 `[S]`

## Phase 7: 스케줄 자동 수집 (Scheduled Collection) — 계획 중 (0/6)
> dev-docs: `dev/active/phase7-scheduler/`

### 7A. 사전 준비 (수동)
- [ ] 7.1 Railway Public Networking 확인/활성화 `[S]`
- [ ] 7.2 GitHub Secrets 등록 (RAILWAY_DATABASE_URL, ALERT_WEBHOOK_URL) `[S]` — blocked by 7.1

### 7B. Workflow 구현
- [ ] 7.3 `.github/workflows/daily-collect.yml` 작성 `[M]`

### 7C. 검증 + 문서
- [ ] 7.4 workflow_dispatch 수동 실행 E2E 검증 `[M]` — blocked by 7.2, 7.3
- [ ] 7.5 Runbook 업데이트 (스케줄 수집 섹션) `[S]` — blocked by 7.4
- [ ] 7.6 dev-docs 갱신 + 커밋 `[S]` — blocked by 7.5

---

## Summary
- **Phase 0~3**: 36 tasks — **ALL COMPLETE** (✅)
- **Phase 4**: 15 tasks — **ALL COMPLETE** (✅)
- **Phase 5**: 13 tasks — **ALL COMPLETE** (✅)
- **Phase 6**: 9 tasks — **ALL COMPLETE** (✅)
- **Phase 7**: 6 tasks — PLANNING (0/6)
- **Grand Total**: 79 tasks (73 complete + 6 planned)
- **Tests**: 409 passed, 7 skipped, ruff clean

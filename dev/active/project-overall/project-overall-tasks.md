# Project Overall Tasks
> Last Updated: 2026-02-12
> Status: In Progress (Phase 4 진행 중, 2/14)

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

## Phase 4: API ← 진행 중 (5/14)
> dev-docs: `dev/active/phase4-api/`

### 4A. 기반 구조 ✅ 완료
- [x] 4.1 FastAPI 앱 골격 (main.py, CORS, error handler, DI) `[M]`
- [x] 4.2 Pydantic 스키마 정의 `[M]` — `77e4b1d`
- [x] 4.3 Repository 계층 (DB 접근 추상화) `[M]` — `b990914`

### 4B. 조회 API
- [x] 4.4 `GET /v1/health` — 헬스체크 `[S]` (Step 4.1에서 구현 완료)
- [x] 4.5 `GET /v1/assets` — 자산 목록 `[S]`
- [ ] 4.6 `GET /v1/prices/daily` — 가격 조회 (pagination) `[M]`
- [ ] 4.7 `GET /v1/factors` — 팩터 조회 `[M]`
- [ ] 4.8 `GET /v1/signals` — 시그널 조회 `[M]`

### 4C. 백테스트 API
- [ ] 4.9 `GET /v1/backtests` — 백테스트 목록 `[S]`
- [ ] 4.10 `GET /v1/backtests/{run_id}` + `/equity` + `/trades` `[M]`
- [ ] 4.11 `POST /v1/backtests/run` — 온디맨드 백테스트 실행 `[L]`

### 4D. 집계 API + 테스트
- [ ] 4.12 `GET /v1/dashboard/summary` — 대시보드 요약 `[M]`
- [ ] 4.13 `GET /v1/correlation` — 자산 간 상관행렬 (on-the-fly) `[M]`
- [ ] 4.14 API 단위 + 통합 테스트 `[M]`

## Phase 5: 프론트엔드 (Frontend)
> dev-docs: `dev/active/phase5-frontend/` (생성 예정)

### 5A. 기반 + 핵심 차트
- [ ] 5.1 Vite + React 18 + TypeScript 프로젝트 초기화 `[M]`
- [ ] 5.2 API 클라이언트 (Axios) + 타입 정의 `[M]`
- [ ] 5.3 레이아웃 (사이드바 네비게이션 + 메인 콘텐츠) `[M]`
- [ ] 5.4 가격 차트 페이지 (라인/캔들, Recharts) `[L]`
- [ ] 5.5 수익률 비교 차트 (정규화 누적수익률) `[M]`

### 5B. 분석 시각화
- [ ] 5.6 상관 히트맵 (자산 간 correlation matrix) `[M]`
- [ ] 5.7 팩터 현황 (RSI/MACD 서브차트 + 비교 테이블) `[M]`
- [ ] 5.8 시그널 타임라인 (가격 + 매매 마커 오버레이) `[M]`
- [ ] 5.9 전략 성과 비교 (에쿼티 커브 + 메트릭스 + 거래 이력) `[L]`
- [ ] 5.10 대시보드 홈 (요약 카드 + 미니 차트) `[M]`

## Phase 6: 배포 & 운영 (Deploy & Ops)
> dev-docs: `dev/active/phase6-deploy/` (생성 예정)

### 6A. 환경 분리 및 설정
- [ ] 6.1 환경 분리 (dev/staging/prod .env 전략) `[M]`
- [ ] 6.2 CORS + TLS + 보안 헤더 설정 `[S]`

### 6B. 백엔드 배포
- [ ] 6.3 FastAPI 프로덕션 서버 설정 (uvicorn workers, NSSM) `[M]`
- [ ] 6.4 Alembic 프로덕션 마이그레이션 절차 `[S]`

### 6C. 프론트엔드 빌드 및 배포
- [ ] 6.5 Vite 프로덕션 빌드 + 최적화 `[M]`
- [ ] 6.6 프론트엔드 호스팅 설정 (Vercel/Netlify/Nginx) `[M]`

### 6D. CI/CD 파이프라인
- [ ] 6.7 GitHub Actions CI — lint + test + build `[L]`
- [ ] 6.8 GitHub Actions CD — 조건부 배포 `[M]`

### 6E. 스케줄러 및 배치
- [ ] 6.9 Windows Task Scheduler 배치 등록 `[M]`
- [ ] 6.10 Discord Webhook 알림 연동 `[S]`

### 6F. 모니터링 및 관측성
- [ ] 6.11 JSON 구조화 로그 + API 응답시간 미들웨어 `[M]`
- [ ] 6.12 `job_run` 기반 모니터링 `[M]`

### 6G. 백업 및 복구
- [ ] 6.13 DB 백업 스크립트 (`pg_dump`) + 복구 절차 `[M]`
- [ ] 6.14 롤백 전략 문서 (Alembic downgrade + Git rollback) `[S]`

### 6H. 운영 문서
- [ ] 6.15 배포 체크리스트 + 운영 런북 `[M]`

### 6G. Hantoo fallback (선택)
- [ ] 6.16 Hantoo REST API fallback (005930, 000660) `[L]`

---

## Summary
- **Phase 0~3**: 36 tasks — **ALL COMPLETE** (✅)
- **Phase 4**: 14 tasks — 5 완료, 9 남음 (36%)
- **Phase 5**: 10 tasks (S: 0, M: 8, L: 2, XL: 0)
- **Phase 6**: 16 tasks (S: 4, M: 9, L: 2, XL: 0)
- **Grand Total**: 76 tasks (41 완료 + 35 남음)
- **Critical Path**: Phase 4 (API) → Phase 5 (Frontend) → Phase 6 (Deploy)
- **Tests**: 294 unit + 7 integration

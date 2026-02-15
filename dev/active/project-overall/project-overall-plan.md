# Project Overall Plan
> Last Updated: 2026-02-15
> Status: In Progress (Phase 0~6 완료, Phase 7 계획 중)

## 1. Summary (개요)

**목적**: 7개 자산(KOSPI200, 삼성전자, SK하이닉스, SOXL, BTC, Gold, Silver)의 일봉 데이터 수집/저장/분석/시각화 MVP 구축.

**범위**: Phase 1~7 (골격 → 수집 → 분석 → API → 프론트엔드 → 배포/운영 → 스케줄 자동화)

**예상 결과물**:
- FDR 기반 일봉 수집 파이프라인 ✅
- PostgreSQL 데이터 저장소 (Railway) ✅
- 팩터/전략/백테스트 분석 엔진 ✅
- FastAPI 조회/백테스트/집계 API (12개 엔드포인트) ✅
- React + Recharts 대시보드 SPA (6개 페이지) ✅

## 2. Current State (현재 상태)

- **Phase 1 완료**: 프로젝트 골격, DB 8 테이블, Alembic 마이그레이션, asset_master 시드
- **Phase 2 완료**: FDR 수집기, 재시도, UPSERT, 정합성 검증, 3년 백필 (5,559 rows)
- **Phase 3 완료**: 전처리, 팩터 15개, 전략 3종, 백테스트, 성과지표, 배치 스크립트
- **Phase 4 완료**: FastAPI 12 endpoints, Router-Service-Repository 3계층, 405 tests
- **Phase 5 완료**: React SPA 6페이지, 13 steps, UX 버그 11개 수정, 사용자 확인 통과
- **Phase 6 완료**: CI/CD (GitHub Actions) + Railway 배포 + Vercel 배포 + E2E 검증
- **Git**: `master` 브랜치, 409 passed + 7 skipped, ruff clean
- **DB**: price_daily 5,573+ rows, factor_daily 55K+, signal_daily 15K+, backtest 21 runs

## 3. Target State (목표 상태)

| 영역 | 목표 | 현재 |
|------|------|------|
| 수집 | 7개 자산 일봉 자동 수집, UPSERT, 정합성 검증 | ✅ 완료 |
| DB | 8개 테이블 운영, Alembic 마이그레이션 관리 | ✅ 완료 |
| 분석 | 팩터 15종, 전략 3종, 백테스트 실행 가능 | ✅ 완료 |
| API | 12개 엔드포인트 운영 (조회/백테스트/집계) | ✅ 완료 (15 steps, 12 endpoints, 405 tests) |
| 대시보드 | 6개 페이지 (홈/가격/상관/팩터/시그널/전략성과) | ✅ 완료 (13 steps, UX 검증 완료) |
| 운영 | 일일 배치, 실패 알림, JSON 로그, 배포 | ✅ 완료 (CI/CD + Railway + Vercel) |
| 자동 수집 | GitHub Actions cron 기반 일일 자동 수집 | 계획 중 (Phase 7) |

## 4. Implementation Phases (구현 단계)

### Phase 1: 프로젝트 골격 + DB ✅ 완료
- Python 프로젝트 초기화 (`pyproject.toml`, `config/settings.py`)
- DB 모델 정의 (SQLAlchemy 8 테이블) + Alembic 마이그레이션
- `asset_master` 시드 + `db/session.py` SessionLocal
- 9 tasks, 9 commits

### Phase 2: 수집기 (Collector) ✅ 완료
- `collector/fdr_client.py` — FDR 래퍼 + 심볼 매핑 + 재시도
- `collector/ingest.py` — UPSERT 오케스트레이션 + 부분 실패 허용
- `collector/validators.py` — OHLCV 정합성 검증
- `collector/alerting.py` — Discord 실패 알림
- `scripts/collect.py` — 수집 배치 CLI
- 3년 백필 완료: 5,559 rows, 7개 자산
- 10 tasks, 10 commits

### Phase 3: 분석 엔진 (Research Engine) ✅ 완료
- `research_engine/preprocessing.py` — 캘린더 정렬, 결측 처리, 이상치 플래그
- `research_engine/factors.py` — 15개 팩터 계산
- `research_engine/factor_store.py` — factor_daily UPSERT
- `research_engine/strategies/` — Strategy ABC + 3종 전략 (모멘텀/추세/평균회귀)
- `research_engine/signal_store.py` — signal_daily DELETE+INSERT
- `research_engine/backtest.py` — BacktestEngine (단일/다중 자산)
- `research_engine/metrics.py` — 성과 지표 13개 (CAGR, MDD, Sharpe 등)
- `research_engine/backtest_store.py` — backtest_run/equity_curve/trade_log 저장
- `scripts/run_research.py` — 분석 배치 CLI (factor→signal→backtest→DB)
- 12 tasks, 8 commits, 223 unit + 7 integration tests

### Phase 4: API ✅ 완료
> dev-docs: `dev/active/phase4-api/`

**Stage A: 기반 구조** (Step 4.1~4.3)
- FastAPI 앱 골격 (main.py, CORS, error handler, DI)
- Pydantic v2 스키마 (요청/응답 분리)
- Repository 계층 (DB 접근 추상화)

**Stage B: 조회 API** (Step 4.4~4.8)
- 5개 엔드포인트: health, assets, prices/daily, factors, signals
- Pagination (limit/offset, 기본 500)

**Stage C: 백테스트 API** (Step 4.9~4.11)
- 조회 3개: backtests 목록, {run_id} 상세, equity, trades
- 실행 1개: POST /backtests/run (research_engine 연동)

**Stage D: 집계 + 테스트** (Step 4.12~4.14)
- dashboard/summary, correlation (on-the-fly)
- httpx TestClient 단위/통합 테스트

### Phase 5: 프론트엔드 (Frontend) ✅ 완료
> dev-docs: `dev/active/phase5-frontend/`

**Stage A: 기반 구조** (Step 5.1~5.3) ✅
- Vite 6.4 + React 19 + TypeScript 5.9 + TailwindCSS 3.4
- Axios API 클라이언트 + 14개 TypeScript 타입 (백엔드 Pydantic 1:1)
- 사이드바 레이아웃 + React Router v6 (6개 경로)

**Stage B: 핵심 차트** (Step 5.4~5.5) ✅
- 가격 차트 (라인차트 + ComposedChart 거래량) + 수익률 비교 차트

**Stage C: 분석 시각화** (Step 5.6~5.8) ✅
- 상관 히트맵, 팩터 현황 (RSI/MACD), 시그널 타임라인 (매매 마커)

**Stage D: 전략 성과 + 홈** (Step 5.9~5.10) ✅
- 에쿼티 커브 비교 + 메트릭스 + 거래 이력, 대시보드 홈

**Stage E: UX 디버깅** (Step 5.11~5.13) ✅
- UX 버그 11개 수정 (전략 ID, X축 정렬, CORS, NaN, missing_threshold 등)
- 13 tasks, 11 commits, 사용자 UX 확인 완료

### Phase 6: 배포 & 운영 (Deploy & Ops) ✅ 완료
> dev-docs: `dev/active/phase6-deploy/`

- CI/CD: GitHub Actions (lint + test + deploy-railway + deploy-vercel)
- 배포: Railway (백엔드) + Vercel (프론트엔드)
- CORS 설정 + E2E 검증 완료
- 9 tasks, 13 steps

### Phase 7: 스케줄 자동 수집 (Scheduled Collection) — 계획 중
> dev-docs: `dev/active/phase7-scheduler/`
> 스코프: GitHub Actions cron으로 일일 수집 파이프라인 자동화

**Stage A: 사전 준비** (Step 7.1~7.2)
- Railway PostgreSQL Public Networking 활성화
- GitHub Secrets 등록 (RAILWAY_DATABASE_URL, ALERT_WEBHOOK_URL)

**Stage B: Workflow 구현** (Step 7.3)
- `.github/workflows/daily-collect.yml` — cron (KST 18:00) + workflow_dispatch
- 파이프라인: collect.py → healthcheck.py → run_research.py

**Stage C: 검증 + 문서** (Step 7.4~7.6)
- workflow_dispatch 수동 실행 E2E 검증
- Runbook 업데이트 + dev-docs 갱신

## 5. 데이터 흐름

```
GitHub Actions cron (KST 18:00) → collector (FDR) → price_daily
                                   ↓
                         research_engine (preprocessing → factors → signals → backtest)
                                   ↓
                         factor_daily / signal_daily / backtest_* DB
                                   ↓
                         API (FastAPI, 12 endpoints)
                                   ↓
                         Frontend (React + Recharts, 6 pages)
```

## 6. Risks & Mitigation (리스크 및 완화)

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| FDR 단일 소스 장애 | 전 자산 수집 중단 | 중 | Phase 6에서 Hantoo fallback 추가, FDR 실패율 모니터링 |
| Railway PostgreSQL 연결 불안정 | 데이터 적재/조회 불가 | 저 | TLS 강제, 커넥션 풀링, 헬스체크 |
| Windows 단일 호스트 장애 | 수집 중단 (Phase 7에서 해소) | 저 | GitHub Actions cron으로 이전 |
| GitHub Actions cron 지연 | 수집 시간 최대 15분 변동 | 저 | 장 마감 후이므로 허용 범위 |
| API 상관행렬 on-the-fly 성능 | 응답 지연 | 저 | 데이터량 소규모(7자산×3년), 캐싱 고려 |
| 대시보드 대량 데이터 렌더 | UX 저하 | 저 | Pagination, 날짜 범위 제한, 데이터 다운샘플 |
| 프로덕션 환경변수 유출 | 보안 침해 | 중 | GitHub Secrets, `.env` gitignore |

## 7. Dependencies (의존성)

### 외부
- **Railway PostgreSQL**: DB 호스팅 — `DATABASE_URL` 설정 ✅
- **FinanceDataReader**: 전 자산 데이터 소스 — 검증 완료 ✅
- **Discord Webhook**: 알림 채널 — Phase 6에서 연동
- **GitHub Actions**: CI/CD — Phase 6에서 설정

### 기술
- Python 3.12.3, Node.js 18+, PostgreSQL 15+ (Railway)
- venv: `backend/.venv/` (Windows)

# Project Overall Plan
> Last Updated: 2026-02-13
> Status: In Progress (Phase 4 진행 중, Step 4.11 완료)

## 1. Summary (개요)

**목적**: 7개 자산(KOSPI200, 삼성전자, SK하이닉스, SOXL, BTC, Gold, Silver)의 일봉 데이터 수집/저장/분석/시각화 MVP 구축.

**범위**: Phase 1~6 (골격 → 수집 → 분석 → API → 프론트엔드 → 배포/운영)

**예상 결과물**:
- FDR 기반 일봉 수집 파이프라인 ✅
- PostgreSQL 데이터 저장소 (Railway) ✅
- 팩터/전략/백테스트 분석 엔진 ✅
- FastAPI 조회/백테스트/집계 API (12개 엔드포인트)
- React + Recharts 대시보드 SPA (6개 페이지)

## 2. Current State (현재 상태)

- **Phase 1 완료**: 프로젝트 골격, DB 8 테이블, Alembic 마이그레이션, asset_master 시드
- **Phase 2 완료**: FDR 수집기, 재시도, UPSERT, 정합성 검증, 3년 백필 (5,559 rows)
- **Phase 3 완료**: 전처리, 팩터 15개, 전략 3종, 백테스트, 성과지표, 배치 스크립트
- **Git**: `master` 브랜치, 347 unit + 7 integration tests, ruff clean
- **DB**: price_daily 5,559 rows, 7개 자산 (2023-02 ~ 2026-02)

## 3. Target State (목표 상태)

| 영역 | 목표 | 현재 |
|------|------|------|
| 수집 | 7개 자산 일봉 자동 수집, UPSERT, 정합성 검증 | ✅ 완료 |
| DB | 8개 테이블 운영, Alembic 마이그레이션 관리 | ✅ 완료 |
| 분석 | 팩터 15종, 전략 3종, 백테스트 실행 가능 | ✅ 완료 |
| API | 12개 엔드포인트 운영 (조회/백테스트/집계) | Step 4.11 완료 (Stage A+B+C 완료, 10개 엔드포인트) |
| 대시보드 | 6개 페이지 (홈/가격/상관/팩터/시그널/전략성과) | 미착수 |
| 운영 | 일일 배치, 실패 알림, JSON 로그, 배포 | 부분 (배치만 완료) |

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

### Phase 4: API ← 다음 단계
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

### Phase 5: 프론트엔드 (Frontend)
- Vite + React 18 + TypeScript 프로젝트 초기화
- API 클라이언트 + 타입 정의
- 6개 페이지:
  1. 대시보드 홈 (요약 카드 + 미니 차트)
  2. 가격/수익률 (라인 차트 + 정규화 누적수익률 비교)
  3. 상관 히트맵 (자산 간 rolling correlation)
  4. 팩터 현황 (RSI/MACD 서브차트 + 비교 테이블)
  5. 시그널 타임라인 (가격 + 매매 마커 오버레이)
  6. 전략 성과 (에쿼티 커브 + 메트릭스 카드 + 거래 이력)

### Phase 6: 배포 & 운영 (Deploy & Ops)

#### 6A. 환경 분리 및 설정
- 환경별 설정 분리 (dev / staging / prod)
- Production `.env` 관리 (Railway env vars)
- CORS_ORIGINS 화이트리스트, DB TLS 강제

#### 6B. 백엔드 배포
- FastAPI 프로덕션 서버 (uvicorn workers, NSSM/Windows Service)
- Alembic 프로덕션 마이그레이션 절차

#### 6C. 프론트엔드 빌드 및 배포
- Vite 프로덕션 빌드 + 최적화
- 정적 파일 호스팅 (Vercel / Netlify / Nginx)

#### 6D. CI/CD 파이프라인
- GitHub Actions: lint + test + build + 조건부 배포

#### 6E. 스케줄러 및 배치
- Windows Task Scheduler 일일 수집 + 분석 순차 실행
- Discord Webhook 알림

#### 6F. 모니터링, 백업, 문서
- JSON 구조화 로그, API 응답시간 미들웨어
- DB 백업 (`pg_dump`), 복구 절차
- 배포 체크리스트, 운영 런북

#### 6G. Hantoo fallback (선택, v0.9+)
- 국내주식(005930, 000660) REST API 이중화

## 5. 데이터 흐름

```
scheduler → collector (FDR) → price_daily
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
| Windows 단일 호스트 장애 | 전체 서비스 중단 | 중 | 주기 백업, 재기동 스크립트 |
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

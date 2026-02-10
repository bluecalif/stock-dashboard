# Project Overall Plan
> Last Updated: 2026-02-10
> Status: Planning

## 1. Summary (개요)

**목적**: 7개 자산(KOSPI200, 삼성전자, SK하이닉스, SOXL, BTC, Gold, Silver)의 일봉 데이터 수집/저장/분석/시각화 MVP 구축.

**범위**: Phase 0(문서/온보딩) 완료 상태에서 Phase 1~6(구현~배포~운영)까지 전체 프로젝트 로드맵.

**예상 결과물**:
- FDR 기반 일봉 수집 파이프라인
- PostgreSQL 데이터 저장소 (Railway)
- 팩터/전략/백테스트 분석 엔진
- FastAPI 조회 API
- React + Recharts 대시보드 SPA

## 2. Current State (현재 상태)

- **Phase 0 완료**: 문서 전용 상태. 앱 코드 없음.
- **Git**: `master` 브랜치, 초기 커밋 `6c66d35` (26개 문서 파일)
- **데이터 접근성**: **Conditional Go** — FDR 전 자산 PASS, `DATABASE_URL` 미설정만 잔존
- **기존 파일**: 마스터플랜, 데이터 접근성 검증 보고서, CLAUDE.md, Skills, 온보딩 문서

## 3. Target State (목표 상태)

| 영역 | 목표 |
|------|------|
| 수집 | 7개 자산 일봉 자동 수집, UPSERT, 정합성 검증 |
| DB | 8개 테이블 운영, Alembic 마이그레이션 관리 |
| 분석 | 팩터 15종, 전략 3종, 백테스트 실행 가능 |
| API | 9개 엔드포인트 운영 (`/v1/*`) |
| 대시보드 | 가격/수익률/상관/전략 성과 4개 화면 |
| 운영 | 일일 배치, 실패 알림(Discord), JSON 로그 |

## 4. Implementation Phases (구현 단계)

### Phase 1: 프로젝트 골격 + DB + 수집 기본 (Week 1)
- Python 프로젝트 초기화 (`pyproject.toml`)
- DB 모델 정의 (SQLAlchemy) + Alembic 초기화
- `asset_master` 시드 데이터
- `collector/fdr_client.py` — FDR 래퍼
- `collector/ingest.py` — 기본 수집 오케스트레이션
- `collector/validators.py` — OHLCV 정합성 검증
- 기본 단위 테스트

### Phase 2: 수집기 안정화 + 정합성/복구 (Week 2)
- 지수 백오프 재시도
- idempotent UPSERT 구현
- 자산 단위 지연 처리 (부분 실패 허용)
- `job_run` 테이블 기록
- 정합성 검증 강화 (고가/저가 역전, 음수, 중복)
- 3년 백필 실행 및 검증

### Phase 3: 팩터 + 전략 엔진 (Week 3)
- `research_engine/factors.py` — 팩터 15종 생성
- `research_engine/strategies.py` — 전략 3종 (모멘텀/추세/평균회귀)
- `factor_daily`, `signal_daily` 테이블 적재
- 전략 신호 경계값 단위 테스트

### Phase 4: 백테스트 + API + 대시보드 (Week 4)
- `research_engine/backtest.py` — 백테스트 실행기
- `backtest_run`, `backtest_equity_curve`, `backtest_trade_log` 적재
- FastAPI 서버 (`api/`) — 9개 엔드포인트
- Router-Service-Repository 패턴
- React 대시보드 (`dashboard/`) — Vite + TypeScript + Recharts
- 4개 화면: 가격, 수익률, 상관관계, 전략 성과

### Phase 5: Hantoo fallback + 통합테스트 + QA (Week 5)
- Hantoo REST API fallback (005930, 000660)
- E2E 통합 테스트 (`collector → DB → research_engine → API → dashboard`)
- 회귀 테스트 (고정 샘플 스냅샷)
- API 부하 테스트 (동시 접속 시나리오)
- 보안 점검 (환경변수 노출, CORS, SQL injection, XSS)

### Phase 6: 배포 + 인프라 + 운영 (Week 5~6)

#### 6A. 환경 분리 및 설정
- 환경별 설정 분리 (dev / staging / prod)
- Production `.env` 관리 전략 (Railway env vars, 로컬 `.env.production`)
- `CORS_ORIGINS` 환경변수로 화이트리스트 관리
- DB TLS 연결 강제 확인
- `PYTHONUTF8=1` 프로덕션 환경 적용

#### 6B. 백엔드 배포
- FastAPI 프로덕션 서버 설정 (uvicorn workers, host/port)
- 프로세스 매니저 적용 (NSSM 또는 Windows Service로 등록)
- Alembic 마이그레이션 프로덕션 실행 절차
- API 헬스체크 엔드포인트 (`/v1/health`) 모니터링 연동
- Gunicorn/uvicorn 워커 수 튜닝

#### 6C. 프론트엔드 빌드 및 배포
- Vite 프로덕션 빌드 (`vite build`)
- 정적 파일 호스팅 전략 결정 (Vercel / Netlify / Nginx on Windows)
- API base URL 환경변수 (`VITE_API_URL`)
- 빌드 최적화 (코드 스플리팅, 트리셰이킹, 에셋 해시)
- SPA 라우팅 fallback 설정

#### 6D. CI/CD 파이프라인
- GitHub Actions 워크플로우:
  - **lint**: `ruff check .` + `eslint`
  - **test**: `pytest` + `vitest`
  - **build**: Python 패키지 검증 + Vite 빌드
  - **deploy**: 조건부 배포 (main 브랜치 push 시)
- PR 체크 자동화 (lint + test 필수 통과)
- 시크릿 관리 (GitHub Secrets → `DATABASE_URL`, `ALERT_WEBHOOK_URL`)

#### 6E. 스케줄러 및 배치
- Windows Task Scheduler 일일 수집 배치 등록
- 수집 → 분석 순차 실행 스크립트
- 배치 실패 시 Discord Webhook 알림
- 배치 실행 로그 파일 로테이션

#### 6F. 모니터링 및 관측성
- JSON 구조화 로그 (수집기/API/분석 엔진)
- `job_run` 테이블 기반 작업 성공/실패율 대시보드
- API 응답시간 로깅 (미들웨어)
- 디스크 사용량 / DB 용량 모니터링
- Discord 알림 채널: 수집 실패, API 에러, 배치 이상

#### 6G. 백업 및 복구
- Railway PostgreSQL 자동 백업 확인 및 보존 정책
- 수동 백업 스크립트 (`pg_dump`)
- 복구 절차 문서화 (`pg_restore`)
- 롤백 전략: Alembic downgrade 절차, Git 기반 코드 롤백

#### 6H. 운영 문서
- 배포 체크리스트 (deploy-checklist.md)
- 운영 런북 (runbook.md): 장애 대응 절차
- 환경변수 목록 및 설명
- 아키텍처 다이어그램 최종본

## 5. Task Breakdown (태스크 목록)

### Phase 1 (Week 1)
| # | Task | Size | Dependencies |
|---|------|------|-------------|
| 1.1 | `pyproject.toml` + 의존성 설치 | S | - |
| 1.2 | `.env.example` + `DATABASE_URL` 설정 | S | 1.1 |
| 1.3 | `db/models.py` — SQLAlchemy 모델 8개 테이블 | M | 1.1 |
| 1.4 | Alembic 초기화 + 초기 마이그레이션 | M | 1.2, 1.3 |
| 1.5 | `asset_master` 시드 스크립트 | S | 1.4 |
| 1.6 | `collector/fdr_client.py` — FDR 래퍼 | M | 1.1 |
| 1.7 | `collector/validators.py` — 정합성 검증 | M | 1.1 |
| 1.8 | `collector/ingest.py` — 수집 오케스트레이션 | L | 1.3, 1.6, 1.7 |
| 1.9 | 단위 테스트 (심볼 매핑, 검증, 수집) | M | 1.6, 1.7, 1.8 |

### Phase 2 (Week 2)
| # | Task | Size | Dependencies |
|---|------|------|-------------|
| 2.1 | 지수 백오프 재시도 로직 | M | 1.6 |
| 2.2 | idempotent UPSERT 구현 | M | 1.8 |
| 2.3 | 부분 실패 허용 + `job_run` 기록 | M | 1.3 |
| 2.4 | 정합성 검증 강화 | S | 1.7 |
| 2.5 | 3년 백필 실행 + 검증 | L | 2.1, 2.2 |

### Phase 3 (Week 3)
| # | Task | Size | Dependencies |
|---|------|------|-------------|
| 3.1 | `factors.py` — 팩터 15종 | L | 1.3 |
| 3.2 | `strategies.py` — 전략 3종 | L | 3.1 |
| 3.3 | `factor_daily`/`signal_daily` 적재 파이프라인 | M | 3.1, 3.2 |
| 3.4 | 팩터/전략 단위 테스트 | M | 3.1, 3.2 |

### Phase 4 (Week 4)
| # | Task | Size | Dependencies |
|---|------|------|-------------|
| 4.1 | `backtest.py` — 백테스트 실행기 | XL | 3.2 |
| 4.2 | 백테스트 결과 테이블 적재 | M | 4.1 |
| 4.3 | FastAPI 서버 기본 구조 | M | 1.3 |
| 4.4 | API 엔드포인트 9개 구현 | L | 4.3 |
| 4.5 | Pydantic 스키마 정의 | M | 4.3 |
| 4.6 | React 프로젝트 초기화 (Vite + TS) | M | - |
| 4.7 | 대시보드 4개 화면 구현 | XL | 4.4, 4.6 |

### Phase 5 (Week 5) — 통합테스트 + QA
| # | Task | Size | Dependencies |
|---|------|------|-------------|
| 5.1 | Hantoo REST API fallback | L | 2.2 |
| 5.2 | E2E 통합 테스트 (collector → DB → engine → API → dashboard) | L | 4.4, 4.7 |
| 5.3 | 회귀 테스트 (고정 샘플 스냅샷) | M | 5.2 |
| 5.4 | API 부하 테스트 (동시 접속 시나리오) | M | 4.4 |
| 5.5 | 보안 점검 (env 노출, CORS, injection, XSS) | M | 4.4, 4.7 |

### Phase 6 (Week 5~6) — 배포 + 인프라 + 운영
| # | Task | Size | Dependencies |
|---|------|------|-------------|
| 6.1 | 환경 분리 (dev/staging/prod .env 전략) | M | 1.2 |
| 6.2 | CORS + TLS + 보안 헤더 설정 | S | 4.3 |
| 6.3 | FastAPI 프로덕션 서버 설정 (uvicorn workers, NSSM) | M | 4.3 |
| 6.4 | Alembic 프로덕션 마이그레이션 절차 | S | 1.4 |
| 6.5 | Vite 프로덕션 빌드 + 최적화 | M | 4.6 |
| 6.6 | 프론트엔드 호스팅 설정 (Vercel/Netlify/Nginx) | M | 6.5 |
| 6.7 | GitHub Actions CI — lint + test + build | L | 5.2 |
| 6.8 | GitHub Actions CD — 조건부 배포 | M | 6.7 |
| 6.9 | Windows Task Scheduler 배치 등록 | M | 2.5 |
| 6.10 | Discord Webhook 알림 연동 | S | 2.3 |
| 6.11 | JSON 구조화 로그 + API 응답시간 미들웨어 | M | 4.3 |
| 6.12 | `job_run` 기반 모니터링 대시보드 | M | 2.3, 4.7 |
| 6.13 | DB 백업 스크립트 (`pg_dump`) + 복구 절차 | M | 1.4 |
| 6.14 | 롤백 전략 문서 (Alembic downgrade + Git rollback) | S | 6.4 |
| 6.15 | 배포 체크리스트 + 운영 런북 작성 | M | 6.1~6.14 |

**총계**: 37개 태스크 (S: 8, M: 18, L: 7, XL: 4)

## 6. Risks & Mitigation (리스크 및 완화)

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| FDR 단일 소스 장애 | 전 자산 수집 중단 | 중 | Phase 5에서 Hantoo fallback 추가, FDR 실패율 모니터링 |
| Railway PostgreSQL 연결 불안정 | 데이터 적재/조회 불가 | 저 | TLS 강제, 커넥션 풀링, 헬스체크 |
| Windows 단일 호스트 장애 | 전체 서비스 중단 | 중 | 주기 백업, 재기동 스크립트 |
| FDR/외부 API 스키마 변경 | 수집 파이프라인 파손 | 저 | 스키마 검증 레이어, 알림 |
| 대시보드 성능 (대량 데이터) | UX 저하 | 저 | 페이지네이션, 날짜 범위 제한 |
| 프로덕션 환경변수 유출 | 보안 침해 | 중 | GitHub Secrets, `.env` gitignore, 코드 리뷰 |
| Alembic 마이그레이션 실패 (프로덕션) | 서비스 중단 | 중 | 스테이징 사전 검증, downgrade 절차 준비 |
| CI/CD 파이프라인 중단 | 배포 불가 | 저 | GitHub Actions 상태 모니터링, 수동 배포 fallback |
| 프론트엔드 빌드 실패 | 대시보드 접근 불가 | 저 | 이전 빌드 캐시 유지, 빌드 알림 |

## 7. Dependencies (의존성)

### 외부 의존성
- **Railway PostgreSQL**: DB 호스팅 — `DATABASE_URL` 설정 필수 (현재 미설정)
- **FinanceDataReader**: 전 자산 데이터 소스 — 검증 완료 (Conditional Go)
- **Discord Webhook**: 알림 채널 — Phase 6에서 설정
- **GitHub Actions**: CI/CD — Phase 6에서 설정
- **Vercel / Netlify / Nginx**: 프론트엔드 호스팅 — Phase 6에서 결정

### 기술 의존성
- Python 3.11+ (FDR, FastAPI 호환)
- Node.js 18+ (Vite, React)
- PostgreSQL 15+ (Railway)
- NSSM 또는 Windows Service (백엔드 프로세스 매니저)
- Git + GitHub (CI/CD, 코드 관리)

### 선행 작업
- `DATABASE_URL` 환경변수 설정 → DB 연결 검증 → Task 1.4(Alembic) 이후 가능 (1.1/1.3/1.6/1.7은 DB 없이 선행 가능)
- GitHub Secrets 설정 → Phase 6 CI/CD 가능
- 프론트엔드 호스팅 계정 준비 → Phase 6C 가능

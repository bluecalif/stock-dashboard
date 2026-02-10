# Project Overall Tasks
> Last Updated: 2026-02-10
> Status: Planning

## Phase 0: 사전 준비 (완료)
- [x] 마스터플랜 작성 (docs/masterplan-v0.md)
- [x] 데이터 접근성 검증 (Conditional Go)
- [x] CLAUDE.md + Skills + Hooks 설정
- [x] Git 초기화 + remote 설정 + push
- [x] Kiwoom 폐기, FDR 단일 소스 결정

## Phase 1: 프로젝트 골격 + DB + 수집 기본 (Week 1)
- [ ] 1.1 `pyproject.toml` + 의존성 설치 `[S]`
- [ ] 1.2 `.env.example` + `DATABASE_URL` 설정 `[S]`
- [ ] 1.3 `db/models.py` — SQLAlchemy 모델 8개 테이블 `[M]` → depends: 1.1
- [ ] 1.4 Alembic 초기화 + 초기 마이그레이션 `[M]` → depends: 1.3
- [ ] 1.5 `asset_master` 시드 스크립트 `[S]` → depends: 1.4
- [ ] 1.6 `collector/fdr_client.py` — FDR 래퍼 `[M]` → depends: 1.1
- [ ] 1.7 `collector/validators.py` — 정합성 검증 `[M]` → depends: 1.1
- [ ] 1.8 `collector/ingest.py` — 수집 오케스트레이션 `[L]` → depends: 1.3, 1.6, 1.7
- [ ] 1.9 단위 테스트 (심볼 매핑, 검증, 수집) `[M]` → depends: 1.6, 1.7, 1.8

## Phase 2: 수집기 안정화 + 정합성/복구 (Week 2)
- [ ] 2.1 지수 백오프 재시도 로직 `[M]` → depends: 1.6
- [ ] 2.2 idempotent UPSERT 구현 `[M]` → depends: 1.8
- [ ] 2.3 부분 실패 허용 + `job_run` 기록 `[M]` → depends: 1.3
- [ ] 2.4 정합성 검증 강화 `[S]` → depends: 1.7
- [ ] 2.5 3년 백필 실행 + 검증 `[L]` → depends: 2.1, 2.2

## Phase 3: 팩터 + 전략 엔진 (Week 3)
- [ ] 3.1 `factors.py` — 팩터 15종 `[L]` → depends: 1.3
- [ ] 3.2 `strategies.py` — 전략 3종 `[L]` → depends: 3.1
- [ ] 3.3 `factor_daily`/`signal_daily` 적재 파이프라인 `[M]` → depends: 3.1, 3.2
- [ ] 3.4 팩터/전략 단위 테스트 `[M]` → depends: 3.1, 3.2

## Phase 4: 백테스트 + API + 대시보드 (Week 4)
- [ ] 4.1 `backtest.py` — 백테스트 실행기 `[XL]` → depends: 3.2
- [ ] 4.2 백테스트 결과 테이블 적재 `[M]` → depends: 4.1
- [ ] 4.3 FastAPI 서버 기본 구조 `[M]` → depends: 1.3
- [ ] 4.4 API 엔드포인트 9개 구현 `[L]` → depends: 4.3
- [ ] 4.5 Pydantic 스키마 정의 `[M]` → depends: 4.3
- [ ] 4.6 React 프로젝트 초기화 (Vite + TS) `[M]`
- [ ] 4.7 대시보드 4개 화면 구현 `[XL]` → depends: 4.4, 4.6

## Phase 5: Hantoo fallback + 통합테스트 + QA (Week 5)
- [ ] 5.1 Hantoo REST API fallback `[L]` → depends: 2.2
- [ ] 5.2 E2E 통합 테스트 (collector → DB → engine → API → dashboard) `[L]` → depends: 4.4, 4.7
- [ ] 5.3 회귀 테스트 (고정 샘플 스냅샷) `[M]` → depends: 5.2
- [ ] 5.4 API 부하 테스트 (동시 접속 시나리오) `[M]` → depends: 4.4
- [ ] 5.5 보안 점검 (env 노출, CORS, injection, XSS) `[M]` → depends: 4.4, 4.7

## Phase 6: 배포 + 인프라 + 운영 (Week 5~6)

### 6A. 환경 분리 및 설정
- [ ] 6.1 환경 분리 (dev/staging/prod .env 전략) `[M]` → depends: 1.2
- [ ] 6.2 CORS + TLS + 보안 헤더 설정 `[S]` → depends: 4.3

### 6B. 백엔드 배포
- [ ] 6.3 FastAPI 프로덕션 서버 설정 (uvicorn workers, NSSM) `[M]` → depends: 4.3
- [ ] 6.4 Alembic 프로덕션 마이그레이션 절차 `[S]` → depends: 1.4

### 6C. 프론트엔드 빌드 및 배포
- [ ] 6.5 Vite 프로덕션 빌드 + 최적화 `[M]` → depends: 4.6
- [ ] 6.6 프론트엔드 호스팅 설정 (Vercel/Netlify/Nginx) `[M]` → depends: 6.5

### 6D. CI/CD 파이프라인
- [ ] 6.7 GitHub Actions CI — lint + test + build `[L]` → depends: 5.2
- [ ] 6.8 GitHub Actions CD — 조건부 배포 `[M]` → depends: 6.7

### 6E. 스케줄러 및 배치
- [ ] 6.9 Windows Task Scheduler 배치 등록 `[M]` → depends: 2.5
- [ ] 6.10 Discord Webhook 알림 연동 `[S]` → depends: 2.3

### 6F. 모니터링 및 관측성
- [ ] 6.11 JSON 구조화 로그 + API 응답시간 미들웨어 `[M]` → depends: 4.3
- [ ] 6.12 `job_run` 기반 모니터링 대시보드 `[M]` → depends: 2.3, 4.7

### 6G. 백업 및 복구
- [ ] 6.13 DB 백업 스크립트 (`pg_dump`) + 복구 절차 `[M]` → depends: 1.4
- [ ] 6.14 롤백 전략 문서 (Alembic downgrade + Git rollback) `[S]` → depends: 6.4

### 6H. 운영 문서
- [ ] 6.15 배포 체크리스트 + 운영 런북 작성 `[M]` → depends: 6.1~6.14

---

## Summary
- **Total Tasks**: 37
- **Size Distribution**: S: 8, M: 18, L: 7, XL: 4
- **Critical Path**: 1.1 → 1.3 → 1.8 → 2.2 → 3.1 → 3.2 → 4.1 → 4.4 → 5.2 → 6.7 → 6.8
- **Blocker**: `DATABASE_URL` 설정 (Phase 1 시작 전 필수)
- **배포 선행 조건**: GitHub Secrets 설정, 프론트엔드 호스팅 계정 준비

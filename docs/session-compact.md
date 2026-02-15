# Session Compact

> Generated: 2026-02-15 10:00
> Source: Conversation compaction via /compact-and-go

## Goal
Phase 6 (Deploy & Ops) 구현 — 통합 검증 + CI/CD + 실배포 + 운영 안정화. 9개 Step 실행.

## Completed
- [x] **Phase 6 dev-docs 생성** (`/dev-docs` 스킬 실행, 이전 세션)
- [x] **project-overall 동기화** (이전 세션)
- [x] **Phase 6 스코프 확장**: CI/CD + 실배포 포함으로 dev-docs 재작성 (6 tasks → 9 tasks)
  - `phase6-deploy-plan.md` — 9 tasks, 6 stages (A~F), Railway + Vercel + GitHub Actions 포함
  - `phase6-deploy-tasks.md` — 6.7/6.8/6.9 신규 추가, Summary 9개
  - `phase6-deploy-context.md` — 배포 아키텍처/CI/CD 흐름/결정사항 7건/컨벤션 체크리스트
  - `docs/session-compact.md` — TODO 9개, Key Decisions 갱신

## Current State

### 프로젝트 진행률
| Phase | 상태 | Tasks |
|-------|------|-------|
| 1-5 (Skeleton~Frontend) | ✅ 완료 | 64/64 |
| 6 Deploy & Ops | 진행 중 | 2/9 |

### Phase 6 태스크 (9개, 모두 미완료)
| # | Task | Size | Stage |
|---|------|------|-------|
| 6.1 | 리서치 파이프라인 배치 스케줄링 | S | A: 배치 통합 |
| 6.4 | 로그 로테이션 | S | A: 배치 통합 |
| 6.2 | 테스트 전체 실행 & 검증 | M | B: 테스트 검증 |
| 6.3 | Pre-deployment 체크 스크립트 | M | C: 운영 도구 |
| 6.7 | GitHub Actions CI 파이프라인 | M | D: CI/CD |
| 6.8 | 백엔드 Railway 배포 | M | E: 프로덕션 배포 |
| 6.9 | 프론트엔드 Vercel 배포 | M | E: 프로덕션 배포 |
| 6.5 | 운영 문서 (Runbook) | M | F: 문서화 |
| 6.6 | dev-docs 갱신 & 커밋 | S | F: 문서화 |

### Changed Files (이번 세션)
```
dev/active/phase6-deploy/
├── phase6-deploy-plan.md      (수정: CI/CD + 배포 추가)
├── phase6-deploy-context.md   (수정: 배포 인프라 추가)
├── phase6-deploy-tasks.md     (수정: 9 tasks로 확장)
└── debug-history.md           (기존, 미변경)

docs/session-compact.md        (수정: 스코프 확장 반영)
```

### Git / Tests
- Branch: `master`, Phase 6 dev-docs 전체 미커밋 (untracked)
- project-overall 3개 파일도 미커밋 (modified)
- Tests: 미실행 (Step 6.2에서 확인 예정)

## Remaining / TODO
- [x] **Step 6.1**: `daily_collect.bat`에 `run_research.py` 호출 추가 (collect → healthcheck → research)
- [x] **Step 6.4**: `daily_collect.bat`에 30일 로그 로테이션 추가
- [ ] **Step 6.2**: `python -m pytest` 전체 실행, 실패 수정
- [ ] **Step 6.3**: `backend/scripts/preflight.py` 신규 생성 (.env/DB/테이블/시드/데이터 검증)
- [ ] **Step 6.7**: `.github/workflows/ci.yml` 생성 (pytest + ruff, PostgreSQL service container)
- [ ] **Step 6.8**: Railway App 배포 (Procfile, railway.toml, requirements.txt, CORS 수정)
- [ ] **Step 6.9**: Vercel 배포 (vercel.json, VITE_API_BASE_URL 환경변수 처리)
- [ ] **Step 6.5**: `docs/runbook.md` 운영 문서 생성 (배포 절차 포함)
- [ ] **Step 6.6**: dev-docs 갱신 + 전체 커밋 + session-compact 갱신

## Key Decisions
- **Phase 6 스코프 확장** (2026-02-15): CI/CD + 실배포 포함. 6 tasks → 9 tasks
- **백엔드 배포: Railway App**: 기존 Railway PostgreSQL과 동일 프로젝트, 내부 네트워크 활용
- **프론트엔드 배포: Vercel**: React SPA 정적 배포, GitHub 연동 자동 배포
- **CI: GitHub Actions**: pytest + ruff, PostgreSQL service container, 무료 티어
- **Discord webhook**: 미설정 상태 → 코드 검증만, 실발송 테스트 제외
- **로그 로테이션**: Windows `forfiles` 커맨드로 30일 자동 삭제

## Context
다음 세션에서는 답변에 한국어를 사용하세요.
- **작업 디렉토리**: `backend/` (Python) + `frontend/` (React)
- **venv**: `backend/.venv/Scripts/activate` (Windows), Python 3.12.3
- **Bash 경로**: `/c/Projects-2026/stock-dashboard` (Windows 백슬래시 불가)
- **기존 배치 구조**: `daily_collect.bat` — collect.py → healthcheck.py 순차 실행 (run_research.py 미포함)
- **run_research.py 인자**: `--start YYYY-MM-DD --end YYYY-MM-DD` (필수), `--assets`, `--strategy` (선택)
- **preflight.py 검증 항목**: DATABASE_URL → DB 연결 → 8개 테이블 → 7개 시드 → 최근 데이터
- **DB 테이블 8개**: asset_master, price_daily, factor_daily, signal_daily, backtest_run, backtest_equity_curve, backtest_trade_log, job_run
- **배포 인프라**: Railway (DB + API), Vercel (Frontend), GitHub Actions (CI/CD)
- **배포 아키텍처**:
  ```
  [Windows PC]                    [Cloud]
   ├── Task Scheduler             ├── Railway PostgreSQL (DB)
   │   └── daily_collect.bat      ├── Railway App (FastAPI API)
   │       ├── collect.py         │   └── /v1/* endpoints
   │       ├── healthcheck.py     └── Vercel (React SPA)
   │       └── run_research.py        └── → Railway API
   └── 로컬 개발 환경
  ```
- Git remote: `https://github.com/bluecalif/stock-dashboard.git`
- dev-docs: `dev/active/phase6-deploy/` (plan, tasks, context, debug-history)
- **CORS 현재 설정** (`api/main.py`): localhost:5173/5174만 허용 → Railway 배포 시 Vercel 도메인 추가 필요
- **settings.py**: `database_url`, `fdr_timeout`, `log_level`, `alert_webhook_url` 등 Pydantic BaseSettings

## Next Action
1. **Step 6.1 + 6.4**: `daily_collect.bat` 수정 (research 추가 + 로그 로테이션)
2. **Step 6.2**: pytest 전체 실행 & 실패 수정
3. **Step 6.3**: `preflight.py` 생성
4. **Step 6.7**: GitHub Actions CI 파이프라인 생성
5. **Step 6.8**: Railway 백엔드 배포
6. **Step 6.9**: Vercel 프론트엔드 배포
7. **Step 6.5**: `runbook.md` 생성 (배포 절차 포함)
8. **Step 6.6**: 전체 커밋

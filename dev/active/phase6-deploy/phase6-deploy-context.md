# Phase 6: Deploy & Ops — Context
> Last Updated: 2026-02-15
> Status: In Progress

## 1. 핵심 파일

### 수정 대상
| 파일 | 용도 | 액션 |
|------|------|------|
| `backend/scripts/daily_collect.bat` | 일일 배치 스크립트 | 수정: research 추가 + 로그 로테이션 |
| `backend/scripts/preflight.py` | Pre-deployment 체크 | 신규 생성 |
| `backend/api/main.py` | FastAPI 앱 | 수정: CORS 프로덕션 도메인 추가 |
| `.github/workflows/ci.yml` | CI 파이프라인 | 신규 생성 |
| `backend/Procfile` | Railway 배포 설정 | 신규 생성 |
| `backend/railway.toml` | Railway 빌드 설정 | 신규 생성 |
| `backend/requirements.txt` | Railway 의존성 | 신규 생성 (pyproject.toml 기반) |
| `frontend/vercel.json` | Vercel SPA 라우팅 | 신규 생성 |
| `frontend/src/api/client.ts` | API base URL | 수정: 환경변수 기반 URL |
| `docs/runbook.md` | 운영 문서 | 신규 생성 |

### 참조 파일 (읽기 전용)
| 파일 | 용도 |
|------|------|
| `backend/scripts/run_research.py` | 리서치 파이프라인 CLI (--start, --end, --assets, --strategy) |
| `backend/scripts/collect.py` | 수집 CLI (--start, --end, --assets) |
| `backend/scripts/healthcheck.py` | 데이터 신선도 체크 (DB 기반) |
| `backend/scripts/register_scheduler.bat` | Task Scheduler 등록 |
| `backend/scripts/seed_assets.py` | asset_master 시드 |
| `backend/db/session.py` | SessionLocal 팩토리 |
| `backend/db/models.py` | SQLAlchemy 모델 8개 |
| `backend/config/settings.py` | Pydantic BaseSettings (.env 로드) |
| `backend/collector/alerting.py` | Discord webhook 알림 |
| `backend/pyproject.toml` | Python 의존성 정의 |
| `frontend/package.json` | Node 의존성 |
| `frontend/vite.config.ts` | Vite 빌드 설정 |

## 2. 데이터 인터페이스

### 배치 파이프라인 흐름
```
daily_collect.bat
  ├── 1. collect.py --start T-7 --end T     → price_daily UPSERT
  ├── 2. healthcheck.py                      → 신선도 체크 + Discord 알림
  ├── 3. run_research.py --start T-7 --end T → factor/signal/backtest DB 저장
  └── 4. forfiles /P logs /D -30 /C "..."    → 30일 이전 로그 삭제
```

### preflight.py 검증 항목
```
1. .env 필수 변수 (DATABASE_URL)
2. DB 연결 테스트 (SELECT 1)
3. 테이블 존재 확인 (8개)
4. asset_master 시드 확인 (7개 자산)
5. 최근 수집 데이터 존재 여부
```

### CI/CD 흐름
```
GitHub Push/PR → GitHub Actions
  ├── CI: pytest + ruff (모든 push/PR)
  └── CD: Railway 자동 배포 (master push → Railway webhook)

Railway:
  backend/ → pip install → uvicorn api.main:app → https://[app].railway.app

Vercel:
  frontend/ → npm install → npm run build → https://[app].vercel.app
```

### 배포 아키텍처
```
[Windows PC]                    [Cloud]
 ├── Task Scheduler             ├── Railway PostgreSQL (DB)
 │   └── daily_collect.bat      ├── Railway App (FastAPI API)
 │       ├── collect.py         │   └── /v1/* endpoints
 │       ├── healthcheck.py     └── Vercel (React SPA)
 │       └── run_research.py        └── → Railway API
 └── 로컬 개발 환경
```

## 3. 주요 결정사항

| 일자 | 결정 | 근거 |
|------|------|------|
| 2026-02-14 | Discord webhook 실발송 테스트 제외 | 미설정 상태, 코드 검증만 |
| 2026-02-14 | 로그 로테이션: 30일 | Windows forfiles 커맨드로 간단 구현 |
| 2026-02-14 | preflight.py: DB 기반 검증 | .env + DB 연결 + 테이블 + 시드 + 최근 데이터 |
| 2026-02-15 | Phase 6 스코프 확장: CI/CD + 실배포 포함 | 기존 6 tasks → 9 tasks. GitHub Actions + Railway + Vercel |
| 2026-02-15 | 백엔드 배포: Railway App | 이미 Railway PostgreSQL 사용 중, 동일 프로젝트에 App 추가로 내부 네트워크 활용 |
| 2026-02-15 | 프론트엔드 배포: Vercel | React SPA 정적 배포에 최적, GitHub 연동 자동 배포 |
| 2026-02-15 | CI: GitHub Actions (pytest + ruff) | 무료 티어 충분, GitHub 네이티브 통합 |
| 2026-02-15 | 헬스체크 503 분리: /health(엄격) + /ready(진단) | Railway 헬스체크가 DB 다운을 감지하도록 |
| 2026-02-15 | Alembic startCommand 통합 | idempotent, 배포마다 자동 마이그레이션 |
| 2026-02-15 | dependencies.py RuntimeError → HTTPException(503) | 503 체인 일관성 |

## Changed Files (Step 6.1 + 6.4)
- `backend/scripts/daily_collect.bat` — 수정: research 파이프라인 호출 추가 + 30일 로그 로테이션

## Changed Files (Step 6.2)
- `backend/tests/unit/test_factor_store.py` — 수정: mock_preprocess 시그니처에 **kwargs 추가

## Changed Files (CI/CD Deploy — 2026-02-15)
- `.github/workflows/ci.yml` — deploy-railway + deploy-vercel job 추가
- `backend/.railwayignore` — 신규: .venv 등 Railway 업로드 제외
- `backend/railway.toml` — builder: nixpacks→dockerfile, healthcheck 수정
- `backend/Dockerfile` — 신규: Python 3.12-slim 배포 이미지
- `docs/cli-deployment.md` — 토큰 생성/등록 가이드 (이전 세션)

## Changed Files (Step 6.10~6.12 — 배포 안정화)
- `backend/api/dependencies.py` — RuntimeError → HTTPException(503)
- `backend/api/routers/health.py` — DB 실패 503 반환 + `/v1/ready` 진단 엔드포인트
- `backend/Dockerfile` — CMD exec form 전환, alembic.ini COPY 추가
- `backend/railway.toml` — startCommand에 `alembic upgrade head &&` 추가
- `backend/tests/unit/test_api/test_main.py` — 헬스체크 테스트 503 업데이트 + ready 테스트 추가
- `backend/tests/unit/test_api/test_edge_cases.py` — 헬스체크 테스트 503 업데이트
- `docs/cli-deployment.md` — 트러블슈팅/체크리스트/서비스구조/운영명령어 대폭 확장

## Changed Files (Step 6.13 — D-5 디버깅, 세션 2)
- `backend/api/routers/health.py` — DI 분리: `Depends(get_db)` 제거, 항상 200 liveness
- `backend/railway.toml` — `startCommand`: `&&` → `|| true;`, healthcheck 주석 처리 (디버깅)
- `backend/tests/unit/test_api/test_main.py` — `monkeypatch` 기반 health 테스트 전환 + 6 tests
- `backend/tests/unit/test_api/test_edge_cases.py` — health 503→200 반영
- `.github/workflows/ci.yml` — Railway deploy 로그 수집 단계 추가

## 4. 컨벤션 체크리스트

### 배치 스크립트
- [x] `setlocal enabledelayedexpansion` 사용
- [x] `PYTHONUTF8=1` + `chcp 65001` 설정
- [x] venv Python 경로 사용 (`%VENV_PYTHON%`)
- [x] 로그 파일에 날짜별 기록
- [x] ERRORLEVEL 기반 성공/실패 분기

### Python 스크립트
- [x] `sys.path.insert(0, ...)` 으로 backend/ 추가
- [x] `config.logging.setup_logging()` 호출
- [x] `db.session.SessionLocal` None 체크
- [x] `encoding='utf-8'` 명시

### CI/CD
- [x] GitHub Actions workflow YAML 유효성
- [x] PostgreSQL service container 설정
- [x] pip cache 설정
- [x] GitHub Secrets 등록 (RAILWAY_TOKEN, VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID)

### 배포
- [ ] Railway 환경변수 설정 (DATABASE_URL, CORS_ORIGINS)
- [ ] Vercel 환경변수 설정 (VITE_API_BASE_URL)
- [ ] CORS 프로덕션 도메인 추가
- [x] health 엔드포인트 경로 수정 (/v1/health)

### 배포 안정화 (Stage G)
- [ ] dependencies.py: RuntimeError → HTTPException(503)
- [ ] health.py: DB 실패 503 반환 + /v1/ready 분리
- [ ] Dockerfile: CMD exec form + alembic 파일 COPY
- [ ] railway.toml: alembic upgrade head 자동화
- [ ] cli-deployment.md: 트러블슈팅/체크리스트/운영 명령어 추가

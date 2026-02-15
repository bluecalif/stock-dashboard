# Phase 6: Deploy & Ops — Debug History
> Last Updated: 2026-02-15

## Step 6.2: 테스트 전체 실행 & 검증

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| 1 | test_factor_store | mock_preprocess에 missing_threshold kwarg 미지원 → preprocess_failed | mock 시그니처에 `**kwargs` 추가 | `tests/unit/test_factor_store.py:234` |

## CI/CD Deploy 디버깅 (2026-02-15)

### D-1: Railway deploy — "Multiple services found"
- **증상**: `railway up --ci` 실행 시 `Multiple services found. Please specify a service via the --service flag.`
- **원인**: Railway 프로젝트에 Postgres 서비스가 이미 존재하여 서비스 지정 필요
- **수정**: `railway up --ci --service stock-dashboard` → `--service` 플래그 추가
- **커밋**: `c32728d`

### D-2: Railway deploy — "Service not found"
- **증상**: `--service stock-dashboard` 지정했으나 `Service not found`
- **원인**: Railway 프로젝트에 앱 서비스가 없었음 (Postgres DB만 존재)
- **수정**: `railway add --service backend`로 빈 서비스 생성, `--service backend`로 변경
- **커밋**: `5407153`

### D-3: Railway deploy — nixpacks 빌드 실패 (로그 없음)
- **증상**: 업로드 성공 → `scheduling build on Metal builder` → `Deploy failed` (6초)
- **원인**: nixpacks 빌더가 프로젝트 인식 실패 (빌드 로그 출력 없이 즉시 실패)
- **시도**: `.railwayignore` 추가 (`.venv/`, `__pycache__/` 등 제외) → 동일 실패
- **수정**: `railway.toml`에서 `builder = "nixpacks"` → `builder = "dockerfile"` 변경, `Dockerfile` 추가
- **커밋**: `1c9c0ba` (.railwayignore)

### D-4: Railway deploy — 헬스체크 실패 (경로/타임아웃/PORT)
- **증상**: Dockerfile 빌드 성공 → 헬스체크 30초 타임아웃 → `Deploy failed`
- **원인 1**: `railway.toml`의 `healthcheckPath = "/health"` → 실제 엔드포인트는 `/v1/health`
- **원인 2**: 헬스체크 타임아웃 30초가 앱 시작에 불충분
- **원인 3**: Dockerfile CMD에 `$PORT` 환경변수 미사용 (Railway가 PORT 주입)
- **수정**: healthcheckPath → `/v1/health`, 타임아웃 → 120초, CMD에 `${PORT:-8000}` 사용
- **커밋**: `0511c8b` (Step 6.10-6.12 일괄 수정에 포함)

### D-5: Railway deploy — 헬스체크 503 (DB 미설정 + startCommand 블로킹)
> 2026-02-15 세션 2 — 5회 디버깅 시도, 다중 근본 원인 해결

**증상**: Step 6.10-6.12 push 후 Railway 배포 시 헬스체크 `service unavailable` 5회 반복 → `Deploy failed`. 2분 retry window 내 모든 시도 실패.

**분석 1: `get_db()` Depends 레벨 503**
- `api/dependencies.py`의 `get_db()`가 `SessionLocal is None`일 때 `HTTPException(503)` raise
- `/v1/health` 엔드포인트의 `try/except`에 **도달하기 전에** FastAPI DI 레벨에서 503 발생
- DATABASE_URL이 Railway에 미설정 → `SessionLocal = None` → 무조건 503

**수정 1: 헬스체크 DI 분리** (`d1fa72c`)
- `/v1/health`: `Depends(get_db)` 제거, `SessionLocal` 직접 사용, **항상 200 반환** (liveness probe)
- `/v1/ready`: 마찬가지로 DI 제거, DB 실패 시 503 (readiness probe)
- 테스트: `monkeypatch`로 `SessionLocal` mock 방식으로 전환

**문제 2: ruff lint 실패** (`8534037`)
- 미사용 import 3개: `Depends`, `Session`, `get_db`
- CI test job에서 `ruff check` 실패로 deploy job 미실행

**분석 3: `alembic upgrade head &&` 블로킹**
- `railway.toml`의 `startCommand = "alembic upgrade head && uvicorn ..."`
- DATABASE_URL 빈 문자열 → `alembic upgrade head` 크래시 (SQLAlchemy URL 파싱 실패)
- `&&` 연산자로 인해 alembic 실패 시 **uvicorn 미시작** → HTTP 연결 불가 → healthcheck 실패
- 로컬 검증: `DATABASE_URL="" alembic upgrade head` → 즉시 `ArgumentError` (hang 아님)

**수정 3: `||true;` 패턴** (`e0c5d91`)
- `startCommand = "alembic upgrade head || true; uvicorn ..."` — alembic 실패해도 uvicorn 시작

**분석 4: 여전히 "service unavailable" — CI 로그 수집 시도**
- 로컬에서 `DATABASE_URL="" uvicorn api.main:app` → 정상 시작, `/v1/health` → 200 OK 확인
- Railway 빌드 로그 직접 확인 불가 (SPA 대시보드, Railway CLI 인증 만료)
- CI workflow에 `railway logs` 단계 추가하여 런타임 로그 수집 시도
  - 1차: `railway logs --limit 50 --service backend` → `--limit` 미지원 (`e1b3745`)
  - 2차: deployment ID 캡처 + `railway logs <DEPLOY_ID>` → `No service could be found` (`aba4c26`)
  - Railway CLI가 token 기반 실행 시 서비스 자동 링크 안 됨 → `--service` flag 필요

**현재 상태**: 헬스체크 비활성화(`railway.toml` 주석 처리)하여 서비스 시작 자체를 먼저 확인하는 방향으로 전환 중. 미커밋 변경 있음.

**핵심 의문**: 로컬에서는 `/v1/health` → 200 정상 동작하나, Railway에서 계속 `service unavailable`. 가능한 원인:
1. Docker 레이어 캐시로 구 코드 사용 (빌드 19초 완료 → 캐시 의심)
2. Railway 내부 네트워킹/PORT 바인딩 문제
3. `startCommand`의 `${PORT:-8000}`에서 Railway PORT 주입 타이밍 이슈

### Vercel deploy — 성공
- **상태**: 3회 연속 성공 (deploy-vercel job)
- **구성**: `vercel pull → build → deploy --prebuilt --prod`

## Modified Files Summary
```
.github/workflows/ci.yml       — deploy-railway + deploy-vercel job 추가, 로그 수집 단계 추가
backend/.railwayignore          — 신규: .venv 등 업로드 제외
backend/railway.toml            — builder dockerfile 변경, healthcheck 수정, startCommand || true
backend/Dockerfile              — 신규: Python 3.12-slim 기반 배포 이미지, CMD exec form
backend/api/routers/health.py   — DI 분리: Depends(get_db) → SessionLocal 직접 사용, 200 liveness
backend/api/dependencies.py     — RuntimeError → HTTPException(503)
backend/tests/unit/test_api/test_main.py       — monkeypatch 기반 health 테스트로 전환
backend/tests/unit/test_api/test_edge_cases.py — health 503→200 반영
```

## Step 6.10~6.12: 배포 안정화 (근본 이슈 해결)

### 구조적 개선 사항 (코드 디버깅이 아닌 아키텍처 개선)

| # | 파일 | 변경 | 이유 |
|---|------|------|------|
| S-1 | `api/dependencies.py` | `RuntimeError` → `HTTPException(503)` | DB 미설정 시 500 대신 503으로 일관된 응답 |
| S-2 | `api/routers/health.py` | DB 실패 → 503 + `/v1/ready` 분리 | Railway 헬스체크가 DB 다운 감지 가능 |
| S-3 | `Dockerfile` | CMD exec form + `alembic.ini` COPY | 시그널 전파 + 마이그레이션 지원 |
| S-4 | `railway.toml` | `alembic upgrade head &&` startCommand | 배포마다 자동 마이그레이션 |

## Lessons Learned
1. **Railway 서비스 구분**: Railway 프로젝트에 DB만 있어도 "multiple services"로 판단됨. 앱 서비스는 별도 생성 필요 (`railway add --service [name]`)
2. **Railway Project Token vs Account Token**: Project Token은 `railway up` 전용. CLI 로그인/서비스 생성에는 Account Token 또는 브라우저 로그인 필요
3. **nixpacks 빌드 불안정**: nixpacks가 빌드 로그 없이 실패할 수 있음. Dockerfile 기반이 더 안정적
4. **Railway PORT 주입**: Railway가 `$PORT` 환경변수를 주입하므로 Dockerfile CMD에서 반드시 `${PORT:-8000}` 사용
5. **헬스체크 경로 일치**: `railway.toml`의 `healthcheckPath`와 실제 엔드포인트 경로가 정확히 일치해야 함 (prefix 포함)
6. **환경변수 = 배포의 마지막 마일**: 코드/설정이 완벽해도 DATABASE_URL, CORS_ORIGINS, VITE_API_BASE_URL 3종 미설정이면 앱 미동작
7. **헬스체크 liveness/readiness 분리**: `/health`(항상 200, liveness) + `/ready`(DB 필수, 503, readiness)로 Railway 헬스체크 통과와 운영 진단 모두 지원
8. **FastAPI DI와 헬스체크 충돌**: `Depends(get_db)`가 헬스체크 엔드포인트 자체를 503으로 만들 수 있음. 헬스체크는 DI 없이 직접 DB 접근해야 함
9. **startCommand `&&` vs `||true;`**: `&&`는 앞 명령 실패 시 뒷 명령 미실행. DB 미설정 시 `alembic upgrade head` 실패 → uvicorn 미시작. `|| true;`로 graceful 실패 허용 필수
10. **Railway CLI logs 명령 제약**: `railway logs --limit` 미지원, Token 기반 실행 시 `--service` flag 필수, deployment ID로도 서비스 지정 필요
11. **CI에서 Railway 배포 실패 원인 추적 어려움**: Railway 빌드/런타임 로그가 CI stdout에 충분히 노출되지 않음. SPA 대시보드에서만 확인 가능한 정보가 있어 디버깅 병목

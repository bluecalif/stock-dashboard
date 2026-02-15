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

**결론**: D-5에서 식별된 3가지 핵심 의문 → D-6에서 1번(캐시) + 3번(PORT 변수 확장) 확정. → **Minimum Viable Deploy 전략으로 전환**.

**핵심 의문 (D-5 시점)**:
1. ❌ Docker 레이어 캐시로 구 코드 사용 (빌드 19초 완료 → 캐시 의심) → **D-6에서 확인: 2단계 빌드로 해결**
2. ⬜ Railway 내부 네트워킹/PORT 바인딩 문제 → 해당 없음 (PORT 변수 확장 문제였음)
3. ❌ `startCommand`의 `${PORT:-8000}`에서 Railway PORT 주입 타이밍 이슈 → **D-6에서 확인: 근본 원인**

---

### D-6: Minimum Viable Deploy + 근본 원인 해결 — Railway startCommand 셸 변수 미확장
> 2026-02-15 세션 3 — D-5 핵심 의문 해소, 2커밋으로 배포 성공

**전략 전환: Minimum Viable Deploy**
- D-5에서 5회 디버깅에도 `service unavailable` 지속 → 변수 너무 많아 원인 특정 불가
- 복잡한 설정(healthcheck, alembic, 로그 수집 로직) 전부 제거 → **최소 상태에서 배포 성공 확인 후 점진 복원**

**커밋 1 (`a449fdc`): Minimum Viable Deploy — 3개 파일 동시 수정**

1. **`backend/Dockerfile` — Docker 캐시 무효화 (2단계 pip install)**
   ```dockerfile
   # 1단계: 의존성만 설치 (pyproject.toml 변경 시에만 재실행 — 캐시 활용)
   COPY pyproject.toml .
   RUN pip install --no-cache-dir .

   # 2단계: 소스 코드 복사 (항상 최신 — 캐시 무효화)
   COPY alembic.ini .
   COPY collector/ collector/
   ...
   # editable 재설치 (fast — --no-deps이므로 egg-link만 생성)
   RUN pip install --no-cache-dir -e . --no-deps
   ```
   - **Before**: `COPY pyproject.toml . → COPY 소스 → pip install -e .` (소스 변경해도 deps 캐시가 소스 포함)
   - **After**: deps 먼저 설치 → 소스 복사 → editable 재설치. 소스 변경 시 반드시 최신 코드 반영

2. **`backend/railway.toml` — healthcheck/alembic 완전 제거**
   ```toml
   [deploy]
   startCommand = "sh -c 'uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}'"
   restartPolicyType = "on_failure"
   restartPolicyMaxRetries = 3
   ```
   - `healthcheckPath`, `healthcheckTimeout` 삭제 (헬스체크 비활성화)
   - `alembic upgrade head || true;` 삭제 (DB 미설정 상태에서 불필요한 복잡성)
   - **순수 uvicorn만** 실행하여 서비스 시작 자체를 먼저 확인

3. **`.github/workflows/ci.yml` — Railway 로그 수집 단순화**
   ```yaml
   - name: Show Railway deploy logs
     run: |
       sleep 10
       railway logs --service backend 2>&1 || echo "Could not fetch logs"
   ```
   - D-5에서의 deployment ID 캡처 로직 제거 (불안정)
   - `--service backend` 플래그 추가 (Railway CLI token 기반 실행 시 필수)
   - `sleep 10`으로 로그 생성 대기

**CI 실행 결과**: 빌드 성공 + 런타임 로그 드디어 확보!

**런타임 로그에서 발견된 에러**:
```
ERROR:    Error loading ASGI app. Could not import module "api.main".
...실은 아닌...
'${PORT:-8000}' is not a valid integer
```

**근본 원인 확정**:
- Railway의 `startCommand`는 **셸 없이 리터럴로 명령 실행**
- `uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}` → `${PORT:-8000}`이 문자열 그대로 전달
- uvicorn이 `'${PORT:-8000}'`을 정수로 파싱 시도 → `not a valid integer` → 즉시 크래시
- D-4에서 Dockerfile CMD에 `sh -c`로 감싼 건 맞았지만, `railway.toml`의 `startCommand`가 CMD를 **덮어씀**
- startCommand에도 `sh -c`가 필요했으나 D-5까지 이 사실을 몰랐음

**커밋 2 (`8e97c72`): startCommand sh -c 래핑**
```toml
# Before (D-5까지):
startCommand = "alembic upgrade head || true; uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"

# After:
startCommand = "sh -c 'uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}'"
```

**배포 성공 확인** (Railway 런타임 로그):
```
INFO:     Started server process [2]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:7276 (Press CTRL+C to quit)
```
- PORT=7276 (Railway 주입) 정상 바인딩 확인
- `/v1/health` 응답 확인 가능 상태

**D-6 핵심 인사이트: startCommand vs Dockerfile CMD**
| 항목 | Dockerfile CMD | railway.toml startCommand |
|------|---------------|--------------------------|
| 셸 확장 | `sh -c` 명시하면 동작 | **셸 없이 리터럴 실행** — `sh -c` 필수 |
| 우선순위 | 기본 | **startCommand가 CMD를 덮어씀** |
| 변수 확장 | `["sh", "-c", "..."]` exec form에서 가능 | 반드시 `sh -c '...'`로 래핑 |

---

### D-7: 점진 복원 — healthcheck + alembic 재활성화
> 2026-02-15 세션 3 — D-6 배포 성공 확인 후 점진 복원

**변경**: `railway.toml`에 D-6에서 제거했던 설정 재활성화
```toml
startCommand = "sh -c 'alembic upgrade head || true; uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}'"
healthcheckPath = "/v1/health"
healthcheckTimeout = 120
```

**결과**: CI 성공, Railway 배포 성공, healthcheck `/v1/health` → 200 OK 통과
- alembic은 `Could not parse SQLAlchemy URL` 에러 → `|| true`로 graceful 실패 → uvicorn 정상 시작
- alembic 실패 원인은 D-8에서 분석

**커밋**: `2db9684`

---

### D-8: postgres:// 스키마 호환성 — SQLAlchemy 2.x는 postgresql:// 필수
> 2026-02-15 세션 3 — alembic URL 파싱 실패 근본 원인 해결

**증상**: D-7 배포 성공했으나 alembic이 `Could not parse SQLAlchemy URL from given URL string` 에러 지속. `/v1/health` → `{"db":"not_configured"}` — DB 미연결.

**분석**:
- Railway Postgres는 `DATABASE_URL`을 `postgres://` 스키마로 제공
- SQLAlchemy 2.x는 `postgres://` 스키마를 지원하지 않음 (deprecated) → `postgresql://` 필수
- `db/session.py`와 `db/alembic/env.py` 모두 URL을 그대로 사용 → 파싱 실패

**수정**: 두 파일에 자동 변환 로직 추가
```python
_url = settings.database_url
if _url.startswith("postgres://"):
    _url = _url.replace("postgres://", "postgresql://", 1)
```

**커밋**: `6fd0a4a`

---

### D-9: Railway 변수 참조 미해석 — `${{Postgres.DATABASE_URL}}` 실패
> 2026-02-15 세션 3 — 환경변수 설정 최종 해결

**증상**: D-8 코드 수정 배포 후에도 `/v1/health` → `{"db":"not_configured"}`. DATABASE_URL이 컨테이너에 빈 문자열로 전달됨.

**분석**:
- backend 서비스에 `DATABASE_URL = ${{Postgres.DATABASE_URL}}`로 설정
- Railway 변수 참조 `${{ServiceName.VAR}}`에서 서비스 이름이 정확히 일치해야 함
- Postgres 서비스의 실제 이름이 참조에 쓴 이름과 불일치 → 참조가 빈 문자열로 resolve

**수정**: 참조 대신 **실제 URL 직접 입력**
```
postgresql://postgres:***@postgres.railway.internal:5432/railway
```
- Railway 대시보드 → backend 서비스 → Variables → DATABASE_URL 값 직접 교체
- 환경변수 변경 후 수동 Redeploy 클릭 (자동 재배포 트리거 안 됨)

**결과**:
```
/v1/health → {"status":"ok","db":"connected"} ✅
/v1/ready  → {"status":"ok","db":"connected"} ✅
/v1/prices/daily?asset_id=KS200 → OHLCV 데이터 반환 ✅
/v1/factors?symbol=KS200 → 팩터 데이터 반환 ✅
/v1/signals?symbol=KS200 → 시그널 데이터 반환 ✅
```

**현재 상태**: 백엔드 API 완전 동작. 남은 작업: CORS_ORIGINS, Vercel VITE_API_BASE_URL, E2E 검증.

### Vercel deploy — 성공
- **상태**: 연속 성공 (deploy-vercel job)
- **구성**: `vercel pull → build → deploy --prebuilt --prod`

## Modified Files Summary
```
.github/workflows/ci.yml       — deploy-railway + deploy-vercel job 추가, 로그 수집 단계 추가/단순화
backend/.railwayignore          — 신규: .venv 등 업로드 제외
backend/railway.toml            — builder dockerfile, healthcheck 수정→제거, startCommand sh -c 래핑
backend/Dockerfile              — 신규: Python 3.12-slim, 2단계 pip install (캐시 무효화)
backend/api/routers/health.py   — DI 분리: Depends(get_db) → SessionLocal 직접 사용, 200 liveness
backend/api/dependencies.py     — RuntimeError → HTTPException(503)
backend/db/session.py           — postgres:// → postgresql:// 자동 변환
backend/db/alembic/env.py       — postgres:// → postgresql:// 자동 변환
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
12. **Railway startCommand는 셸 없이 실행**: `${PORT:-8000}` 같은 셸 변수 확장이 안 됨. 반드시 `sh -c '...'`로 래핑 필수. Dockerfile CMD에 `sh -c`가 있어도 startCommand가 CMD를 덮어쓰므로 startCommand 자체에 `sh -c` 필요
13. **Minimum Viable Deploy 전략**: 디버깅 변수가 많을 때 모든 복잡성 제거 → 최소 상태로 배포 성공 확인 → 점진 복원이 가장 효과적. 5회 실패 후 이 전략으로 1회 만에 근본 원인 특정
14. **Docker 2단계 빌드로 캐시 무효화**: `COPY pyproject.toml → pip install` (deps 캐시) → `COPY 소스 → pip install -e . --no-deps` (항상 최신). 소스 변경 시 deps 재설치 없이 빠른 빌드 + 최신 코드 보장
15. **startCommand vs Dockerfile CMD 우선순위**: `railway.toml`의 `startCommand`가 존재하면 Dockerfile CMD를 완전히 무시. 두 곳 모두 설정 시 혼란 발생 → startCommand에 통일 권장
16. **Railway Postgres `postgres://` 스키마**: Railway Postgres는 `postgres://` 스키마 URL을 제공하나, SQLAlchemy 2.x는 `postgresql://`만 지원. 앱 코드에서 자동 변환 필수
17. **Railway 변수 참조 `${{ServiceName.VAR}}`**: 서비스 이름이 정확히 일치해야 함. 대소문자 또는 이름 불일치 시 빈 문자열로 resolve됨. 디버깅 어려움 → 초기에는 직접 URL 입력이 안전
18. **Railway 환경변수 변경 시 자동 재배포 안 될 수 있음**: 변수 변경 후 Deployments 탭에서 수동 Redeploy 필요한 경우 있음

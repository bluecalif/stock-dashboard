# Phase 6: Deploy & Ops — Debug History
> Last Updated: 2026-02-14

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

### D-4: Railway deploy — 헬스체크 실패
- **증상**: Dockerfile 빌드 성공 → 헬스체크 30초 타임아웃 → `Deploy failed`
- **원인 1**: `railway.toml`의 `healthcheckPath = "/health"` → 실제 엔드포인트는 `/v1/health`
- **원인 2**: 헬스체크 타임아웃 30초가 앱 시작에 불충분
- **원인 3**: Dockerfile CMD에 `$PORT` 환경변수 미사용 (Railway가 PORT 주입)
- **수정**: healthcheckPath → `/v1/health`, 타임아웃 → 120초, CMD에 `${PORT:-8000}` 사용
- **상태**: 수정 완료, CI push 전 (다음 배포에서 확인 예정)

### Vercel deploy — 성공
- **상태**: 3회 연속 성공 (deploy-vercel job)
- **구성**: `vercel pull → build → deploy --prebuilt --prod`

## Modified Files Summary
```
.github/workflows/ci.yml       — deploy-railway + deploy-vercel job 추가
backend/.railwayignore          — 신규: .venv 등 업로드 제외
backend/railway.toml            — builder dockerfile 변경, healthcheck 수정
backend/Dockerfile              — 신규: Python 3.12-slim 기반 배포 이미지
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
7. **헬스체크 503 분리**: `/health`(엄격, 503) + `/ready`(진단, 200) 2트랙으로 Railway 헬스체크와 운영 진단 모두 지원

# CLI 배포 가이드 — Railway / Vercel

> Last Updated: 2026-02-15

CI/CD 환경(GitHub Actions)에서 CLI로 배포하는 방법. 권한 거부(401/403) 방지 + 트러블슈팅 + 운영 명령어 포함.

---

## 배포 전 필수 환경변수 체크리스트

배포가 "성공"해도 이 환경변수들이 없으면 앱이 **실제로 동작하지 않습니다**.

### GitHub Secrets (CI/CD 파이프라인용, 4개)
- [ ] `RAILWAY_TOKEN` — Railway Project Token (배포용)
- [ ] `VERCEL_TOKEN` — Vercel API Token
- [ ] `VERCEL_ORG_ID` — Vercel 팀/조직 ID
- [ ] `VERCEL_PROJECT_ID` — Vercel 프로젝트 ID

### Railway 환경변수 (대시보드 → backend 서비스 → Variables)
- [ ] `DATABASE_URL` — PostgreSQL 내부 URL (`postgresql://...railway.internal/...`)
- [ ] `CORS_ORIGINS` — Vercel 배포 URL (예: `https://stock-dashboard-xxx.vercel.app`)

### Vercel 환경변수 (대시보드 → Project → Settings → Environment Variables)
- [ ] `VITE_API_BASE_URL` — Railway 공개 URL (예: `https://backend-production-xxx.up.railway.app`)

> **중요**: Vercel의 `VITE_` 접두사 환경변수는 **빌드 시** 번들에 포함됩니다. 등록/변경 후 반드시 **재배포** 필요.

---

## 공통 원칙 5가지 (권한 거부를 거의 다 막음)

1. **CI에서는 절대 `login`(브라우저/대화형) 의존 금지**
   → 토큰을 **GitHub Secrets**로 넣고, 워크플로에서 환경변수로 주입. ([GitHub Docs][1])

2. **토큰 “타입”을 작업 목적에 맞게 선택**

* Railway:

  * 배포/로그/리디플로이(프로젝트 단위) = **Project Token → `RAILWAY_TOKEN`** ([Railway Docs][2])
  * 계정/워크스페이스 API 작업 = **Account/Workspace Token → `RAILWAY_API_TOKEN`** ([Railway Docs][3])

3. **스코프(대상 프로젝트/환경)를 “명시적으로 고정”**
   → “다른 팀/프로젝트로 인식”이 403의 1순위 원인.

4. **모든 커맨드에서 “비대화형 옵션” 사용**

* Railway: `--ci` ([Railway Docs][2])
* Vercel: `--yes`, `--token=...` ([Vercel][4])

5. **토큰 노출 시 즉시 폐기/재발급 + Secrets 교체**
   (토큰은 한 번 유출되면 끝입니다.) ([GitHub Docs][1])

---

## Railway: CI 배포 표준 (핵심만)

### 1) 무엇을 Secrets로 넣나

* `RAILWAY_TOKEN` (✅ **Project Token**: “배포용”, 특정 환경에 스코프) ([Railway Docs][2])
* (선택) `RAILWAY_PROJECT_ID`, `RAILWAY_ENVIRONMENT` : 프로젝트/환경을 더 확실히 고정하고 싶을 때

> Railway 문서가 “자동 배포에는 interactive login 대신 **Project Token**을 쓰라”고 명시합니다. ([Railway Docs][2])
> 그리고 CLI 토큰 매핑도 공식으로 정리돼 있어요: Project Token= `RAILWAY_TOKEN`, Account/Workspace Token= `RAILWAY_API_TOKEN`. ([Railway Docs][3])

### 2) GitHub Actions 예시 (Railway)

`.github/workflows/railway-deploy.yml`

```yaml
name: Deploy to Railway (CI)

on:
  push:
    branches: ["main"]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install Railway CLI
        run: npm i -g @railway/cli

      - name: Deploy
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
          # 선택: 아래 두 개는 "대상 고정"을 더 강하게 하고 싶을 때만
          # RAILWAY_PROJECT_ID: ${{ secrets.RAILWAY_PROJECT_ID }}
          # RAILWAY_ENVIRONMENT: ${{ secrets.RAILWAY_ENVIRONMENT }}
        run: |
          railway up --ci
          # 더 강하게 고정하려면(지원되는 경우):
          # railway up --ci --project "$RAILWAY_PROJECT_ID" --environment "$RAILWAY_ENVIRONMENT"
```

### 3) Railway 401/403 방지 체크

* CI에서 `railway login`을 호출하지 말 것 (토큰 있으면 CLI가 로그인 프롬프트 대신 토큰 사용) ([Railway Docs][5])
* 배포 목적이면 **Project Token**을 써야 함 ([Railway Docs][2])
* “Project Token Not Found”류 에러는 보통 **프로젝트 토큰/Secret 이름 불일치** ([Railway Help Station][6])

> 참고: PR 환경 같은 특수 케이스는 Account(유저) 토큰이 필요하다는 논의도 있어요. ([Railway Help Station][7])
> (즉, “배포만”이면 Project Token이 정석, “PR 환경/계정 레벨 작업”이면 API 토큰이 필요할 수 있음)

---

## Vercel: CI 배포 표준 (핵심만)

### 1) 무엇을 Secrets로 넣나 (정석 3종 세트)

* `VERCEL_TOKEN`
* `VERCEL_ORG_ID`
* `VERCEL_PROJECT_ID` ([Vercel][4])

Vercel이 “커스텀 워크플로”에서 위 3개를 환경변수로 두고 CLI를 쓰는 방식을 공식으로 안내합니다. ([Vercel][4])

### 2) CI에서 추천되는 커맨드 흐름 (Preview/Prod 공통)

* `vercel pull --yes ... --token=$VERCEL_TOKEN`
* `vercel build ... --token=$VERCEL_TOKEN`
* `vercel deploy --prebuilt ... --token=$VERCEL_TOKEN` ([Vercel][4])

또한 프로덕션 배포는 `--prod`로 만들 수 있습니다. ([Vercel][8])

### 3) GitHub Actions 예시 (Vercel: PR=Preview, main=Prod)

`.github/workflows/vercel-deploy.yml`

```yaml
name: Deploy to Vercel (CI)

on:
  pull_request:
  push:
    branches: ["main"]

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}
      VERCEL_ORG_ID: ${{ secrets.VERCEL_ORG_ID }}
      VERCEL_PROJECT_ID: ${{ secrets.VERCEL_PROJECT_ID }}

    steps:
      - uses: actions/checkout@v4

      - name: Install Vercel CLI
        run: npm i -g vercel@latest

      # PR -> Preview
      - name: Preview Deploy
        if: github.event_name == 'pull_request'
        run: |
          vercel pull --yes --environment=preview --token="$VERCEL_TOKEN"
          vercel build --token="$VERCEL_TOKEN"
          vercel deploy --prebuilt --token="$VERCEL_TOKEN"

      # main -> Production
      - name: Production Deploy
        if: github.event_name == 'push'
        run: |
          vercel pull --yes --environment=production --token="$VERCEL_TOKEN"
          vercel build --prod --token="$VERCEL_TOKEN"
          vercel deploy --prebuilt --prod --token="$VERCEL_TOKEN"
```

### 4) Vercel 401/403 방지 체크

* 모든 명령에 `--token="$VERCEL_TOKEN"`을 붙여 “대화형 로그인” 제거 ([Vercel][4])
* `VERCEL_ORG_ID / VERCEL_PROJECT_ID`가 틀리면 팀/프로젝트 스코프가 어긋나서 403이 나기 쉬움 (그래서 3종 세트를 고정) ([Vercel][4])

---

## GitHub Secrets: 토큰 생성부터 등록까지 (Step-by-step)

총 4개의 Secret을 GitHub에 등록해야 합니다. 아래 순서대로 하나씩 진행하세요.

### 등록해야 할 Secrets 요약

| Secret Name | 용도 | 생성 위치 |
|-------------|------|----------|
| `RAILWAY_TOKEN` | 백엔드(FastAPI) 배포 | Railway 대시보드 |
| `VERCEL_TOKEN` | 프론트엔드(React) 배포 | Vercel 대시보드 |
| `VERCEL_ORG_ID` | Vercel 팀/조직 스코프 고정 | 로컬 `vercel link` 결과 |
| `VERCEL_PROJECT_ID` | Vercel 프로젝트 스코프 고정 | 로컬 `vercel link` 결과 |

---

### Step 1: Railway Project Token 생성

Railway에서 CI 배포에 사용할 **Project Token**을 만듭니다.

1. https://railway.com/dashboard 에 로그인
2. 배포할 **프로젝트**(stock-dashboard)를 클릭
3. 상단 **Settings** 탭 클릭
4. 왼쪽 메뉴에서 **Tokens** 선택
5. **"Create Project Token"** 클릭
6. Environment를 **production**으로 선택
7. 생성된 토큰을 복사 (이 화면을 떠나면 다시 볼 수 없음!)

> Project Token은 해당 프로젝트의 특정 환경에만 스코프되므로 안전합니다.
> Account Token(`RAILWAY_API_TOKEN`)은 계정 전체 권한이므로 배포에는 사용하지 마세요.

---

### Step 2: Vercel Token 생성

Vercel에서 CI 배포에 사용할 **API Token**을 만듭니다.

1. https://vercel.com/account/tokens 접속 (로그인 필요)
2. **"Create"** 클릭
3. Token 이름 입력 (예: `stock-dashboard-ci`)
4. Scope: **Full Account** 선택 (또는 해당 팀만)
5. Expiration: 필요에 맞게 선택 (No Expiration 추천)
6. **"Create Token"** 클릭
7. 생성된 토큰을 복사 (이 화면을 떠나면 다시 볼 수 없음!)

---

### Step 3: Vercel ORG_ID / PROJECT_ID 확인

이 두 값은 `vercel link`를 실행하면 자동 생성됩니다.

```bash
# 프로젝트 루트에서 실행 (최초 1회)
vercel link --scope <your-team-name>
```

성공하면 `.vercel/project.json` 파일이 생성됩니다:

```json
{
  "projectId": "prj_xxxxxxxxxxxx",   ← VERCEL_PROJECT_ID
  "orgId": "team_xxxxxxxxxxxx",      ← VERCEL_ORG_ID
  "projectName": "stock-dashboard"
}
```

> **참고**: `vercel link` 중 "Connect GitHub repository?" 질문에서
> 에러가 나더라도 무시해도 됩니다. CI/CD 배포에는 영향 없습니다.
> (GitHub 연결은 Vercel 대시보드 → Settings → Git에서 별도로 가능)

이미 `vercel link`를 완료했다면 `.vercel/project.json`에서 값을 확인하세요.

---

### Step 4: GitHub Secrets에 등록

위에서 만든 4개의 값을 GitHub 레포에 등록합니다.

**방법 A: gh CLI (추천 — 터미널에서 바로)**

```bash
# 각 명령 실행 후 프롬프트에 값을 붙여넣고 Enter
gh secret set RAILWAY_TOKEN
gh secret set VERCEL_TOKEN
gh secret set VERCEL_ORG_ID
gh secret set VERCEL_PROJECT_ID
```

**방법 B: GitHub 웹 UI**

1. https://github.com/bluecalif/stock-dashboard/settings/secrets/actions 접속
2. **"New repository secret"** 클릭
3. Name에 Secret 이름, Secret에 값 입력 → **"Add secret"**
4. 4개 모두 반복

---

### 등록 확인

```bash
gh secret list
```

4개가 모두 보이면 완료입니다. 워크플로에서는 `${{ secrets.NAME }}` 형태로 참조합니다. ([GitHub Docs][1])

---

## 본 프로젝트 적용: 통합 CI/CD 워크플로

본 프로젝트는 모노레포(`backend/` + `frontend/`) 구조이므로, 기존 `ci.yml`에 deploy job을 추가하는 통합 방식을 사용합니다.

- **Railway**: `backend/` 디렉토리만 배포 (FastAPI API)
- **Vercel**: `frontend/` 디렉토리만 배포 (React SPA, 루트 `vercel.json` 사용)
- **트리거**: `push` to `master` → test 통과 후 → Railway/Vercel 병렬 배포
- **PR**: lint+test만 실행, 배포 스킵

```yaml
# ci.yml 구조 (개념)
jobs:
  test:              # 기존 lint + pytest
  deploy-railway:    # needs: test, master push만
    env: RAILWAY_TOKEN
    run: railway up --ci
  deploy-vercel:     # needs: test, master push만
    env: VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID
    run: vercel pull → build → deploy --prebuilt --prod
```

---

## (중요) Railway 토큰 형식 참고

* Railway 공식 문서 기준: **CI 배포는 Project Token을 `RAILWAY_TOKEN`으로** 쓰는 것이 정석. CLI는 **토큰이 환경변수에 설정돼 있으면 `railway login` 없이 자동 사용**. ([Railway Docs][2])
* Project Token은 Railway 대시보드에서 프로젝트 단위로 생성하며, 특정 환경(production 등)에 스코프됨.
* Account/Workspace Token(`RAILWAY_API_TOKEN`)은 계정 레벨 작업(PR 환경 생성 등)에만 필요하며, 일반 배포에는 불필요. ([Railway Docs][3])

---

## Railway 서비스 구조 & 내부 네트워크

### 서비스 구성

Railway 프로젝트 `stock-dashboard` 내에 두 서비스가 존재:

| 서비스명 | 유형 | 용도 |
|----------|------|------|
| `backend` | App (Dockerfile) | FastAPI API 서버 |
| `Postgres` | Database | PostgreSQL (Railway 제공) |

### DB URL: 내부 vs 공개

| 구분 | 형식 | 사용 위치 |
|------|------|----------|
| 내부 URL | `postgresql://...railway.internal/...` | Railway 앱 내부 (**추천**) |
| 공개 URL | `postgresql://...proxy.rlwy.net/...` | 외부 접속 (로컬 개발용) |

- Railway 서비스 간에는 **내부 URL** 사용 → 레이턴시 낮음, 비용 절감
- 내부 URL: Postgres 서비스 → Variables 탭 → `DATABASE_PRIVATE_URL`
- **backend 서비스의 `DATABASE_URL`에 내부 URL을 넣어야 함**

### Dockerfile vs nixpacks

| 기준 | Dockerfile | nixpacks (기본) |
|------|-----------|----------------|
| 빌드 제어 | 완전 제어 | Railway 자동 감지 |
| 디버깅 | 로컬 `docker build`로 재현 가능 | Railway 빌드 로그만 의존 |
| Python 버전 고정 | `FROM python:3.12-slim`으로 명시 | 감지 실패 가능성 |
| monorepo 호환성 | 명시적 COPY로 안전 | 프로젝트 루트 오인식 가능 |

> **본 프로젝트 결정**: D-3에서 nixpacks 빌드 실패 (로그 없이 즉시 실패) → Dockerfile 전환.
> monorepo(`backend/` 서브디렉토리) 구조에서 nixpacks가 `pyproject.toml` 위치를 오인식하는 것이 원인.

---

## 배포 후 체크리스트

배포 성공 후 반드시 확인해야 할 항목:

### 1. 헬스체크

```bash
# Railway 백엔드 헬스체크
curl -sf https://<railway-url>/v1/health | python -m json.tool

# 기대 응답: {"status": "ok", "db": "connected"}
# DB 미연결 시: 503 {"status": "error", "db": "disconnected"}
```

### 2. CORS preflight 확인

```bash
curl -H "Origin: https://<vercel-url>" \
     -H "Access-Control-Request-Method: GET" \
     -X OPTIONS \
     https://<railway-url>/v1/health -v 2>&1 | grep -i "access-control"

# access-control-allow-origin: https://<vercel-url> 가 보여야 함
```

### 3. 프론트엔드 API URL 확인

- 브라우저에서 Vercel 앱 접속
- 개발자 도구 → Network 탭
- API 요청 URL이 `http://localhost:8000`이 아닌 Railway URL인지 확인
- localhost로 요청하고 있으면 → Vercel `VITE_API_BASE_URL` 미설정 → 등록 후 재배포

### 4. 데이터 조회 확인

```bash
# 자산 목록 조회
curl -sf https://<railway-url>/v1/assets | python -m json.tool

# 가격 데이터 조회
curl -sf "https://<railway-url>/v1/prices?asset_id=KS200&limit=5" | python -m json.tool
```

---

## 트러블슈팅 가이드

실제 배포 과정에서 겪은 D-1~D-4 이슈를 패턴별로 분류.

### 패턴 1: 빌드 실패

**증상**: GitHub Actions `deploy-railway` job 빨간불, "Build failed" 또는 "Deploy failed" (수초 만에)

**D-3 사례**: nixpacks가 `backend/pyproject.toml`을 찾지 못해 빌드 로그 없이 즉시 실패

**체크리스트**:
1. Railway 대시보드 → 해당 배포 → Build Logs 확인
2. nixpacks 오류 → `railway.toml`에 `builder = "dockerfile"` 추가
3. Dockerfile 오류 → 로컬에서 `docker build -f backend/Dockerfile backend/` 재현
4. `.railwayignore`에 `.venv/`, `__pycache__/` 등 제외 확인

### 패턴 2: 헬스체크 실패

**증상**: 빌드 성공 후 배포 실패, "Health check failed" 또는 서비스 재시작 루프

**D-4 사례**:
- `healthcheckPath` 미설정 → Railway가 기본 경로(`/`) 체크 → 404
- `healthcheckTimeout` 부족 → 앱 기동 전 타임아웃
- CMD에서 `PORT` 환경변수 미사용 → 포트 불일치

**체크리스트**:
1. `railway.toml`에 `healthcheckPath = "/v1/health"` 명시 확인
2. `healthcheckTimeout = 120` 이상 설정
3. Dockerfile CMD가 `${PORT:-8000}` 환경변수를 올바르게 사용하는지 확인
4. Railway 대시보드 → Deploy Logs에서 실제 기동 포트 확인

### 패턴 3: 권한/토큰 오류

**증상**: `401 Unauthorized`, `403 Forbidden`, "Project Token Not Found"

**D-1 사례**: `railway up --ci` (--service 플래그 누락) → 잘못된 서비스로 배포 시도

**D-2 사례**: `--service stock-dashboard` 지정 → 서비스 미존재

**체크리스트**:
1. `ci.yml`에 `railway up --ci --service backend` 형식으로 `--service` 명시
2. `RAILWAY_TOKEN`이 **Project Token**인지 확인 (Account Token 아님)
3. `gh secret list`로 Secrets 등록 여부 확인
4. Railway 대시보드에서 Token 만료 여부 확인
5. 서비스명이 Railway 대시보드의 실제 서비스명과 일치하는지 확인

### 패턴 4: 환경변수 누락

**증상**: 앱 기동 성공하나 API 호출 시 연결 실패, CORS 오류, localhost 호출

**CORS 오류**:
- 브라우저 콘솔: `Access to XMLHttpRequest ... has been blocked by CORS policy`
- 원인: Railway `CORS_ORIGINS`에 Vercel URL 미등록
- 해결: Railway 대시보드 → backend 서비스 → Variables → `CORS_ORIGINS=https://<vercel-url>`

**localhost 호출**:
- 브라우저 Network 탭에서 `http://localhost:8000/...` 요청 확인
- 원인: Vercel `VITE_API_BASE_URL` 미설정
- 해결: Vercel 대시보드 → Settings → Environment Variables → `VITE_API_BASE_URL` 추가 후 **재배포**

**DB 연결 실패**:
- `/v1/health` 응답: 503 `{"status": "error", "db": "disconnected"}`
- 원인: Railway `DATABASE_URL` 미설정
- 해결: Postgres 서비스 Variables → `DATABASE_PRIVATE_URL` 복사 → backend Variables에 `DATABASE_URL`로 등록

### 패턴 5: 서비스 미존재

**D-2 사례**: `railway up --ci --service backend` 실행 시 서비스가 없으면 오류

**해결**: Railway 대시보드 → 프로젝트 → **"+ New"** → **"Empty Service"** → 이름을 `backend`로 설정

---

## 운영 명령어 모음

### 로그 확인

```bash
# Railway — 실시간 로그 스트림
railway logs --service backend

# Railway — 최근 배포 로그
railway logs --service backend --tail 100

# Vercel — 배포 목록
vercel ls --token="$VERCEL_TOKEN"

# Vercel — 특정 배포 로그
vercel logs <deployment-url> --token="$VERCEL_TOKEN"
```

### 재배포

```bash
# Railway — 현재 코드로 재배포 (CI에서)
railway up --ci --service backend

# Railway — 대시보드에서 재배포
# backend 서비스 → Deployments → 최근 배포 → "Redeploy"

# Vercel — 프로덕션 재배포 (CI에서)
vercel pull --yes --environment=production --token="$VERCEL_TOKEN"
vercel build --prod --token="$VERCEL_TOKEN"
vercel deploy --prebuilt --prod --token="$VERCEL_TOKEN"
```

### 롤백

```bash
# Railway — 대시보드에서 롤백
# backend 서비스 → Deployments → 이전 배포 → "Rollback"

# Vercel — 이전 배포로 즉시 전환 (무중단)
vercel rollback <deployment-url-or-id> --token="$VERCEL_TOKEN"
```

### 환경변수 확인

```bash
# Railway — 서비스 환경변수 확인 (로컬에서, Account Token 필요)
railway variables --service backend

# GitHub Secrets 확인 (이름만, 값은 불가)
gh secret list
```

---

## Lessons Learned (D-1 ~ D-4)

1. **Railway 서비스 구분**: Railway 프로젝트에 DB만 있어도 "multiple services"로 판단됨 → `--service` 필수
2. **Project Token vs Account Token**: Project Token은 `railway up` 전용. 서비스 생성/계정 작업에는 Account Token 필요
3. **nixpacks 빌드 불안정**: monorepo에서 nixpacks가 빌드 로그 없이 실패 가능 → Dockerfile이 더 안정적
4. **Railway PORT 주입**: Railway가 `$PORT` 환경변수를 주입하므로 CMD에서 반드시 `${PORT:-8000}` 사용
5. **헬스체크 경로 일치**: `railway.toml`의 `healthcheckPath`와 실제 엔드포인트 경로가 정확히 일치해야 함 (prefix 포함)
6. **환경변수 = 배포의 마지막 마일**: 코드/설정이 완벽해도 환경변수 3종(DATABASE_URL, CORS_ORIGINS, VITE_API_BASE_URL) 미설정이면 앱 미동작

---

[1]: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions "Using secrets in GitHub Actions"
[2]: https://docs.railway.com/cli/deploying "Deploying with the CLI"
[3]: https://docs.railway.com/cli "CLI | Railway Docs"
[4]: https://vercel.com/kb/guide/using-vercel-cli-for-custom-workflows "How can I use the Vercel CLI for custom workflows?"
[5]: https://docs.railway.com/cli/login "railway login | Railway Docs"
[6]: https://station.railway.com/questions/error-project-token-not-found-when-dep-391b52a3 "Error: Project Token Not Found"
[7]: https://station.railway.com/questions/token-for-git-hub-action-53342720 "Token for GitHub Action"
[8]: https://vercel.com/docs/cli/deploy "vercel deploy"

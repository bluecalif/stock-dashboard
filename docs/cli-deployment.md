아래는 **“CI(Continuous Integration) 환경(= GitHub Actions 같은 자동화 파이프라인)”에서 CLI로 배포**하는 방법을 **Railway / Vercel 중심으로**, **권한 거부(401/403) 방지**에 초점을 맞춰 **깔끔하게 재정리**한 버전입니다.

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

[1]: https://docs.github.com/actions/security-guides/using-secrets-in-github-actions?utm_source=chatgpt.com "Using secrets in GitHub Actions"
[2]: https://docs.railway.com/cli/deploying?utm_source=chatgpt.com "Deploying with the CLI"
[3]: https://docs.railway.com/cli?utm_source=chatgpt.com "CLI | Railway Docs"
[4]: https://vercel.com/kb/guide/using-vercel-cli-for-custom-workflows?utm_source=chatgpt.com "How can I use the Vercel CLI for custom workflows?"
[5]: https://docs.railway.com/cli/login?utm_source=chatgpt.com "railway login | Railway Docs"
[6]: https://station.railway.com/questions/error-project-token-not-found-when-dep-391b52a3?utm_source=chatgpt.com "\"Error: Project Token Not Found When Deploying with ..."
[7]: https://station.railway.com/questions/token-for-git-hub-action-53342720?utm_source=chatgpt.com "Token for GitHub Action"
[8]: https://vercel.com/docs/cli/deploy?utm_source=chatgpt.com "vercel deploy"

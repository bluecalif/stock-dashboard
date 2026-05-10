---
name: e2e-verify
description: Stock Dashboard 백엔드 + 프론트엔드 통합 검증 스킬. 터미널(curl/Python)로 API를 테스트하고, Puppeteer 헤드리스 브라우저로 UI 스크린샷을 자동 수집해 verification/ 디렉토리에 evidence를 쌓는다. Phase dev-docs의 검증 게이트(G1.x, G2.x 등)를 "Show, don't claim" 정책으로 통과시킬 때 반드시 활성화. 키워드: verify, 검증, screenshot, 스크린샷, Puppeteer, Playwright, E2E, 게이트 통과, evidence, API test, curl test, 브라우저 테스트, headless.
---

# E2E Verify — 백엔드 + 프론트엔드 통합 검증

## 목적

Phase 게이트를 "Show, don't claim" 정책으로 통과시키기 위해:
1. **터미널**: curl / Python 스크립트로 API 응답 검증
2. **브라우저**: Puppeteer headless Chrome으로 UI 스크린샷 수집
3. **Evidence**: `verification/figures/*.png` + `verification/step-N-*.md` 자동 생성

---

## 환경 전제조건 확인

검증 시작 전 반드시 확인:

```bash
# 백엔드 (port 8000)
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/v1/health

# 프론트엔드 (port 5173)
curl -s -o /dev/null -w "%{http_code}" http://localhost:5173
```

둘 다 `200`이어야 한다. 서버가 꺼져 있으면:
- 백엔드: `cd backend && nohup uvicorn api.main:app --port 8000 > /tmp/uvicorn.log 2>&1 &`
- 프론트: `cd frontend && npm run dev &` (또는 사용자에게 직접 실행 요청)

---

## 1단계: 백엔드 API 검증 (curl)

### 기본 패턴

```bash
# GET 엔드포인트
curl -s "http://localhost:8000/v1/<path>?param=value" | python3 -m json.tool

# POST 엔드포인트
curl -s -X POST http://localhost:8000/v1/<path> \
  -H "Content-Type: application/json" \
  -d '{"field": "value"}' | python3 -m json.tool
```

### KPI 값 추출 (시뮬레이션 응답 등)

```bash
curl -s -X POST http://localhost:8000/v1/silver/simulate/replay \
  -H "Content-Type: application/json" \
  -d '{"asset_code":"QQQ","period_years":10,"monthly_amount":1000000}' \
| python3 -c "
import json,sys
d=json.load(sys.stdin)
kpi=d.get('kpi',{})
print('total_return:', kpi.get('total_return'))
print('final_asset_krw:', kpi.get('final_asset_krw'))
print('curve_points:', len(d.get('curve',[])))
"
```

### 복잡한 디버그는 Python 스크립트로

API가 500을 반환할 때는 라우터가 에러 메시지를 숨기므로, Python으로 엔진 함수를 직접 호출해 스택트레이스를 확인한다:

```python
# backend/debug_<issue>.py (검증 후 삭제)
import sys
sys.path.insert(0, '.')
from db.session import SessionLocal
from research_engine.simulation.replay import replay
import traceback

db = SessionLocal()
try:
    curve, kpi = replay('ASSET_CODE', 300000, 10, db)
    print('SUCCESS:', kpi)
except Exception as e:
    traceback.print_exc()
finally:
    db.close()
```

```bash
cd backend && python debug_<issue>.py
```

### 흔한 백엔드 버그 패턴

| 증상 | 원인 | 수정 |
|------|------|------|
| 500 + "Internal server error" | JSON에 `NaN` 직렬화 실패 | 가격 series에 `.dropna()` 추가 |
| 422 + "Field required" | 요청 필드명 불일치 | Pydantic 스키마와 프론트 요청 필드명 대조 |
| 500 + ValueError | asset_id DB 불일치 | `asset_master` 실제 키 확인 |
| KPI 전부 `nan` | 가격 데이터에 NaN 포함 | FDR 한국 자산은 공휴일 NaN 행 생성 → `.dropna()` 필수 |

---

## 2단계: 프론트엔드 브라우저 검증 (Puppeteer)

### 초기 셋업 (프로젝트당 1회)

```bash
mkdir -p /tmp/pw_test && cd /tmp/pw_test
npm init -y
npm install puppeteer-core
```

Windows Chrome 경로: `C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe`

### 표준 검증 스크립트 템플릿

```javascript
// /tmp/pw_test/verify-<step>.cjs
const puppeteer = require("puppeteer-core");
const path = require("path");
const fs = require("fs");

const CHROME_PATH = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe";
const FRONTEND_URL = "http://localhost:5173";
const BACKEND_URL  = "http://localhost:8000";
const FIGURES_DIR  = path.resolve(
  "C:/Users/User/Projects-2026/active/stock-dashboard/dev/active/<phase>/verification/figures"
);
fs.mkdirSync(FIGURES_DIR, { recursive: true });

function log(msg) { console.log(`[${new Date().toISOString().slice(11,19)}] ${msg}`); }
async function delay(ms) { return new Promise(r => setTimeout(r, ms)); }
async function shot(page, filename) {
  await page.screenshot({ path: path.join(FIGURES_DIR, filename), fullPage: false });
  log(`📸 ${filename}`);
}

// ── 온보딩 모달 사전 제거 ────────────────────────────────────────────────────
// IceBreakingModal은 profile.onboarding_completed=false 일 때 매 페이지 진입마다 표시됨.
// Escape/클릭으로는 닫히지 않으므로 API로 먼저 완료 처리 필수.
async function completeOnboarding(accessToken) {
  await fetch(`${BACKEND_URL}/v1/profile/ice-breaking`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": `Bearer ${accessToken}` },
    body: JSON.stringify({ experience_level: "intermediate", decision_style: "logic" }),
  });
}

// ── Auth: API 로그인 → localStorage 주입 ──────────────────────────────────────
async function getTokens(email, password) {
  const res = await fetch(`${BACKEND_URL}/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const j = await res.json();
  return { accessToken: j.access_token, refreshToken: j.refresh_token };
}

async function injectAuth(page, tokens) {
  await page.evaluate((t) => {
    localStorage.setItem("auth_tokens", JSON.stringify(t));
  }, tokens);
}

async function main() {
  const tokens = await getTokens("verify@silver.dev", "silver2026");
  log(`토큰 획득: ${tokens.accessToken.slice(0,20)}...`);

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: "new",
    args: [
      "--no-sandbox",
      "--disable-dev-shm-usage",
      "--disable-web-security",           // localhost CORS 우회 (테스트 전용)
      "--user-data-dir=/tmp/chrome-test-profile",
    ],
    defaultViewport: { width: 1440, height: 900 },
  });

  const consoleErrors = [];
  try {
    const page = await browser.newPage();
    page.on("console", msg => { if (msg.type() === "error") consoleErrors.push(msg.text()); });
    page.on("pageerror", err => consoleErrors.push(`PageError: ${err.message}`));

    // Auth 주입
    await page.goto(FRONTEND_URL, { waitUntil: "domcontentloaded" });
    await injectAuth(page, tokens);

    // ── 각 게이트 검증 ────────────────────────────────────────────────────────
    // G1: 라우트 접근
    await page.goto(`${FRONTEND_URL}/silver/compare`, { waitUntil: "networkidle0", timeout: 25000 }).catch(()=>{});
    await delay(2000);
    await page.keyboard.press("Escape").catch(()=>{}); // 온보딩 모달 닫기
    await delay(500);
    await shot(page, "step-1-route-desktop.png");

    // G2: 시뮬레이션 결과 대기
    log("API 응답 대기 중...");
    await page.waitForSelector(".silver-chart-card, .silver-error", { timeout: 20000 }).catch(()=>{});
    await delay(2000);
    const chartVisible = await page.$(".silver-chart-card").then(el => !!el).catch(()=>false);
    log(`차트 카드: ${chartVisible}`);
    await shot(page, "step-2-tab-a-desktop.png");

    // 탭 전환 — 로딩이 끝난 뒤 촬영 (단순 delay는 부족; waitForFunction 필수)
    // 핵심: waitForSelector(".silver-chart-card")는 이전 탭 카드를 즉시 감지해 버림
    // → loading이 없어지고 chart가 있을 때까지 폴링
    async function waitForTabResult(page) {
      await page.waitForFunction(
        () => {
          const loading = document.querySelector(".silver-loading");
          const chart   = document.querySelector(".silver-chart-card");
          const error   = document.querySelector(".silver-error");
          return !loading && (chart || error);
        },
        { timeout: 30000 }
      ).catch(() => {});
      await delay(1000);
    }

    const tabs = await page.$$('button[role="tab"]');
    if (tabs[1]) { await tabs[1].click(); await waitForTabResult(page); await shot(page, "step-2-tab-b.png"); }
    if (tabs[2]) { await tabs[2].click(); await waitForTabResult(page); await shot(page, "step-2-tab-c.png"); }

    // 모바일 뷰포트
    await page.setViewport({ width: 768, height: 900 });
    await page.reload({ waitUntil: "networkidle0", timeout: 20000 }).catch(()=>{});
    await delay(2000);
    await shot(page, "step-4-mobile-768.png");

  } finally {
    await browser.close();
  }

  if (consoleErrors.length) {
    log("브라우저 에러:");
    [...new Set(consoleErrors)].forEach(e => log(`  ${e.slice(0,120)}`));
  }
  log("=== 완료 ===");
}

main().catch(e => { console.error("ERROR:", e.message); process.exit(1); });
```

```bash
cd /tmp/pw_test && node verify-<step>.cjs
```

---

## 3단계: Evidence 문서 작성

`dev/active/<phase>/verification/step-N-<name>.md` 형식:

```markdown
## GN.M — <게이트명> (UI — 스크린샷)

**명령**: <실행한 명령>

**Raw output**:
`figures/step-N-screenshot.png` — Puppeteer headless Chrome 자동 캡처

**검증 결과**: ✅ PASS / ❌ FAIL — <근거>
```

**"Show, don't claim" 원칙**: 결과를 주장하지 말고 명령 + 실제 출력 + 스크린샷으로 증명한다.

---

## 흔한 Puppeteer 문제

| 증상 | 원인 | 해결 |
|------|------|------|
| `ERR_FAILED` CORS 에러 | localhost 간 CORS | `--disable-web-security` + `--user-data-dir` 추가 |
| 인증 리다이렉트 | localStorage 주입 시점 | `goto(FRONTEND_URL)` 후 inject → 이후 대상 URL 이동 |
| 온보딩 모달 차단 | `profile.onboarding_completed=false` → 매 페이지마다 재표시, Escape 무효 | 토큰 획득 후 `POST /v1/profile/ice-breaking` 호출로 사전 완료 처리 |
| 탭 스크린샷 전부 동일 | `waitForSelector(".silver-chart-card")`가 이전 탭 카드를 즉시 감지 | `waitForFunction`으로 loading 없어지고 chart 있을 때까지 폴링 |
| `waitForSelector` timeout | API 느림 또는 에러 | timeout 20~30초, `.catch(()=>{})` 로 timeout 무시 후 스크린샷 |

---

## 검증 계정

- **테스트 계정**: `verify@silver.dev` / `silver2026` (Railway prod DB 등록)
- **목적**: Puppeteer 세션용 전용 계정 (prod 계정 사용 금지)

---

## 전체 플로우 요약

```
1. 서버 상태 확인 (curl health check)
2. curl로 API 엔드포인트 직접 테스트 → KPI 수치 기록
3. 에러(500)이면 Python 스크립트로 엔진 직접 호출 → 스택트레이스 확인 → 버그 수정
4. 수정 후 서버 재시작 → curl 재확인
5. Puppeteer 스크립트 실행 → figures/*.png 수집
6. step-N-*.md 작성 (명령/출력/결과 3단 형식)
7. git add verification/ && git commit
```

# P4-2 App.tsx 라우트 정리 Verification

> Date: 2026-05-10

---

## G2.1 — TypeScript 컴파일

**명령**: `cd frontend && npx tsc --noEmit 2>&1`

**Raw output**:
```
(출력 없음 — 에러 0개)
```

**검증 결과**: ✅ PASS — 컴파일 에러 없음

---

## G2.2 — Bronze 경로 redirect 확인

**명령**: Puppeteer — 각 Bronze 경로 접근 후 최종 URL 확인

**Raw output**:
```
/prices      → /silver/compare ✅
/strategy    → /silver/compare ✅
/correlation → /silver/compare ✅
/indicators  → /silver/compare ✅
/factors     → /silver/compare ✅
/signals     → /silver/compare ✅
/dashboard   → /silver/compare ✅
```

**스크린샷**: `figures/step-2-redirect.png`
- `/prices` 접근 후 `/silver/compare` Tab A 렌더링 확인
- QQQ/SPY/KS200 KPI 정상 표시

**검증 결과**: ✅ PASS — 7개 Bronze 경로 전부 `/silver/compare`로 redirect

---

## 변경 내용 (App.tsx)

- Bronze 페이지 import 5종 제거 (DashboardPage/PricePage/CorrelationPage/IndicatorSignalPage/StrategyPage)
- `Layout` 컴포넌트 import 제거
- `/bronze/*` 라우트 블록 제거
- Bronze 경로 redirect (`/prices`, `/strategy`, `/correlation`, `/indicators`, `/factors`, `/signals`, `/dashboard`) 유지

# P3-4 모바일 반응형 Verification

> Date: 2026-05-10
> Viewport: 768px (tablet), 375px (iPhone SE)

## 변경 사항

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/src/index.css` | `@media (max-width: 768px)` `.silver-kpi-grid: 1fr`, `.silver-pill-group: flex-wrap: wrap`, `.silver-top-nav__items: flex: 1`, `.silver-equity-chart-wrap: 280px` |
| `frontend/src/index.css` | `.silver-equity-chart-wrap { height: 360px }` 기본 정의 추가 |
| `frontend/src/pages/silver/components/EquityChart.tsx` | `silver-equity-chart-wrap` 래퍼 div 추가, `ResponsiveContainer height="100%"` |

---

## G4.1 — 768px nav 가로 스크롤

**명령**:
```js
const navOverflow = await page.$eval('.silver-top-nav__items', el =>
  window.getComputedStyle(el).overflowX
);
// → "auto"
```

**Evidence**:
- `nav overflow-x: auto` ✅
- 스크린샷: `figures/step-4-mobile-nav.png`
  - 상단 nav "Stock Dashboard | 적립식 비교 | 신호 | Chat 💬 | verify · 로그아웃" 가로 정상 표시
  - 탭 네비 3개 전부 표시

**통과 기준**: `overflow-x: auto` 확인 ✅

---

## G4.2 — 768px KPI 1열 + EquityChart 280px

**명령**:
```js
const result = await page.$eval('.silver-kpi-grid', el => ({
  gridTemplateColumns: getComputedStyle(el).gridTemplateColumns,
  width: el.getBoundingClientRect().width,
}));
// → { gridTemplateColumns: "736px", display: "grid", width: 736 }

const chartH = await page.$eval('.silver-equity-chart-wrap', el =>
  getComputedStyle(el).height
);
// → "280px"
```

**Evidence**:
- `gridTemplateColumns: "736px"` = 1fr at 768px viewport (padding 16px×2 제외) ✅
- `EquityChart wrap height: 280px` ✅
- 스크린샷: `figures/step-4-mobile-kpi.png`
  - Tab B "자산 vs 전략" — KPI 카드 4종 1열 세로 스택
  - "최종 자산 4.6억원 / 총 수익률 +284.0% / 연환산 +14.4% / 최대 손실폭 -26.2%"

**통과 기준**: `gridTemplateColumns`가 단일 값(1열) + chart 280px ✅

---

## G4.3 — 768px drawer 풀스크린

**명령**:
```js
const drawerWidth = await page.$eval('.silver-drawer', el =>
  getComputedStyle(el).width
);
// → "768px"
```

**Evidence**:
- `drawer width: 768px` = 100vw at 768px viewport ✅
- 스크린샷: `figures/step-4-mobile-drawer.png`
  - Drawer가 화면 전체 너비 점유
  - 체크박스 + 자산 목록(US ETF / KR 지수 / 벤치마크) 명확히 표시

**통과 기준**: drawer width = viewport width ✅

---

## G4.4 — 375px iPhone SE smoke test

**명령**:
```js
const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
// → 375
// viewport: 375
// OK: no significant horizontal overflow
```

**Evidence**:
- `body scrollWidth: 375` = viewport 동일 → 가로 스크롤 없음 ✅
- 스크린샷: `figures/step-4-iphonese.png`
  - 탭 nav: "단일 자산 | 자산 vs 전략" 1행, "자산 vs 포트폴리오" 2행 (flex-wrap: wrap)
  - 기간 pill: 3년/5년/10년 한 줄 ✅
  - 월 적립금 pill: 30만~200만 1행, 300만 2행으로 wrap ✅
  - 차트 정상 렌더링 ✅

**통과 기준**: 가로 오버플로우 없음 ✅

---

## 결론

| 게이트 | 결과 |
|--------|------|
| G4.1: 768px nav 가로 스크롤 | ✅ PASS |
| G4.2: 768px KPI 1열 + chart 280px | ✅ PASS |
| G4.3: 768px drawer 풀스크린 | ✅ PASS |
| G4.4: 375px iPhone SE smoke test | ✅ PASS |

**P3-4 모바일 반응형 — 전 게이트 PASS**

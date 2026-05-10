# P3-5 AssetPickerDrawer 탭별 분기 Verification

> Date: 2026-05-10

---

## G5.1 — Tab A universe (6종)

**명령**:
```js
// Tab A 기본 → + 자산 추가 클릭 → drawer 열기
const items = await page.$$eval('.silver-drawer__item-label', els =>
  els.map(el => el.textContent?.trim())
);
// → 6종
```

**Raw output**:
```
Tab A items (6): [
  'QQQ (나스닥 100)',
  'SPY (S&P 500)',
  'SCHD (배당 성장)',
  'JEPI (커버드콜)',
  'KOSPI200',
  'WBI (워런 버핏 지수)'
]
```

**스크린샷**: `figures/step-5-drawer-tab-a.png`
- 제목: "자산 선택 (최대 6종)"
- US ETF: QQQ(나스닥 100) ✅ / SPY(S&P 500) ✅ / SCHD(배당 성장) / JEPI(커버드콜)
- KR 지수: KOSPI200 ✅
- 벤치마크: WBI(워런 버핏 지수)
- 현재 3종 선택됨 (QQQ/SPY/KS200) — 기본 선택 확인

**검증 결과**: ✅ PASS — 6종 정확, NVDA/GOOGL 등 D-21 자산 미노출, D-18 universe 준수

---

## G5.2 — Tab B universe (3종)

**명령**:
```js
// Tab B 클릭 → 자산 변경 클릭 → drawer 열기
const items = await page.$$eval('.silver-drawer__item-label', els =>
  els.map(el => el.textContent?.trim())
);
// → 3종
```

**Raw output**:
```
Tab B items (3): [ 'QQQ (나스닥 100)', 'SPY (S&P 500)', 'KOSPI200' ]
```

**스크린샷**: `figures/step-5-drawer-tab-b.png`
- 제목: "자산 선택" (maxSelect=1 → "(최대 N종)" 없음)
- US ETF: QQQ(나스닥 100) ✅(체크) / SPY(S&P 500)
- KR 지수: KOSPI200
- "적용 (1종)" 버튼 — 최대 1종 선택 확인
- SCHD/JEPI/WBI 미노출

**검증 결과**: ✅ PASS — 3종 정확, D-19 universe 준수

---

## G5.3 — Tab C preset select (4개, 비중 편집 없음)

**명령**:
```js
// Tab C 클릭 → preset pill 수집
const presetPills = await page.$$eval(
  '.silver-pill-group:not([role="tablist"]) .silver-pill',
  els => els.map(el => el.textContent?.trim())
);
// → 12개 (기간 3 + 적립금 5 + preset 4)
// preset만 추출: 마지막 4개
```

**Raw output**:
```
Tab C presets (all pills, 12):
  '3년', '5년', '10년',
  '30만', '50만', '100만', '200만', '300만',
  'QQQ + TLT + BTC',       ← preset 1
  'KS200 + TLT + BTC',     ← preset 2
  '테크 + TLT + BTC',       ← preset 3
  '삼성+하이닉스 + TLT + BTC' ← preset 4
```

**스크린샷**: `figures/step-5-drawer-tab-c.png`
- "자산 vs 포트폴리오" 탭 선택
- preset pill 4개 (QQQ+TLT+BTC 활성)
- 비중 정보: "QQQ + TLT + BTC · 비중 60 / 20 / 20" — 편집 UI 없음
- Drawer/편집 UI 미노출 ✅ (D-20 준수)

**검증 결과**: ✅ PASS — preset 4개 정확, 비중 편집 UI 없음, D-20 준수

---

## 결론

| 게이트 | 결과 |
|--------|------|
| G5.1: Tab A universe 6종 | ✅ PASS |
| G5.2: Tab B universe 3종 | ✅ PASS |
| G5.3: Tab C preset 4개, 편집 없음 | ✅ PASS |

**P3-5 AssetPickerDrawer 탭별 분기 — 전 게이트 PASS**

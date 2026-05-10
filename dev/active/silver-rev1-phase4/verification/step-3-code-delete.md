# P4-3 Bronze 코드 삭제 Verification

> Date: 2026-05-10

---

## G3.1 — TypeScript 컴파일 (삭제 후)

**명령**: `cd frontend && npx tsc --noEmit 2>&1`

**Raw output**:
```
(출력 없음 — 에러 0개)
```

**검증 결과**: ✅ PASS — Bronze 파일 7종 삭제 후 컴파일 에러 없음

---

## G3.2 — Silver 페이지 정상 동작

**명령**: Puppeteer — `/silver/compare` + `/silver/signals` 스크린샷

**Raw output**:
```
/silver/compare screenshot saved ✅
/silver/signals rendered: ✅
```

**스크린샷**: `figures/step-3-silver-pages.png`
- Tab A: QQQ 4.6억원 (+284.0% / +14.4% / -26.2%), SPY 3.4억원, KS200 4.6억원 정상 표시
- 차트 3개 시리즈 렌더링 확인

**검증 결과**: ✅ PASS — Bronze 삭제 후 Silver 페이지 완전 정상 동작

---

## G3.3 — 삭제된 파일 없음 확인

**명령**: `ls frontend/src/pages/`

**Raw output**:
```
LoginPage.tsx
SignupPage.tsx
silver
```

**검증 결과**: ✅ PASS — Bronze 페이지 파일 전부 삭제됨. Silver 전용 구조만 존재

---

## 삭제된 파일 목록

| 파일 | 이유 |
|------|------|
| `frontend/src/pages/DashboardPage.tsx` | Silver 메뉴 재편 |
| `frontend/src/pages/PricePage.tsx` | Tab A로 대체 |
| `frontend/src/pages/CorrelationPage.tsx` | Silver 미포함 |
| `frontend/src/pages/StrategyPage.tsx` | backtest 테이블 drop |
| `frontend/src/pages/IndicatorSignalPage.tsx` | SignalDetailPage.tsx로 대체 |
| `frontend/src/pages/FactorPage.tsx` | Bronze 전용 |
| `frontend/src/pages/SignalPage.tsx` | Bronze 전용 |

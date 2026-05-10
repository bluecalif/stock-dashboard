# Phase 3 Debug History — 프론트엔드 신규 페이지
> Gen: silver
> Last Updated: 2026-05-10

---

## Modified Files Summary

```
(Phase 진행 중 갱신)
frontend/src/
├── App.tsx                          (라우트 재편)
├── pages/silver/
│   ├── CompareMainPage.tsx          (신규)
│   ├── SignalDetailPage.tsx         (신규)
│   └── components/
│       ├── SilverLayout.tsx         (신규)
│       ├── CommonInputPanel.tsx     (신규)
│       ├── TabNav.tsx               (신규)
│       ├── AssetPickerDrawer.tsx    (신규)
│       ├── EquityChart.tsx          (신규)
│       ├── KpiCard.tsx              (신규)
│       ├── InterpretCard.tsx        (신규)
│       ├── RiskCard.tsx             (신규)
│       ├── IndicatorCard.tsx        (신규)
│       ├── TabA_SingleAsset.tsx     (신규)
│       ├── TabB_AssetVsStrategy.tsx (신규)
│       └── TabC_AssetVsPortfolio.tsx(신규)
└── api/
    └── simulation.ts               (신규)
```

---

## Lessons Learned

> Phase 진행 중 추가 예정

### 예상 함정 (사전 기록)

- **iOS Safari 100vh**: `min-h-screen`이 iOS에서 address bar 포함 높이를 계산해 하단 버튼 잘림 발생. `min-h-[100dvh]` 사용 또는 CSS `env(safe-area-inset-bottom)` 패딩 적용.
- **Recharts 고정 높이**: `<AreaChart height={360}>` 직접 지정 시 모바일에서 넘침. 반드시 `<ResponsiveContainer>` 감싸기.
- **tabular-nums 누락**: KPI 숫자에 `font-variant-numeric: tabular-nums` 미적용 시 자릿수 흔들림 — 비교 화면에서 특히 두드러짐.
- **CORS 오류**: 로컬 dev에서 `http://localhost:5173` → `http://localhost:8000` 크로스오리진. `vite.config.ts` proxy 또는 FastAPI CORS 설정 확인.

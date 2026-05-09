# Phase E: 전략 페이지 — Debug History
> Last Updated: 2026-03-17

| Bug # | Module | Issue | Fix | File |
|-------|--------|-------|-----|------|
| 1 | Frontend Build | `tsc -b` 빌드 시 IndicatorSignalPage의 `setForwardDays` 미사용 오류 (Vercel 배포 실패) | `const [forwardDays, setForwardDays]` → `const [forwardDays]` | `frontend/src/pages/IndicatorSignalPage.tsx` |

## Modified Files Summary
```
frontend/src/
├── api/analysis.ts                          — fetchStrategyBacktest() 추가
├── types/api.ts                             — StrategyBacktestResponse 타입 추가
├── pages/
│   ├── StrategyPage.tsx                     — 전면 리라이트
│   └── IndicatorSignalPage.tsx              — 미사용 변수 제거
└── components/
    ├── strategy/
    │   ├── StrategyDescriptionCard.tsx       — 신규
    │   └── TradeNarrativePanel.tsx           — 신규
    └── charts/
        ├── EquityCurveWithEvents.tsx         — 신규
        └── AnnualPerformanceChart.tsx        — 신규
```

## Lessons Learned
- `tsc --noEmit`은 통과하지만 `tsc -b`는 더 엄격할 수 있음 (Vercel 빌드 사용) — 로컬 검증 시 `tsc -b`도 확인 필요

# Session Compact

> Generated: 2026-02-14
> Source: Conversation compaction via /compact-and-go

## Goal
Phase 5 Frontend ✅ 완료 → Phase 6 (Deploy & Ops) 착수 예정

## Completed
- [x] **Step 5.1~5.3**: Stage A 기반 구조 (Vite+React+TS, API 클라이언트, 레이아웃)
- [x] **Step 5.4**: 가격 차트 — `PriceLineChart.tsx`, `PricePage.tsx` (멀티 자산, mergeByDate)
- [x] **Step 5.5**: 수익률 비교 — `ReturnsChart.tsx` (기준일=100 정규화, priceMap 공유)
- [x] **Step 5.6**: 상관 히트맵 — `CorrelationHeatmap.tsx` (CSS Grid, RGB 보간), `CorrelationPage.tsx`
- [x] **Step 5.7**: 팩터 현황 — `FactorChart.tsx` (RSI/MACD 서브차트), `FactorPage.tsx` (비교 테이블)
- [x] **Step 5.8**: 시그널 타임라인 — `SignalOverlay.tsx` (ComposedChart+Scatter 마커), `SignalPage.tsx`
- [x] **Step 5.9**: 전략 성과 — `EquityCurveChart.tsx`, `StrategyPage.tsx` (메트릭스+거래 이력)
- [x] **Step 5.10**: 대시보드 홈 — `MiniChart.tsx` (스파크라인), `DashboardPage.tsx` (요약 카드+백테스트 테이블)

## Current State

### 프로젝트 진행률
| Phase | 상태 | Tasks |
|-------|------|-------|
| 1-4 (Skeleton~API) | ✅ 완료 | 46/46 |
| 5 Frontend | ✅ 완료 | 10/10 |
| 6 Deploy & Ops | 미착수 | 0/16 |

### Git / Tests
- Branch: `master`, Backend: 405 passed, Frontend: TSC ✅ / Vite build ✅

### 프론트엔드 구조
```
frontend/src/
├── api/          # client.ts + 7개 API 모듈
├── types/        # api.ts (14개 인터페이스)
├── components/   # layout(Sidebar,Layout) + common(Loading,Error,AssetSelect,DateRange) + charts(7개)
├── pages/        # 6개 완료 (Dashboard,Price,Correlation,Factor,Signal,Strategy)
├── App.tsx       # BrowserRouter + 6 Routes
└── index.css     # Tailwind
```

## Key Decisions
- mergeByDate()/toNormalizedReturns(): Map 기반 멀티 자산 데이터 병합, 첫 종가=100 정규화
- CorrelationHeatmap: CSS Grid + correlationColor() RGB 보간 (-1파랑/0흰/+1빨강)
- FactorChart: RSI(70/30 기준선), MACD(ComposedChart: Bar+Line), formatValue() 유형별 포맷
- SignalOverlay: ComposedChart(Line+Scatter), SVG 삼각형 마커, signalMap 기반 병합
- EquityCurveChart: mergeEquityCurves(), StrategyPage: limit=1 최신 백테스트, 12지표 메트릭스
- 기본 선택: KS200, 기본 기간: 최근 1년

## Context
다음 세션에서는 답변에 한국어를 사용하세요.
- **작업 디렉토리**: `frontend/` (React SPA)
- **venv**: `backend/.venv/Scripts/activate` (Windows), Python 3.12.3
- **Bash 경로**: `/c/Projects-2026/stock-dashboard` (Windows 백슬래시 불가)
- **dev-docs**: `dev/active/phase5-frontend/` (Phase 5 계획)
- **API 스키마 참조**: `backend/api/schemas/` (14개 Pydantic 클래스)
- **CORS**: localhost:5173 허용 완료
- **API endpoints**: 12개 (`/v1/assets`, `/v1/prices/daily`, `/v1/factors`, `/v1/signals`, `/v1/backtests/*`, `/v1/dashboard/summary`, `/v1/correlation`)
- Git remote: `https://github.com/bluecalif/stock-dashboard.git`

## Next Action
1. Phase 6 (Deploy & Ops) 착수 — `dev/active/phase6-deploy/` 계획 수립

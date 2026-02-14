# Session Compact

> Generated: 2026-02-14
> Source: Conversation compaction via /compact-and-go

## Goal
Phase 5 Frontend 구현 완료 → UX 디버깅 (Step 5.11~5.13) → Phase 6 착수

## Completed
- [x] **Step 5.1~5.3**: Stage A 기반 구조 (Vite+React+TS, API 클라이언트, 레이아웃)
- [x] **Step 5.4**: 가격 차트 — `PriceLineChart.tsx`, `PricePage.tsx` (멀티 자산, mergeByDate)
- [x] **Step 5.5**: 수익률 비교 — `ReturnsChart.tsx` (기준일=100 정규화, priceMap 공유)
- [x] **Step 5.6**: 상관 히트맵 — `CorrelationHeatmap.tsx` (CSS Grid, RGB 보간), `CorrelationPage.tsx`
- [x] **Step 5.7**: 팩터 현황 — `FactorChart.tsx` (RSI/MACD 서브차트), `FactorPage.tsx` (비교 테이블)
- [x] **Step 5.8**: 시그널 타임라인 — `SignalOverlay.tsx` (ComposedChart+Scatter 마커), `SignalPage.tsx`
- [x] **Step 5.9**: 전략 성과 — `EquityCurveChart.tsx`, `StrategyPage.tsx` (메트릭스+거래 이력)
- [x] **Step 5.10**: 대시보드 홈 — `MiniChart.tsx` (스파크라인), `DashboardPage.tsx` (요약 카드+백테스트 테이블)
- [x] **UX 확인**: 사용자 테스트 완료 → 11개 버그 발견 (`docs/front-UX-check.md`)
- [x] **디버깅 계획 수립**: 버그 분석 + 수정 계획 (Step 5.11~5.13)

## Current State

### 프로젝트 진행률
| Phase | 상태 | Tasks |
|-------|------|-------|
| 1-4 (Skeleton~API) | ✅ 완료 | 46/46 |
| 5 Frontend | 🔧 UX 디버깅 | 10/13 |
| 6 Deploy & Ops | 미착수 | 0/16 |

### UX 버그 현황 (from `docs/front-UX-check.md`)
| # | 페이지 | 이슈 | 원인 유형 |
|---|--------|------|----------|
| 1 | Home | MiniChart X축 역순 | 코드 (정렬 누락) |
| 2 | Price | Gold/Silver Network Error | 조사 필요 |
| 3 | Price | 거래량 미표시 | 코드 (기능 추가) |
| 4 | Factor | KS200/005930/000660 미표시 | 조사 필요 |
| 5 | Signal | X축 역순 | 코드 (정렬 누락) |
| 6 | Signal | 마커 설명 없음 | 코드 (범례 추가) |
| 7 | Signal | 관망/무신호 구분 불가 | 코드 (signal=0 비표시) |
| 8 | Signal | 추세추종 미표시 | 코드 (`trend_follow` → `trend`) |
| 9 | Signal | 평균회귀 마커만 | 조사 필요 |
| 10 | Strategy | 전체 미표시 | 코드+조사 (전략 ID + 데이터) |
| 11 | Dashboard | 백테스트 상태 배지 | 코드 (`completed` → `success`) |

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

## Remaining / TODO
- [ ] **Step 5.11**: 전략 ID 수정 + X축 정렬 + 시그널 범례/관망 + 대시보드 상태 배지
  - `SignalPage.tsx`, `StrategyPage.tsx`: `trend_follow` → `trend`
  - `DashboardPage.tsx`: MiniChart 정렬 + 상태 `completed` → `success`
  - `SignalOverlay.tsx`: ASC 정렬 + 범례 + 관망 마커(회색●)
- [ ] **Step 5.12**: Gold/Silver 에러 + 거래량 차트
  - API 데이터 확인 → `Promise.allSettled` 방어적 처리
  - `PriceLineChart.tsx`: ComposedChart + Volume Bar
- [ ] **Step 5.13**: 팩터/전략 데이터 확인 (DB 파이프라인 이슈 여부)
- [ ] Phase 6 (Deploy & Ops) 착수

## Key Decisions
- mergeByDate()/toNormalizedReturns(): Map 기반 멀티 자산 데이터 병합, 첫 종가=100 정규화
- CorrelationHeatmap: CSS Grid + correlationColor() RGB 보간 (-1파랑/0흰/+1빨강)
- FactorChart: RSI(70/30 기준선), MACD(ComposedChart: Bar+Line), formatValue() 유형별 포맷
- SignalOverlay: ComposedChart(Line+Scatter), SVG 삼각형 마커, signalMap 기반 병합
- EquityCurveChart: mergeEquityCurves(), StrategyPage: limit=1 최신 백테스트, 12지표 메트릭스
- 기본 선택: KS200, 기본 기간: 최근 1년
- **전략 ID**: 백엔드 `STRATEGY_REGISTRY` = `momentum`, `trend`, `mean_reversion` (프론트 `trend_follow` 오류 수정)
- **X축 정렬**: 백엔드 repo DESC 유지, 프론트에서 ASC 정렬 추가
- **관망 마커**: 회색 원(●)으로 매수(▲)/청산(▼)과 구분

## Context
다음 세션에서는 답변에 한국어를 사용하세요.
- **작업 디렉토리**: `frontend/` (React SPA)
- **venv**: `backend/.venv/Scripts/activate` (Windows), Python 3.12.3
- **Bash 경로**: `/c/Projects-2026/stock-dashboard` (Windows 백슬래시 불가)
- **dev-docs**: `dev/active/phase5-frontend/` (Phase 5 계획)
- **UX 체크 결과**: `docs/front-UX-check.md`
- **디버깅 계획**: `.claude/plans/zany-giggling-stearns.md`
- **API 스키마 참조**: `backend/api/schemas/` (14개 Pydantic 클래스)
- **CORS**: localhost:5173 허용 완료
- **API endpoints**: 12개 (`/v1/assets`, `/v1/prices/daily`, `/v1/factors`, `/v1/signals`, `/v1/backtests/*`, `/v1/dashboard/summary`, `/v1/correlation`)
- Git remote: `https://github.com/bluecalif/stock-dashboard.git`

## Next Action
1. Step 0: API curl 테스트로 데이터 유무 확인 (Gold/Silver, Factor, Backtest)
2. Step 5.11: 코드 버그 수정 (전략 ID, X축, 시그널 범례)
3. Step 5.12: Gold/Silver + 거래량 차트
4. Step 5.13: 데이터 파이프라인 이슈 확인
5. Phase 6 착수

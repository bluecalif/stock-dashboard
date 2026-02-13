# Phase 5: Frontend — Tasks
> Last Updated: 2026-02-13
> Status: In Progress (6/10)

## 5A. 기반 구조

- [x] 5.1 Vite + React 18 + TypeScript 프로젝트 초기화 `[M]`
  - Vite 6.4 + React 19 + TypeScript 5.9 프로젝트 생성
  - TailwindCSS 3.4 + PostCSS + autoprefixer 설정
  - `.env` (VITE_API_BASE_URL), `.gitignore`
  - ESLint 9 + react-hooks/react-refresh 플러그인
  - axios, recharts, react-router-dom 의존성 설치
  - `npm run build` 정상 동작 확인

- [x] 5.2 API 클라이언트 (Axios) + 타입 정의 `[M]`
  - `src/types/api.ts` — 14개 TypeScript 인터페이스 (백엔드 Pydantic 1:1)
  - `src/api/client.ts` — Axios 인스턴스 (baseURL, error interceptor)
  - `src/api/assets.ts` — fetchAssets()
  - `src/api/prices.ts` — fetchPrices()
  - `src/api/factors.ts` — fetchFactors()
  - `src/api/signals.ts` — fetchSignals()
  - `src/api/backtests.ts` — fetchBacktests(), fetchBacktestDetail(), fetchEquity(), fetchTrades(), runBacktest()
  - `src/api/dashboard.ts` — fetchDashboardSummary()
  - `src/api/correlation.ts` — fetchCorrelation()

- [x] 5.3 레이아웃 (사이드바 네비게이션 + 메인 콘텐츠) `[M]`
  - `src/components/layout/Sidebar.tsx` — 6개 메뉴 (NavLink active 스타일링)
  - `src/components/layout/Layout.tsx` — 사이드바 + Outlet 메인 영역
  - `src/App.tsx` — BrowserRouter + 6개 Route 정의
  - `src/components/common/Loading.tsx`, `ErrorMessage.tsx` — 공통 UI
  - `src/components/common/AssetSelect.tsx` — 자산 선택 (단일/멀티 모드)
  - `src/components/common/DateRangePicker.tsx` — 날짜 범위 + 프리셋 버튼
  - 6개 페이지 placeholder 생성 (Dashboard/Price/Correlation/Factor/Signal/Strategy)

## 5B. 핵심 차트

- [x] 5.4 가격 차트 페이지 (라인차트, 자산/기간 선택) `[L]`
  - `src/pages/PricePage.tsx` — AssetSelect 멀티 모드, DateRangePicker, Promise.all 병렬 fetch
  - `src/components/charts/PriceLineChart.tsx` — Recharts LineChart, 7색 팔레트, dot=false
  - mergeByDate()로 멀티 자산 종가 병합, connectNulls, Y축 가격 포맷팅

- [x] 5.5 수익률 비교 차트 (정규화 누적수익률) `[M]`
  - `src/components/charts/ReturnsChart.tsx` — 정규화 수익률 차트 (기준일=100)
  - toNormalizedReturns()로 종가 → 기준일 100 정규화 변환
  - PricePage에 가격/수익률 탭 전환 UI, ReferenceLine y=100 기준선
  - 여러 자산 동시 비교, priceMap 공유로 API 재호출 없음

## 5C. 분석 시각화

- [x] 5.6 상관 히트맵 (자산 간 correlation matrix) `[M]`
  - `src/pages/CorrelationPage.tsx` — 기간/윈도우 필터(DateRangePicker + 5단계 윈도우 버튼), fetchCorrelation API 호출
  - `src/components/charts/CorrelationHeatmap.tsx` — N×N 히트맵 (커스텀 CSS Grid 셀)
  - 색상 스케일: -1(파랑) ~ 0(흰) ~ +1(빨강), 호버 툴팁(4자리 상관계수)
  - 범례 그라디언트 바, 반응형 셀 크기 (자산 수에 따라 조절)

- [ ] 5.7 팩터 현황 (RSI/MACD 서브차트 + 비교 테이블) `[M]`
  - `src/pages/FactorPage.tsx` — 자산/팩터 선택, API 호출
  - `src/components/charts/FactorChart.tsx` — 팩터별 서브차트
  - RSI: 70/30 기준선, MACD: 시그널 라인
  - 팩터 비교 테이블 (자산별 최신 팩터 값)

- [ ] 5.8 시그널 타임라인 (가격 + 매매 마커 오버레이) `[M]`
  - `src/pages/SignalPage.tsx` — 자산/전략 선택, prices + signals API 호출
  - `src/components/charts/SignalOverlay.tsx` — 가격 차트 + 매수/청산 마커
  - 매수: 초록 삼각형 ▲, 청산: 빨강 삼각형 ▼
  - 3전략 시그널 매트릭스 (자산 × 전략 최신 상태)

## 5D. 전략 성과 + 홈

- [ ] 5.9 전략 성과 비교 (에쿼티 커브 + 메트릭스 + 거래 이력) `[L]`
  - `src/pages/StrategyPage.tsx` — 전략/자산 선택, backtests API 호출
  - `src/components/charts/EquityCurveChart.tsx` — 에쿼티 커브 라인 차트
  - 성과 메트릭스 카드 (CAGR, MDD, Sharpe, 승률 등)
  - 거래 이력 테이블 (entry/exit, pnl, cost)
  - 전략 간 비교 (동일 자산, 다른 전략)

- [ ] 5.10 대시보드 홈 (요약 카드 + 미니 차트) `[M]`
  - `src/pages/DashboardPage.tsx` — dashboard/summary API 호출
  - 7자산 요약 카드 (최신가격, 등락률, 최신 시그널)
  - `src/components/charts/MiniChart.tsx` — 미니 가격 라인 (최근 30일)
  - 최근 백테스트 결과 요약 테이블

---

## Summary
- **Total**: 10 tasks (6 completed, 60%)
- **Size 분포**: M: 8, L: 2
- **Stages**: A(3) → B(2) → C(3) → D(2)
- **Critical Path**: 5.1 → 5.2/5.3 → 5.4 → 나머지 페이지

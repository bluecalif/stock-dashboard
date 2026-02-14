# Phase 5: Frontend — Tasks
> Last Updated: 2026-02-14
> Status: Complete (13/13, 100%)

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

- [x] 5.7 팩터 현황 (RSI/MACD 서브차트 + 비교 테이블) `[M]` — `3b8ceed`
  - `src/pages/FactorPage.tsx` — 자산/팩터 멀티 선택, 10개 팩터 토글, API 병렬 fetch, 비교 테이블
  - `src/components/charts/FactorChart.tsx` — RSI(70/30 기준선), MACD(ComposedChart: MACD+Signal+히스토그램), 일반 팩터 라인
  - 팩터 비교 테이블 (자산별 최신 팩터 값, 12개 팩터, 유형별 포맷팅)

- [x] 5.8 시그널 타임라인 (가격 + 매매 마커 오버레이) `[M]`
  - `src/pages/SignalPage.tsx` — 자산/전략 선택, prices + signals API 병렬 호출, 전략 시그널 매트릭스 테이블
  - `src/components/charts/SignalOverlay.tsx` — ComposedChart(Line+Scatter), 커스텀 삼각형 마커, 시그널 툴팁
  - 매수: 초록 삼각형 ▲, 청산: 빨강 삼각형 ▼
  - 3전략 시그널 매트릭스 (전략별 최신 시그널/날짜/스코어/액션)

## 5D. 전략 성과 + 홈

- [x] 5.9 전략 성과 비교 (에쿼티 커브 + 메트릭스 + 거래 이력) `[L]`
  - `src/pages/StrategyPage.tsx` — 자산/전략 선택(3전략 멀티 토글), backtests→equity+trades 병렬 fetch, 성과 메트릭스 비교 테이블(12지표), 거래 이력 테이블
  - `src/components/charts/EquityCurveChart.tsx` — Recharts LineChart, 멀티 백테스트 에쿼티 커브 비교, mergeEquityCurves()
  - 성과 메트릭스: 총수익률/CAGR/MDD/변동성/Sharpe/Sortino/Calmar/승률/거래횟수/평균PnL/B&H CAGR/초과수익
  - 거래 이력: 진입일/진입가/청산일/청산가/방향(매수/매도)/수량/손익/수수료
  - 전략 간 비교 (동일 자산, 다른 전략 — 최신 백테스트 1개씩)

- [x] 5.10 대시보드 홈 (요약 카드 + 미니 차트) `[M]` — `3b583a9`
  - `src/pages/DashboardPage.tsx` — dashboard/summary API 호출
  - 7자산 요약 카드 (최신가격, 등락률, 최신 시그널)
  - `src/components/charts/MiniChart.tsx` — 미니 가격 라인 (최근 30일)
  - 최근 백테스트 결과 요약 테이블

## 5E. UX 디버깅 (사용자 테스트 기반)

- [x] 5.11 UX 버그 수정 — 전략 ID 불일치 + X축 정렬 + 시그널 범례 `[M]` — `398f7da`
  - **전략 ID 불일치** (Critical): `SignalPage.tsx`, `StrategyPage.tsx`에서 `trend_follow` → `trend`로 수정
  - **X축 정렬** (Home+Signal): ASC 정렬 추가 (`DashboardPage.tsx`, `SignalOverlay.tsx`)
  - **시그널 범례**: SignalLegend 컴포넌트 추가, 관망 회색 원(●) 마커
  - **대시보드 상태 배지**: `"completed"` → `"success"`

- [x] 5.12 UX 버그 수정 — Gold/Silver 에러 + 거래량 차트 `[M]` — `398f7da`
  - **Gold/Silver 에러**: `Promise.allSettled` 방어 처리
  - **거래량 차트**: `ComposedChart` + `Bar`(거래량) + 이중 YAxis
  - `mergeByDate()` volume 병합

- [x] 5.13 UX 버그 수정 — 팩터/전략 데이터 + Bug #9 `[S]` — `398f7da`, `d227ee9`
  - **파이프라인 수정**: missing_threshold 10%로 상향 → KS200/005930/000660 팩터 생성 성공
  - **백테스트 저장**: numpy/Timestamp → Python native 타입 변환 헬퍼
  - **CORS**: 5174 포트 추가
  - **NaN 방어**: API 스키마 field_validator로 NaN→None 변환
  - **Bug #9**: mean_reversion close 컬럼 누락 수정 → 전 자산 시그널+백테스트 성공

---

## Summary
- **Total**: 13 tasks (13 completed, 100%) ✅ Phase 5 완료
- **Size 분포**: S: 1, M: 10, L: 2
- **Stages**: A(3) → B(2) → C(3) → D(2) → E(3, UX 디버깅)
- **UX 버그**: 11개 발견 → 11개 수정 완료

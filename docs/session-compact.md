# Session Compact

> Generated: 2026-02-13
> Source: Conversation compaction via /compact-and-go

## Goal
Phase 5 Frontend — Stage C 진행중 (Step 5.6 완료, Step 5.7로 이동)

## Completed
- [x] **Step 5.1~5.3**: Stage A 기반 구조 (이전 세션)
- [x] **Step 5.4 완료**: 가격 차트 페이지 구현
  - `src/components/charts/PriceLineChart.tsx` — Recharts LineChart 래퍼
  - `src/pages/PricePage.tsx` — AssetSelect 멀티 + DateRangePicker + mergeByDate()
- [x] **Step 5.5 완료**: 수익률 비교 차트 (정규화 누적수익률)
  - `src/components/charts/ReturnsChart.tsx` — 기준일=100 정규화 차트, ReferenceLine y=100
  - `src/pages/PricePage.tsx` — 가격/수익률 탭 전환, toNormalizedReturns(), priceMap 공유
- [x] **Step 5.6 완료**: 상관 히트맵 (자산 간 correlation matrix)
  - `src/components/charts/CorrelationHeatmap.tsx` — N×N 히트맵 (CSS Grid, -1~+1 색상 보간, 호버 툴팁, 범례)
  - `src/pages/CorrelationPage.tsx` — DateRangePicker + 5단계 윈도우 버튼(20/40/60/120/250일) + fetchCorrelation
  - TSC ✅ / Vite build ✅

## Current State

### 프로젝트 진행률
| Phase | 이름 | 상태 | Tasks |
|-------|------|------|-------|
| 1 | Skeleton | ✅ 완료 | 9/9 |
| 2 | Collector | ✅ 완료 | 10/10 |
| 3 | Research Engine | ✅ 완료 | 12/12 |
| 4 | API | ✅ 완료 | 15/15 |
| 5 | Frontend | **진행중** | 6/10 |
| 6 | Deploy & Ops | 미착수 | 0/16 |

### Git / Tests
- Branch: `master`
- Backend: 405 passed, 7 skipped
- Frontend: TSC ✅ / Vite build ✅

### 프론트엔드 구조 (현재)
```
frontend/src/
├── api/          # client.ts + 7개 API 모듈 ✅
├── types/        # api.ts (14개 인터페이스) ✅
├── components/
│   ├── layout/   # Sidebar, Layout ✅
│   ├── common/   # Loading, ErrorMessage, AssetSelect, DateRangePicker ✅
│   └── charts/   # PriceLineChart ✅ + ReturnsChart ✅ + CorrelationHeatmap ✅
├── pages/        # PricePage ✅ + CorrelationPage ✅ + 4개 placeholder
├── App.tsx       # BrowserRouter + Routes ✅
├── main.tsx      # 엔트리포인트 ✅
└── index.css     # Tailwind directives ✅
```

## Key Decisions
- PriceLineChart: PricePoint 타입 (date + 동적 asset_id 키)으로 멀티 자산 데이터 병합
- mergeByDate(): Map 기반으로 여러 자산의 가격을 date 기준 단일 배열로 병합
- toNormalizedReturns(): 첫 종가 기준 100 정규화, priceMap 공유로 API 재호출 없음
- 기본 선택: KS200, 기본 기간: 최근 1년
- CorrelationHeatmap: 순수 CSS Grid + RGB 보간 (Recharts 히트맵 미지원)
- correlationColor(): -1(파랑)~0(흰)~+1(빨강) RGB 선형 보간, 셀 크기 자산 수에 따라 반응형

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
1. **Step 5.7 실행**: 팩터 현황 (RSI/MACD 서브차트 + 비교 테이블) `[M]`
   - `src/pages/FactorPage.tsx` — 자산/팩터 선택, API 호출
   - `src/components/charts/FactorChart.tsx` — 팩터별 서브차트
   - RSI: 70/30 기준선, MACD: 시그널 라인
   - 팩터 비교 테이블 (자산별 최신 팩터 값)
2. 이후 Step 5.8 (시그널 타임라인) 순서로 진행

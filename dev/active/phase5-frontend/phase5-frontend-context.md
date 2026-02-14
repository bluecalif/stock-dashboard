# Phase 5: Frontend — Context
> Last Updated: 2026-02-14
> Status: Complete (13/13, 100%)

## 1. 핵심 파일 (이 Phase에서 읽어야 할 기존 코드)

### 백엔드 API 스키마 (TypeScript 타입 매핑 기준)
| 파일 | 용도 |
|------|------|
| `backend/api/schemas/asset.py` | `AssetResponse` — asset_id, name, category, is_active |
| `backend/api/schemas/price.py` | `PriceDailyResponse` — OHLCV + source |
| `backend/api/schemas/factor.py` | `FactorDailyResponse` — asset_id, date, factor_name, version, value |
| `backend/api/schemas/signal.py` | `SignalDailyResponse` — id, signal, score, action, meta_json |
| `backend/api/schemas/backtest.py` | `BacktestRunRequest/Response`, `EquityCurveResponse`, `TradeLogResponse` |
| `backend/api/schemas/dashboard.py` | `AssetSummary`, `DashboardSummaryResponse` |
| `backend/api/schemas/correlation.py` | `CorrelationResponse`, `CorrelationPeriod` |
| `backend/api/schemas/common.py` | `PaginationParams`, `ErrorResponse` |

### 백엔드 API 라우터 (엔드포인트 시그니처 참조)
| 파일 | 엔드포인트 |
|------|-----------|
| `backend/api/routers/health.py` | `GET /v1/health` |
| `backend/api/routers/assets.py` | `GET /v1/assets` |
| `backend/api/routers/prices.py` | `GET /v1/prices/daily` |
| `backend/api/routers/factors.py` | `GET /v1/factors` |
| `backend/api/routers/signals.py` | `GET /v1/signals` |
| `backend/api/routers/backtests.py` | `GET/POST /v1/backtests/*` |
| `backend/api/routers/dashboard.py` | `GET /v1/dashboard/summary` |
| `backend/api/routers/correlation.py` | `GET /v1/correlation` |

### 스킬 가이드
| 파일 | 용도 |
|------|------|
| `.claude/skills/frontend-dev/SKILL.md` | 프론트엔드 아키텍처, 차트 패턴, 안티패턴 |

## 2. 데이터 인터페이스

### 입력 (API 소비)
| API 엔드포인트 | 소비 페이지 | 파라미터 |
|---------------|-----------|---------|
| `GET /v1/dashboard/summary` | 대시보드 홈 | — |
| `GET /v1/assets` | 모든 페이지 (자산 선택 드롭다운) | is_active |
| `GET /v1/prices/daily` | 가격/수익률, 시그널 타임라인 | asset_id, from, to, limit, offset |
| `GET /v1/factors` | 팩터 현황 | asset_id, factor_name, from, to |
| `GET /v1/signals` | 시그널 타임라인 | asset_id, strategy_id, from, to |
| `GET /v1/correlation` | 상관 히트맵 | asset_ids, from, to, window |
| `GET /v1/backtests` | 전략 성과 | strategy_id, asset_id, limit |
| `GET /v1/backtests/{run_id}` | 전략 성과 상세 | — |
| `GET /v1/backtests/{run_id}/equity` | 전략 성과 (에쿼티 커브) | — |
| `GET /v1/backtests/{run_id}/trades` | 전략 성과 (거래 이력) | — |

### 출력 (사용자에게 제공)
| 페이지 | 시각화 유형 |
|--------|-----------|
| 대시보드 홈 | 요약 카드 (7자산), 미니 라인 차트, 최신 시그널 매트릭스 |
| 가격/수익률 | 가격 라인 차트, 정규화 누적수익률 비교 차트 |
| 상관 히트맵 | N×N 상관행렬 히트맵 (기간/윈도우 조절) |
| 팩터 현황 | RSI/MACD 서브차트, 팩터 비교 테이블 |
| 시그널 타임라인 | 가격 차트 + 매수/청산 마커 오버레이, 3전략 시그널 매트릭스 |
| 전략 성과 | 에쿼티 커브 비교, 성과 메트릭스 카드, 거래 이력 테이블 |

## 3. 주요 결정사항

| 항목 | 결정 | 근거 |
|------|------|------|
| 프레임워크 | React 18 + TypeScript | masterplan §8.5.2, 타입 안전성 |
| 빌드 | Vite 5.x | 빠른 HMR, ESM 네이티브 |
| 차트 | Recharts 2.x | React 네이티브, 커스텀 용이, masterplan 지정 |
| HTTP | Axios | 인터셉터/에러 핸들링 편리, masterplan 지정 |
| 라우팅 | React Router v6 | SPA 표준, 6개 페이지 |
| 스타일링 | TailwindCSS 3.x | 유틸리티 기반, 빠른 프로토타이핑 |
| 상태 관리 | React useState + useEffect | MVP 수준에서 충분, 별도 상태 라이브러리 불필요 |
| API Base URL | `VITE_API_BASE_URL` 환경변수 | 하드코딩 금지, 환경별 배포 지원 |
| 히트맵 구현 | 순수 CSS Grid + RGB 보간 | Recharts 히트맵 미지원, 커스텀 구현이 더 유연 |
| 컴포넌트 구조 | Page(fetch) → Chart(pure render) | 관심사 분리, 재사용성 |

## 4. TypeScript 타입 정의 (백엔드 Pydantic ↔ 프론트엔드 1:1)

```typescript
// types/api.ts

interface Asset {
  asset_id: string;
  name: string;
  category: string;
  is_active: boolean;
}

interface PriceDaily {
  asset_id: string;
  date: string;          // YYYY-MM-DD
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
  source: string;
}

interface FactorDaily {
  asset_id: string;
  date: string;
  factor_name: string;
  version: string;
  value: number;
}

interface SignalDaily {
  id: number;
  asset_id: string;
  date: string;
  strategy_id: string;
  signal: number;
  score: number | null;
  action: string | null;
  meta_json: Record<string, unknown> | null;
}

interface BacktestRun {
  run_id: string;        // UUID
  strategy_id: string;
  asset_id: string;
  status: string;
  config_json: Record<string, unknown>;
  metrics_json: Record<string, unknown> | null;
  started_at: string;    // ISO datetime
  ended_at: string | null;
}

interface EquityCurve {
  run_id: string;
  date: string;
  equity: number;
  drawdown: number;
}

interface TradeLog {
  id: number;
  run_id: string;
  asset_id: string;
  entry_date: string;
  entry_price: number;
  exit_date: string | null;
  exit_price: number | null;
  side: string;
  shares: number;
  pnl: number | null;
  cost: number | null;
}

interface AssetSummary {
  asset_id: string;
  name: string;
  latest_price: number | null;
  price_change_pct: number | null;
  latest_signal: Record<string, string> | null;
}

interface DashboardSummary {
  assets: AssetSummary[];
  recent_backtests: BacktestRun[];
  updated_at: string;
}

interface CorrelationPeriod {
  start: string;
  end: string;
  window: number;
}

interface CorrelationMatrix {
  asset_ids: string[];
  matrix: number[][];
  period: CorrelationPeriod;
}
```

## 5. 프로젝트 구조 (목표)

```
frontend/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
├── .env                        # VITE_API_BASE_URL=http://localhost:8000
├── public/
├── src/
│   ├── main.tsx                # 앱 엔트리포인트
│   ├── App.tsx                 # React Router 루트
│   ├── api/
│   │   ├── client.ts           # Axios 인스턴스
│   │   ├── assets.ts           # /v1/assets
│   │   ├── prices.ts           # /v1/prices/daily
│   │   ├── factors.ts          # /v1/factors
│   │   ├── signals.ts          # /v1/signals
│   │   ├── backtests.ts        # /v1/backtests/*
│   │   ├── dashboard.ts        # /v1/dashboard/summary
│   │   └── correlation.ts      # /v1/correlation
│   ├── types/
│   │   └── api.ts              # TypeScript 인터페이스 (14개)
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx     # 사이드바 네비게이션
│   │   │   └── Layout.tsx      # 레이아웃 셸
│   │   ├── charts/
│   │   │   ├── PriceLineChart.tsx
│   │   │   ├── ReturnsChart.tsx
│   │   │   ├── CorrelationHeatmap.tsx
│   │   │   ├── FactorChart.tsx
│   │   │   ├── SignalOverlay.tsx
│   │   │   ├── EquityCurveChart.tsx
│   │   │   └── MiniChart.tsx
│   │   └── common/
│   │       ├── Loading.tsx
│   │       ├── ErrorMessage.tsx
│   │       ├── AssetSelect.tsx
│   │       └── DateRangePicker.tsx
│   └── pages/
│       ├── DashboardPage.tsx   # 대시보드 홈
│       ├── PricePage.tsx       # 가격/수익률
│       ├── CorrelationPage.tsx # 상관 히트맵
│       ├── FactorPage.tsx      # 팩터 현황
│       ├── SignalPage.tsx      # 시그널 타임라인
│       └── StrategyPage.tsx    # 전략 성과
└── .gitignore
```

## 6. Changed Files

### Step 5.1 — 프로젝트 초기화 (이전 세션)
- `frontend/package.json` — Vite 6.4 + React 19 + TS 5.9 + 의존성
- `frontend/vite.config.ts`, `tailwind.config.js`, `postcss.config.js`
- `frontend/tsconfig.json`, `tsconfig.app.json`, `tsconfig.node.json`
- `frontend/eslint.config.js`, `frontend/.env`, `frontend/.gitignore`
- `frontend/index.html`, `frontend/src/main.tsx`, `frontend/src/index.css`

### Step 5.2 — API 클라이언트 + 타입 정의
- `frontend/src/types/api.ts` — 14개 인터페이스 (Pydantic 1:1)
- `frontend/src/api/client.ts` — Axios 인스턴스 + error interceptor
- `frontend/src/api/assets.ts` — fetchAssets()
- `frontend/src/api/prices.ts` — fetchPrices()
- `frontend/src/api/factors.ts` — fetchFactors()
- `frontend/src/api/signals.ts` — fetchSignals()
- `frontend/src/api/backtests.ts` — fetchBacktests/Detail/Equity/Trades/Run
- `frontend/src/api/dashboard.ts` — fetchDashboardSummary()
- `frontend/src/api/correlation.ts` — fetchCorrelation()

### Step 5.3 — 레이아웃 + 라우팅
- `frontend/src/App.tsx` — BrowserRouter + 6개 Route
- `frontend/src/components/layout/Sidebar.tsx` — 사이드바 네비게이션
- `frontend/src/components/layout/Layout.tsx` — Sidebar + Outlet
- `frontend/src/components/common/Loading.tsx` — 로딩 스피너
- `frontend/src/components/common/ErrorMessage.tsx` — 에러 표시 + 재시도
- `frontend/src/components/common/AssetSelect.tsx` — 자산 선택 (단일/멀티)
- `frontend/src/components/common/DateRangePicker.tsx` — 날짜 범위 + 프리셋
- `frontend/src/pages/DashboardPage.tsx` — placeholder
- `frontend/src/pages/PricePage.tsx` — placeholder
- `frontend/src/pages/CorrelationPage.tsx` — placeholder
- `frontend/src/pages/FactorPage.tsx` — placeholder
- `frontend/src/pages/SignalPage.tsx` — placeholder
- `frontend/src/pages/StrategyPage.tsx` — placeholder

### Step 5.4 — 가격 차트 페이지
- `frontend/src/components/charts/PriceLineChart.tsx` — **신규**, Recharts LineChart 래퍼 (멀티 자산, 7색 팔레트)
- `frontend/src/pages/PricePage.tsx` — placeholder → 완전한 가격 차트 페이지 (AssetSelect, DateRangePicker, mergeByDate)

### Step 5.5 — 수익률 비교 차트
- `frontend/src/components/charts/ReturnsChart.tsx` — **신규**, 정규화 누적수익률 차트 (기준일=100, ReferenceLine)
- `frontend/src/pages/PricePage.tsx` — 가격/수익률 탭 전환 UI, toNormalizedReturns(), priceMap 상태 공유

### Step 5.6 — 상관 히트맵
- `frontend/src/components/charts/CorrelationHeatmap.tsx` — **신규**, N×N 히트맵 (CSS Grid, -1~+1 색상 보간, 호버 툴팁, 범례)
- `frontend/src/pages/CorrelationPage.tsx` — placeholder → 완전한 상관 히트맵 페이지 (DateRangePicker, 윈도우 선택, fetchCorrelation)

### Step 5.7 — 팩터 현황
- `frontend/src/components/charts/FactorChart.tsx` — **신규**, RSI/MACD/일반 팩터 서브차트 (RSI: 70/30 기준선, MACD: ComposedChart MACD+Signal+히스토그램, 일반: LineChart)
- `frontend/src/pages/FactorPage.tsx` — placeholder → 완전한 팩터 현황 페이지 (10개 팩터 토글, 자산 멀티 선택, 병렬 fetch, 비교 테이블 12개 팩터 × N자산)

### Step 5.8 — 시그널 타임라인
- `frontend/src/components/charts/SignalOverlay.tsx` — **신규**, ComposedChart(Line+Scatter) 가격차트 + 매매 마커 오버레이 (매수: 초록▲, 청산: 빨강▼), 커스텀 Tooltip
- `frontend/src/pages/SignalPage.tsx` — placeholder → 완전한 시그널 타임라인 페이지 (자산/전략 선택, prices+signals 병렬 fetch, 전략별 차트 렌더링, 3전략 시그널 매트릭스 테이블)

### Step 5.9 — 전략 성과 비교
- `frontend/src/components/charts/EquityCurveChart.tsx` — **신규**, Recharts LineChart 에쿼티 커브 (멀티 백테스트 비교, 7색 팔레트, formatEquity Y축)
- `frontend/src/pages/StrategyPage.tsx` — placeholder → 완전한 전략 성과 페이지 (자산/전략 선택, backtests→equity+trades 병렬 fetch, mergeEquityCurves(), 12지표 메트릭스 비교 테이블, 전략별 거래 이력 테이블)

### Step 5.10 — 대시보드 홈
- `frontend/src/pages/DashboardPage.tsx` — dashboard/summary API, 7자산 요약 카드 + 미니차트 + 백테스트 테이블
- `frontend/src/components/charts/MiniChart.tsx` — **신규**, 스파크라인 미니 차트 (120x40)

### UX 디버깅 — 발견된 버그 (2026-02-14 사용자 테스트)

#### 발견된 버그 목록
| 페이지 | 이슈 | 원인 | 유형 |
|--------|------|------|------|
| Home | MiniChart X축 역순 | 백엔드 DESC 정렬, 프론트 정렬 누락 | 코드 |
| Price | Gold/Silver Network Error | `GC=F`/`SI=F` API 응답 실패 (데이터 유무 확인 필요) | 조사 |
| Price | 거래량 미표시 | `mergeByDate()` close만 추출, volume 무시 | 코드 |
| Factor | KS200/005930/000660 미표시 | 팩터 데이터 유무 확인 필요 | 조사 |
| Signal | X축 역순 | 백엔드 DESC, 프론트 정렬 누락 | 코드 |
| Signal | 마커 설명 없음 | 범례 UI 미구현 | 코드 |
| Signal | 관망/무신호 구분 불가 | signal=0 완전 비표시 | 코드 |
| Signal | 추세추종 미표시 | 전략 ID `trend_follow` vs 백엔드 `trend` 불일치 | 코드 |
| Signal | 평균회귀 마커만 표시 | 가격 데이터 부재 또는 필터링 이슈 | 조사 |
| Strategy | 전체 미표시 | 전략 ID 불일치 + 백테스트 데이터 확인 필요 | 코드+조사 |
| Dashboard | 백테스트 상태 배지 | `"completed"` vs 백엔드 `"success"` 불일치 | 코드 |

#### 핵심 결정사항
| 항목 | 결정 | 근거 |
|------|------|------|
| 전략 ID 수정 | `trend_follow` → `trend` | 백엔드 `STRATEGY_REGISTRY` 키: `momentum`, `trend`, `mean_reversion` |
| X축 정렬 | 프론트에서 ASC 정렬 추가 | 백엔드 repo는 DESC 유지 (최신 우선 조회 효율), 프론트에서 차트용 정렬 |
| 관망 표시 | 회색 원(●) 마커 | 매수(▲초록)/청산(▼빨강)과 시각적 구분 |
| 가격 실패 격리 | `Promise.allSettled` | 개별 자산 실패가 전체 페이지 에러로 전파 방지 |

## 7. 컨벤션 체크리스트

### 프론트엔드 관련
- [x] TypeScript strict mode 활성화
- [x] API 타입 백엔드 Pydantic 스키마와 1:1 매칭
- [x] API URL 환경변수 관리 (`VITE_API_BASE_URL`)
- [x] Axios 인스턴스 중앙화 (`api/client.ts`)
- [x] Recharts ResponsiveContainer 항상 사용
- [x] 일봉 데이터 `dot={false}` (데이터 포인트 다수)
- [x] Page(fetch+state) → Chart(props) 분리
- [x] React Router v6 경로 정의
- [x] TailwindCSS 유틸리티 사용
- [x] CORS: localhost:5173 (Vite dev server)

### 인코딩 관련
- [ ] JSON 응답: UTF-8 자동 (Axios)
- [ ] 한글 자산명 정상 렌더링 확인

### 숫자/날짜 포맷
- [ ] 날짜: `YYYY-MM-DD` (ISO 8601)
- [ ] 가격: `toLocaleString('ko-KR')` (천 단위 콤마)
- [ ] 수익률: 소수점 2자리 + `%` 접미사

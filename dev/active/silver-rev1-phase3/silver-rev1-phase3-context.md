# Phase 3 Context — 프론트엔드 신규 페이지
> Gen: silver
> Last Updated: 2026-05-10

---

## 0. 핵심 원칙 — "Show, don't claim"

> **검증 게이트의 체크박스는 evidence가 `verification/step-N-<topic>.md`에 paste되고 사용자가 본 후에만 표시 가능.**
> Claude의 "PASS / 통과" 주장만으로는 mark complete 금지. UI step은 반드시 PNG 스크린샷 첨부.

---

## 1. 핵심 참조 파일

### 1.1 이 Phase에서 반드시 읽어야 할 기존 코드

| 파일 | 용도 |
|---|---|
| `frontend/src/App.tsx` | 현재 라우트 구조 — Silver 추가 시 충돌 방지 |
| `frontend/src/components/layout/Layout.tsx` | Bronze 레이아웃 — Silver는 SilverLayout으로 분리 |
| `frontend/src/components/layout/Sidebar.tsx` | Bronze nav — Silver는 상단 nav로 교체 |
| `frontend/src/pages/IndicatorSignalPage.tsx` | SignalDetailPage 베이스 (단순화 출발점) |
| `frontend/src/api/prices.ts` | API 클라이언트 패턴 — simulation.ts 작성 시 참고 |
| `frontend/src/components/charts/EquityCurveChart.tsx` | 기존 Recharts 패턴 |
| `backend/api/routers/simulation.py` | 응답 스키마 확인 (replay/strategy/portfolio) |
| `backend/api/schemas/simulation.py` | Pydantic 스키마 → TypeScript 타입 변환 기준 |

### 1.2 디자인 레퍼런스

| 파일 | 용도 |
|---|---|
| `.claude/skills/frontend-dev/references/silver-design.md` | 디자인 토큰, KpiCard 레시피, EquityChart 레시피, Pill 셀렉터, AssetPickerDrawer |
| `docs/UX-design-ref.JPG` | 다크 네이비 SaaS 대시보드 시각 레퍼런스 |
| `docs/silver-masterplan.md` §4, §6 | IA 와이어프레임 + 컴포넌트 명세 |

---

## 2. 데이터 인터페이스

### 2.1 API 엔드포인트 (Phase 2 완성)

| 엔드포인트 | 메서드 | 설명 |
|---|---|---|
| `/v1/silver/simulate/replay` | POST | Tab A — 적립식 단순 replay |
| `/v1/silver/simulate/strategy` | POST | Tab B — 전략 A/B 적용 |
| `/v1/silver/simulate/portfolio` | POST | Tab C — 60/20/20 포트폴리오 |
| `/v1/fx/usd-krw` | GET | USD/KRW 환율 조회 (표시용) |

### 2.2 요청 스키마 (TypeScript 타입)

```typescript
// api/simulation.ts
export interface ReplayRequest {
  asset_codes: string[];        // ["QQQ", "SPY", "KS200"]
  monthly_amount: number;       // 1000000 (원 단위)
  period_years: number;         // 3, 5, 10
  base_currency: "KRW" | "local";
}

export interface StrategyRequest extends ReplayRequest {
  strategy_type: "A" | "B";
}

export interface PortfolioRequest {
  preset_id: string;            // "qqqtltbtc" | "ks200tltbtc" | ...
  monthly_amount: number;
  period_years: number;
}
```

### 2.3 응답 스키마

```typescript
export interface EquityPoint {
  date: string;                 // "2016-05-10"
  krw_value: number;
}

export interface KpiResult {
  final_asset_krw: number;
  total_return: number;         // 0.2839 = +28.39%
  annualized_return: number;    // 0.1440 = +14.40%
  yearly_worst_mdd: number;     // -0.2624 = -26.24%
  yearly_mdd: Record<string, number>;
}

export interface SimulationResult {
  asset_code: string;
  curve: EquityPoint[];
  kpi: KpiResult;
  is_padding: boolean;          // JEPI 등 padding 구간 존재 여부
  padding_start_date?: string;  // padding 구간 시작일
}

export interface ReplayResponse {
  results: SimulationResult[];
}
```

### 2.4 컴포넌트 데이터 흐름

```
CommonInputPanel
 ├─ period_years: 3|5|10
 └─ monthly_amount: 30|50|100|200|300만원

TabA_SingleAsset
 ├─ POST /v1/silver/simulate/replay
 ├─ results[] → EquityChart (multi-series)
 └─ results[] → KpiCard × (자산 수)

TabB_AssetVsStrategy
 ├─ POST /v1/silver/simulate/strategy (type A)
 ├─ POST /v1/silver/simulate/strategy (type B)
 └─ results[] → EquityChart + KpiCard

TabC_AssetVsPortfolio
 ├─ POST /v1/silver/simulate/replay (선택 자산)
 ├─ POST /v1/silver/simulate/portfolio (preset)
 └─ results[] → EquityChart + KpiCard
```

---

## 3. 주요 결정사항

| # | 결정 | 출처 | 코딩 영향 |
|---|---|---|---|
| D-11 | 상단 가로 nav (`SilverLayout`) | Q6-16 | Bronze `Layout`/`Sidebar`와 분리. Silver 라우트만 `SilverLayout`으로 감쌈 |
| D-12 | chat/AI = Bronze Phase F 그대로 | Q6-19 | `/silver/chat` → Bronze `ChatPage` 재사용 |
| D-13 | 신호 카드 = RSI/MACD/ATR 개별 상태 라벨 | Q7-21 | `IndicatorCard`에 상태 라벨("과매수", "골든크로스" 등) |
| D-18 | Tab A universe = QQQ/SPY/KS200/SCHD/JEPI/WBI 6종 | §8.2 lock | `AssetPickerDrawer`의 Tab A 옵션 목록 |
| D-19 | Tab B 자산 = QQQ/SPY/KS200 3종만 | §9.2 lock | `AssetPickerDrawer`의 Tab B 옵션 목록 |
| D-20 | Tab C preset = 4개 고정, 사용자 비중 편집 불가 | §10.5 lock | preset select UI (비중 편집 UI 추가 금지) |
| D-21 | 신호 자산 = 8종 (QQQ/SPY/KS200/NVDA/GOOGL/TSLA/005930/000660) | §12.3 lock | `SignalDetailPage` 자산 select 옵션 |
| D-2 | JEPI padding 구간 차트 회색 표시 | Q1-2 | `EquityChart` — `<ReferenceArea>` 회색 + "padding 구간" 라벨 |

### 3.1 Bronze 페이지 처리 (Phase 3에서는 코드 삭제 금지)

Phase 3에서는 Bronze 라우트를 redirect만 추가. 기존 `DashboardPage`, `PricePage`, `CorrelationPage`, `StrategyPage`, `IndicatorSignalPage` 파일은 **Phase 4까지 그대로 유지**. import도 유지.

### 3.2 SilverLayout vs Bronze Layout

```typescript
// App.tsx 구조
<Route element={<ProtectedRoute />}>
  {/* Silver 페이지 — SilverLayout */}
  <Route element={<SilverLayout />}>
    <Route path="silver/compare" element={<CompareMainPage />} />
    <Route path="silver/signals" element={<SignalDetailPage />} />
    <Route path="silver/chat" element={<ChatPage />} />
  </Route>

  {/* Bronze 페이지 — 기존 Layout (Phase 4까지 유지) */}
  <Route element={<Layout />}>
    <Route index element={<DashboardPage />} />
    <Route path="prices" element={<PricePage />} />
    ...
  </Route>
</Route>
```

---

## 4. 컨벤션 체크리스트

### 4.1 Silver 디자인 토큰 (silver-design.md §2 기준)

| 항목 | 규칙 |
|---|---|
| 배경 | `--bg-app: #0A0E1A`, `--bg-card: #131826` — CSS 변수 사용, 헥스 하드코딩 금지 |
| 텍스트 | `--text-primary: #F1F5F9`, `--text-secondary: #94A3B8` |
| 액센트 | 첫 시리즈 `--accent-green: #3DD68C`, 두 번째 `--accent-blue: #60A5FA` |
| KPI 양수 | `--accent-green`, 음수 | `--accent-red: #EF4444` |
| KPI 숫자 | `font-variant-numeric: tabular-nums`, size 32~40px |
| 차트 | `dot={false}`, `ResponsiveContainer` 필수, 그리드 `rgba(255,255,255,0.04)` |
| 모바일 | 768px 기준 `@media (max-width: 768px)` |

### 4.2 코드 컨벤션

- TypeScript 타입 정의: `frontend/src/types/api.ts` 에 추가 (Silver 섹션)
- API 클라이언트: `frontend/src/api/simulation.ts` 신규 생성
- 컴포넌트: `frontend/src/pages/silver/components/` 위치
- 상태 관리: 로컬 useState 우선 (Zustand store는 전역 필요 시만)

### 4.3 금지 사항

- 헥스 색 하드코딩 (토큰 사용)
- 라이트 모드 추가 (rev1 다크 모드 단일)
- Tab C에서 사용자 비중 편집 UI (D-20: preset 고정)
- Bronze 파일 삭제/수정 (Phase 4까지 금지)

---

## 5. Tab C Preset 목록 (§10.5 lock)

| preset_id | 비중 | 설명 |
|---|---|---|
| `qqqtltbtc` | QQQ 60% / TLT 20% / BTC 20% | 미국 성장주 중심 |
| `ks200tltbtc` | KS200 60% / TLT 20% / BTC 20% | 국내 지수 중심 |
| `techblendtltbtc` | (NVDA+GOOGL+TSLA) 60% / TLT 20% / BTC 20% | 테크 혼합 |
| `samsungtltbtc` | (005930+000660) 60% / TLT 20% / BTC 20% | 국내 반도체 |

---

## 6. AssetPickerDrawer Universe (lock 요약)

| 탭 | 사용 가능 자산 | 최대 선택 | 기본 선택 |
|---|---|---|---|
| Tab A | QQQ / SPY / KS200 / SCHD / JEPI / WBI (6종) | 6종 | QQQ, SPY, KS200 |
| Tab B | QQQ / SPY / KS200 (3종) | 1종 | QQQ |
| Tab C | preset 4개 선택 (비중 편집 불가) | 1개 | qqqtltbtc |

---

## 8. P3-4 변경사항 (2026-05-10)

### 변경된 파일

| 파일 | 변경 내용 |
|------|-----------|
| `frontend/src/index.css` | `@media (max-width: 768px)`: `.silver-kpi-grid: 1fr`, `.silver-pill-group: flex-wrap: wrap`, `.silver-top-nav__items: flex: 1; min-width: 0` |
| `frontend/src/index.css` | `.silver-equity-chart-wrap { height: 360px }` + 768px에서 `280px` |
| `frontend/src/pages/silver/components/EquityChart.tsx` | `silver-equity-chart-wrap` 래퍼 div 추가, `ResponsiveContainer height="100%"` |
| `dev/active/silver-rev1-phase3/verification/step-4-mobile.md` | G4.1~G4.4 evidence |
| `dev/active/silver-rev1-phase3/verification/figures/step-4-mobile-nav.png` | 768px nav 스크린샷 |
| `dev/active/silver-rev1-phase3/verification/figures/step-4-mobile-kpi.png` | 768px KPI 1열 스크린샷 |
| `dev/active/silver-rev1-phase3/verification/figures/step-4-mobile-drawer.png` | 768px drawer 풀스크린 스크린샷 |
| `dev/active/silver-rev1-phase3/verification/figures/step-4-iphonese.png` | 375px smoke test 스크린샷 |

### 주요 결정사항

| # | 결정 | 이유 |
|---|---|---|
| D-P3-4-1 | nav 가로 스크롤은 `silver-top-nav__items`에 이미 적용됨 (신규 CSS 불필요) | 기존 overflow-x: auto + scrollbar-width: none으로 구현 완료 |
| D-P3-4-2 | `EquityChart`에 CSS 기반 반응형 height 적용 (`silver-equity-chart-wrap`) | React state/hook 없이 CSS media query로 처리, `height` prop으로 override 가능 |
| D-P3-4-3 | drawer `width: 100vw`는 이미 768px media query에 구현됨 | AssetPickerDrawer.tsx 변경 불필요 |
| D-P3-4-4 | `.silver-pill-group { flex-wrap: wrap }` → TabNav도 375px에서 줄바꿈 | 탭 이름이 모두 보이는 UX가 가로 스크롤보다 초보자에게 유리 |

---

## 7. P3-3 변경사항 (2026-05-10)

### 변경된 파일

| 파일 | 변경 내용 |
|---|---|
| `frontend/src/pages/silver/SignalDetailPage.tsx` | 플레이스홀더 → 전체 구현 (351줄) |
| `dev/active/silver-rev1-phase3/verification/step-3-signals.md` | G3.1~G3.3 evidence |
| `dev/active/silver-rev1-phase3/verification/figures/step-3-signals-desktop.png` | RSI 탭 스크린샷 |
| `dev/active/silver-rev1-phase3/verification/figures/step-3-signals-indicator-closeup.png` | IndicatorCard 클로즈업 |
| `dev/active/silver-rev1-phase3/verification/figures/step-3-signals-macd.png` | MACD 탭 스크린샷 |

### 주요 결정사항

| # | 결정 | 이유 |
|---|---|---|
| D-P3-3-1 | QQQ/SPY/NVDA/GOOGL/TSLA 팩터 미계산 → `run_research.py` 실행으로 해결 | 7코어 자산에만 팩터 있었음. D-21 universe 전체 지원 위해 2년치 재계산 |
| D-P3-3-2 | 상태 라벨 IndicatorCard 재사용 ("고변동성" → "고변동" 사용) | IndicatorCard TS 타입 union에 "고변동"만 정의됨 |
| D-P3-3-3 | 날짜 범위 고정 (최근 1년), picker 미제공 | Silver 신호 페이지 단순화 방향 (초보자 UX) |

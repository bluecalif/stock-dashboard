# Session Compact

> Generated: 2026-05-10
> Source: /compact-and-go → 수동 갱신

## Goal

Silver gen Phase 3 — 프론트엔드 신규 페이지 구현.

## Completed

- [x] **Phase 1 전체** (P1-1~P1-6): 데이터 인프라, 15자산 backfill, fx_daily, padding/wbi
- [x] **Phase 2 전체** (P2-1~P2-7): simulation 패키지 8파일 + API 4종 + 61 tests PASSED
- [x] **Phase 3 P3-1**: App.tsx 라우트 재편 + SilverLayout + Silver CSS 토큰 + simulation API 클라이언트 — `eb4c821`

## Current State

- **라우트**: `/silver/compare` → CompareMainPage 플레이스홀더, `/` 및 Bronze 라우트 → redirect 적용
- **SilverLayout**: 상단 가로 nav (적립식 비교 / 신호 / Chat), `var(--bg-app: #0A0E1A)` 다크 톤
- **simulation.ts**: `fetchReplay`, `fetchStrategy`, `fetchPortfolio` API 클라이언트 완성
- **types/api.ts**: Silver simulation 타입 추가 (`EquityPoint`, `SimKpi`, `ReplayResponse` 등)
- **Bronze 페이지**: `/bronze/*` 경로로 직접 접근 가능 (Phase 4까지 유지)

### 환경

- Railway prod DB (단일, staging 없음)
- 서버: `uvicorn api.main:app --port 8000` (backend/ 에서 실행)
- 프론트: `npm run dev` (frontend/ 에서 실행, port 5173)
- 커밋 형식: `[silver-rev1-phase3] Step X.Y: description`
- Git Bash: `/c/Users/User/Projects-2026/active/stock-dashboard`

## Remaining / TODO

### Phase 3 (현재)

- [x] **P3-1**: App.tsx + SilverLayout + routes + API 클라이언트 `eb4c821`
- [ ] **P3-2 (L)**: 11개 컴포넌트 완성 + CompareMainPage 실제 구현
  - CommonInputPanel (기간/적립금 pill)
  - TabNav, TabA_SingleAsset, TabB_AssetVsStrategy, TabC_AssetVsPortfolio
  - AssetPickerDrawer, EquityChart (Recharts AreaChart multi-series)
  - KpiCard, InterpretCard, RiskCard, IndicatorCard
- [ ] **P3-3 (M)**: SignalDetailPage (8종 자산, RSI/MACD/ATR)
- [ ] **P3-4 (L)**: 모바일 반응형 768px
- [ ] **P3-5 (S)**: AssetPickerDrawer 탭별 universe 검증 (Tab A 6종 / Tab B 3종 / Tab C preset)

### Phase 4~5 (다음 세션)

- [ ] Phase 4: 빅뱅 cut-over (Bronze 코드 삭제, 테이블 drop, Agentic tool 정리)
- [ ] Phase 5: 후속 안정화

## Key Decisions

- **SilverLayout**: Bronze `Layout`/`Sidebar`와 완전 분리. Silver 라우트만 SilverLayout으로 감쌈
- **Bronze 보존 경로**: `/bronze/dashboard`, `/bronze/prices` 등 — Phase 4까지 직접 접근 가능
- **CSS 전략**: CSS 변수(`:root`) + Tailwind 혼용. `index.css`에 Silver 토큰 + 컴포넌트 클래스 추가
- **simulation.ts**: axios apiClient 재사용, POST 3종 (replay/strategy/portfolio)

## Next Action

### P3-2: 11개 컴포넌트 + CompareMainPage 완성

구현 순서:
1. `CommonInputPanel.tsx` + `TabNav.tsx` (입력 패널, 탭 전환)
2. `EquityChart.tsx` (Recharts AreaChart, multi-series, JEPI padding)
3. `KpiCard.tsx` + `InterpretCard.tsx` + `RiskCard.tsx` + `IndicatorCard.tsx`
4. `AssetPickerDrawer.tsx` (Tab별 universe 분기)
5. `TabA_SingleAsset.tsx` → `TabB_AssetVsStrategy.tsx` → `TabC_AssetVsPortfolio.tsx`
6. `CompareMainPage.tsx` (전체 조합)

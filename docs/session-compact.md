# Session Compact

> Generated: 2026-05-10
> Source: /compact-and-go

## Goal

Silver gen Phase 3 프론트엔드 구현 — P3-1 완료 후 P3-2 (11개 컴포넌트) 착수 준비.

## Completed

- [x] **Phase 2 마무리**: P2-7 fixtures JSON 생성 + 커밋 (`1f7e426`) + tasks.md 완료 표시
- [x] **project-overall 동기화**: Phase 2 ✅ 완료 (7/7, 13/29), Phase 3 진입 조건 갱신 (`630af0d`)
- [x] **Phase 3 dev-docs 작성**: plan/context/tasks/debug-history/verification README 5파일 (`4ccecdf`)
- [x] **P3-1 완료** (`eb4c821`):
  - `frontend/src/index.css` — Silver CSS 토큰 (`:root` 변수) + `.silver-top-nav`, `.silver-card`, `.silver-pill-group` 등 컴포넌트 클래스
  - `frontend/src/pages/silver/components/SilverLayout.tsx` — 상단 가로 nav (적립식 비교/신호/Chat), ChatPanel 유지, 다크 셸
  - `frontend/src/pages/silver/CompareMainPage.tsx` — 플레이스홀더
  - `frontend/src/pages/silver/SignalDetailPage.tsx` — 플레이스홀더
  - `frontend/src/App.tsx` — Silver 라우트 추가 + Bronze 5개 → `/silver/compare` redirect + Bronze 직접 접근 `/bronze/*` 보존
  - `frontend/src/api/simulation.ts` — `fetchReplay` / `fetchStrategy` / `fetchPortfolio`
  - `frontend/src/types/api.ts` — `EquityPoint`, `SimKpi`, `ReplayResponse`, `StrategyResponse`, `PortfolioResponse` 타입 추가

## Current State

- **Phase 3 진행 중** (1/5 완료)
- `/silver/compare` → CompareMainPage 플레이스홀더 렌더링 (라우트 동작)
- `/` 및 Bronze 라우트(`/prices`, `/correlation` 등) → `/silver/compare` redirect
- Bronze 페이지는 `/bronze/*` 경로로 여전히 직접 접근 가능 (Phase 4까지 유지)
- `npm run build` 통과 (TypeScript 오류 없음)
- Railway prod DB: asset_master 15행, price_daily 37,671행, fx_daily 2,603행
- alembic head: `d8334483342c`

### Changed Files (이번 세션)
- `frontend/src/index.css` — Silver 토큰 + CSS 클래스 추가
- `frontend/src/App.tsx` — Silver 라우트 + Bronze redirect
- `frontend/src/pages/silver/components/SilverLayout.tsx` — 신규
- `frontend/src/pages/silver/CompareMainPage.tsx` — 신규 (플레이스홀더)
- `frontend/src/pages/silver/SignalDetailPage.tsx` — 신규 (플레이스홀더)
- `frontend/src/api/simulation.ts` — 신규
- `frontend/src/types/api.ts` — Silver 타입 추가
- `dev/active/silver-rev1-phase3/silver-rev1-phase3-tasks.md` — P3-1 완료 표시
- `docs/session-compact.md` — 현재 파일

## Remaining / TODO

### Phase 3

- [x] P3-1: App.tsx + SilverLayout + routes + API 클라이언트 `eb4c821`
- [ ] **P3-2 (L)**: 11개 컴포넌트 + CompareMainPage 완성
- [ ] **P3-3 (M)**: SignalDetailPage 완성 (8종 자산, RSI/MACD/ATR)
- [ ] **P3-4 (L)**: 모바일 반응형 768px
- [ ] **P3-5 (S)**: AssetPickerDrawer 탭별 universe 검증

## Key Decisions

- **SilverLayout 분리**: Bronze `Layout`/`Sidebar`와 완전 분리. Silver 라우트만 SilverLayout 감쌈
- **Bronze 보존 경로**: `/bronze/*` — Phase 4 삭제 전까지 직접 접근 가능하게 유지
- **CSS 전략**: CSS 변수(`:root`) + Tailwind 혼용. `index.css`에 Silver 토큰 + 컴포넌트 클래스
- **simulation.ts**: 기존 axios `apiClient` 재사용, POST 3종
- **Chat**: 별도 `/silver/chat` 라우트 없이 SilverLayout 내 ChatPanel 플로팅 버튼 유지 (Bronze AI 그대로)

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 핵심 참조

- `dev/active/silver-rev1-phase3/silver-rev1-phase3-tasks.md` — P3-2 게이트 상세
- `dev/active/silver-rev1-phase3/silver-rev1-phase3-context.md` — API 타입, 디자인 토큰, 컨벤션
- `.claude/skills/frontend-dev/references/silver-design.md` — 디자인 토큰 + 컴포넌트 레시피 (필수)
- `docs/silver-masterplan.md` §4, §6 — IA 와이어프레임 + 컴포넌트 명세
- `backend/api/schemas/simulation.py` — Pydantic 스키마 (이미 TypeScript 타입 변환 완료)

### P3-2 구현 순서 (추천)

1. `CommonInputPanel.tsx` + `TabNav.tsx` (기간/적립금 pill, 탭 전환)
2. `EquityChart.tsx` (Recharts AreaChart, multi-series, JEPI padding 회색 영역)
3. `KpiCard.tsx` + `InterpretCard.tsx` + `RiskCard.tsx` + `IndicatorCard.tsx`
4. `AssetPickerDrawer.tsx` (Tab별 universe 분기: A 6종 / B 3종 / C preset 4개)
5. `TabA_SingleAsset.tsx` → `TabB_AssetVsStrategy.tsx` → `TabC_AssetVsPortfolio.tsx`
6. `CompareMainPage.tsx` (전체 조합)

### Tab C Preset 목록 (lock)

| preset_key | 비중 |
|---|---|
| `QQQ_TLT_BTC` | QQQ 60% / TLT 20% / BTC 20% |
| `KS200_TLT_BTC` | KS200 60% / TLT 20% / BTC 20% |
| `TECH_TLT_BTC` | (NVDA+GOOGL+TSLA) 60% / TLT 20% / BTC 20% |
| `SAMSUNG_TLT_BTC` | (005930+000660) 60% / TLT 20% / BTC 20% |

### 환경

- 서버: `uvicorn api.main:app --port 8000` (backend/)
- 프론트: `npm run dev` (frontend/, port 5173)
- 커밋 형식: `[silver-rev1-phase3] P3-N: description`

## Next Action

### P3-2: 11개 컴포넌트 + CompareMainPage 완성

`frontend/src/pages/silver/components/` 에 아래 순서로 구현:

1. **CommonInputPanel.tsx**: 기간 pill (3년/5년/10년), 적립금 pill (30/50/100/200/300만원) — `silver-pill-group` CSS 클래스 사용
2. **TabNav.tsx**: [단일자산] [자산vs전략] [자산vs포트폴리오] 탭 전환 — `silver-pill--active` 스타일
3. **EquityChart.tsx**: Recharts `AreaChart`, multi-series (SERIES_COLORS 순서), JEPI padding `<ReferenceArea>` 회색
4. **KpiCard.tsx**: 4종 KPI (최종자산/총수익/연환산/MDD), tabular-nums, 양음 색상
5. **InterpretCard.tsx**: 초보자 문구 템플릿
6. **RiskCard.tsx**: worst MDD + amber 톤 경고
7. **IndicatorCard.tsx**: RSI/MACD/ATR 현재값 + 상태 라벨
8. **AssetPickerDrawer.tsx**: 우측 슬라이드, Tab별 universe 분기
9. **TabA_SingleAsset.tsx**: `fetchReplay` 호출 + 차트 + KPI
10. **TabB_AssetVsStrategy.tsx**: `fetchReplay` + `fetchStrategy` 병렬 호출
11. **TabC_AssetVsPortfolio.tsx**: `fetchReplay` + `fetchPortfolio` 호출
12. **CompareMainPage.tsx**: 전체 조합 (공통 상태 + 탭 전환)

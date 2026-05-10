# Phase 3 Tasks — 프론트엔드 신규 페이지
> Gen: silver
> Last Updated: 2026-05-10
> Status: **완료** (5/5)

## DoD (Definition of Done)

- [ ] `/silver/compare` 진입 → Tab A 기본 렌더링 (QQQ/SPY/KS200 3종, 10년, 100만)
- [ ] Tab A/B/C 전환 및 각 탭 API 호출 + KPI 카드 표시
- [ ] Bronze 라우트 → `/silver/compare` redirect 동작
- [ ] `/silver/signals` → 8종 자산 select + RSI/MACD/ATR 차트
- [ ] 모바일 768px — nav/차트/KPI 반응형 확인
- [ ] AssetPickerDrawer — Tab A 6종, Tab B 3종, Tab C preset 분기
- [ ] verification/ evidence 5종 + PNG (UI screenshot) 누적
- [ ] `project-overall-tasks.md` Phase 3 섹션 동기화

---

## P3-1 (M) — App.tsx 라우트 재편 + SilverLayout

**목표**: Silver 라우트를 App.tsx에 등록하고, Bronze 라우트를 `/silver/compare`로 redirect. 상단 가로 nav `SilverLayout` 컴포넌트 작성.

**핵심 lock**: D-11 (상단 가로 nav), D-12 (chat/AI 유지), Phase 4까지 Bronze 파일 삭제 금지.

### Sub-steps

- [x] `frontend/src/pages/silver/components/SilverLayout.tsx` 작성 (상단 가로 nav + Outlet)
- [x] `App.tsx` — `/silver/*` 라우트 추가, Bronze 5개 라우트에 `<Navigate to="/silver/compare" />` redirect 추가
- [x] `frontend/src/api/simulation.ts` — API 클라이언트 함수 (fetchReplay, fetchStrategy, fetchPortfolio)
- [x] `frontend/src/types/api.ts` — Silver 시뮬레이션 타입 추가 (SimulationResult, KpiResult, EquityPoint)
- [x] verification/step-1-routes.md 작성

### G1.1 — `/silver/compare` 라우트 접근 동작
- 명령: `npm run dev` 기동 후 브라우저에서 `http://localhost:5173/silver/compare` 접속
- Evidence: 화면 스크린샷 → `verification/figures/step-1-route-desktop.png`
- 통과 기준: 404가 아닌 CompareMainPage 렌더링 (플레이스홀더 라도), 상단 nav 표시

### G1.2 — Bronze redirect 동작
- 명령: 브라우저에서 `http://localhost:5173/prices` 접속
- Evidence: 리다이렉트 결과 스크린샷 (URL 바 `/silver/compare` 표시) → `verification/figures/step-1-redirect.png`
- 통과 기준: `/prices` → `/silver/compare`로 리다이렉트, URL 변경 확인

### G1.3 — SilverLayout 상단 nav 항목
- 명령: `http://localhost:5173/silver/compare` 접속 후 nav 항목 확인
- Evidence: 스크린샷 (nav 영역 클로즈업) → step-1-routes.md에 paste
- 통과 기준: [적립식 비교] [신호] [Chat] [프로필] 4항목 렌더링, 활성 항목 highlight

---

## P3-2 (L) — 11개 컴포넌트 + API 연동

**목표**: CompareMainPage 및 하위 11개 컴포넌트를 작성하고 시뮬레이션 API와 연동. Tab A는 실제 QQQ/SPY/KS200 10년 결과를 렌더링해야 통과.

**핵심 lock**: D-18 (Tab A 6종 universe), D-19 (Tab B 3종), D-20 (Tab C preset 4개), SERIES_COLORS 순서, tabular-nums KPI.

### Sub-steps

- [x] `CommonInputPanel.tsx` — 기간 pill (3/5/10년), 적립금 pill (30/50/100/200/300만원)
- [x] `TabNav.tsx` — [단일자산] [자산vs전략] [자산vs포트폴리오] pill
- [x] `EquityChart.tsx` — Recharts AreaChart, multi-series, JEPI padding 회색 영역
- [x] `KpiCard.tsx` — 4종 KPI (최종자산/총수익/연환산/MDD), tabular-nums, 양음 색상
- [x] `InterpretCard.tsx` — 초보자 해석 문구 (템플릿 문자열)
- [x] `RiskCard.tsx` — 연도 MDD worst 강조 + 경고 톤
- [x] `IndicatorCard.tsx` — RSI/MACD/ATR 현재값 + 상태 라벨 (Q7-21)
- [x] `AssetPickerDrawer.tsx` — 탭별 universe 분기 (§6), 우측 슬라이드, 모바일 풀스크린
- [x] `TabA_SingleAsset.tsx` — replay API 호출 + EquityChart + KpiCard 렌더링
- [x] `TabB_AssetVsStrategy.tsx` — strategy API 호출 (Type A/B 선택 UI 포함)
- [x] `TabC_AssetVsPortfolio.tsx` — portfolio API 호출 + preset select
- [x] `CompareMainPage.tsx` — 공통 상태 (기간/적립금), 탭 전환, 컴포넌트 조합
- [x] verification/step-2-components.md 작성

### G2.1 — Tab A KPI 렌더링 (실제 API 연동)
- 명령: 브라우저에서 `/silver/compare` Tab A, QQQ/SPY/KS200, 10년, 100만원 설정 후 결과 확인
- Evidence: 데스크탑 스크린샷 → `verification/figures/step-2-tab-a-desktop.png`
- 통과 기준: EquityChart에 3개 시리즈 렌더링, KpiCard 3개 표시, QQQ final_asset_krw 양수

### G2.2 — Tab A KPI 값 정합성
- 명령: 브라우저 DevTools Network 탭 → replay POST 응답 JSON 확인
- Evidence: QQQ kpi.total_return 값 → step-2-components.md paste
- 통과 기준: `total_return` ≈ 2.84 (±5%), fixture `qqq_10y_replay_reference.json` 기준

### G2.3 — Tab B 전략 A 렌더링
- 명령: Tab B 탭 선택, QQQ 선택, 전략 A 선택 후 결과 확인
- Evidence: 스크린샷 → `verification/figures/step-2-tab-b.png`
- 통과 기준: 전략 A 결과 곡선 + replay 곡선 2개 시리즈 표시

### G2.4 — Tab C 포트폴리오 렌더링
- 명령: Tab C 탭, `qqqtltbtc` preset 선택 후 결과 확인
- Evidence: 스크린샷 → `verification/figures/step-2-tab-c.png`
- 통과 기준: 포트폴리오 KPI 카드 표시, 비중 편집 UI 없음

### G2.5 — JEPI padding 구간 시각화
- 명령: Tab A, JEPI 추가 선택 후 차트 확인
- Evidence: 스크린샷 (JEPI 시리즈 포함) → `verification/figures/step-2-jepi-padding.png`
- 통과 기준: JEPI padding 구간에 회색 영역 + "padding 구간" 라벨 표시

---

## P3-3 (M) — SignalDetailPage

**목표**: 기존 `IndicatorSignalPage.tsx`를 베이스로 단순화한 `/silver/signals` 페이지 신규 작성. Q7-21: RSI/MACD/ATR 개별 상태 라벨 방식 유지.

**핵심 lock**: D-21 (8종 자산), 성공률 탭 제거, "매수/매도 추천" 표현 금지.

### Sub-steps

- [x] `pages/silver/SignalDetailPage.tsx` 신규 작성 (IndicatorSignalPage에서 시작)
- [x] 자산 select: QQQ/SPY/KS200/NVDA/GOOGL/TSLA/005930/000660 (8종 고정)
- [x] 지표 탭: RSI / MACD / ATR (성공률 탭 제거)
- [x] 상태 라벨: "과매수 (RSI 74)", "골든크로스 (MACD)", "고변동성 (ATR)" 형식
- [x] 차트: 가격 라인 + 지표 overlay (기존 IndicatorOverlayChart 재사용)
- [x] verification/step-3-signals.md 작성

### G3.1 — SignalDetailPage 기본 렌더링
- 명령: 브라우저에서 `/silver/signals` 접속, QQQ 선택, RSI 탭
- Evidence: 스크린샷 → `verification/figures/step-3-signals-desktop.png`
- 통과 기준: 자산 select(8종), 지표 탭 3개, 가격+RSI 차트 렌더링

### G3.2 — 상태 라벨 표시
- 명령: RSI 탭에서 현재 RSI 값과 상태 라벨 확인
- Evidence: 스크린샷 클로즈업 → step-3-signals.md paste
- 통과 기준: 라벨이 "과매수" / "과매도" / "중립" 중 하나 표시, 구체적 수치 병기

### G3.3 — 성공률 탭 미노출
- 명령: SignalDetailPage 탭 목록 확인
- Evidence: 탭 목록 스크린샷 → step-3-signals.md paste
- 통과 기준: "성공률" 탭 없음, [RSI] [MACD] [ATR] 3개만 존재

---

## P3-4 (L) — 모바일 반응형 768px

**목표**: 768px 미만에서 모든 Silver 페이지가 가독성 있게 렌더링. Q6-20 (rev1 필수), silver-design.md §9 기준.

**핵심 lock**: nav 가로 스크롤(hamburger 미확정 → 시안 후 결정), KPI 1열, 차트 세로 스택, drawer 풀스크린.

### Sub-steps

- [x] `SilverLayout.tsx` 모바일 nav: 768px 미만 가로 스크롤 (overflow-x: auto)
- [x] `CommonInputPanel.tsx` 모바일: pill 그룹 줄바꿈 (flex-wrap: wrap)
- [x] KPI 그리드: `grid-cols-2` (데스크탑) → `grid-cols-1` (모바일)
- [x] `EquityChart.tsx`: `silver-equity-chart-wrap` div + CSS 280px/360px 반응형
- [x] `AssetPickerDrawer.tsx`: 768px 미만 `width: 100vw` 풀스크린
- [x] 전 Silver 페이지 모바일 검증
- [x] verification/step-4-mobile.md 작성

### G4.1 — 모바일 nav 가로 스크롤
- 명령: 브라우저 DevTools → 768px 뷰포트로 `/silver/compare` 접속
- Evidence: 모바일 스크린샷 → `verification/figures/step-4-mobile-nav.png`
- 통과 기준: nav 항목이 가로 스크롤로 접근 가능, 오버플로 hidden 없음

### G4.2 — KPI 카드 1열 렌더링
- 명령: 768px 뷰포트에서 Tab A KPI 영역 확인
- Evidence: 모바일 스크린샷 (KPI 영역 포함) → `verification/figures/step-4-mobile-kpi.png`
- 통과 기준: KPI 카드 4개가 1열로 세로 나열, 텍스트 잘림 없음

### G4.3 — Drawer 풀스크린 모달
- 명령: 768px 뷰포트에서 `+ 추가` 버튼 클릭
- Evidence: 모바일 drawer 스크린샷 → `verification/figures/step-4-mobile-drawer.png`
- 통과 기준: drawer가 `width: 100vw` 전체 화면, [추가] [취소] 버튼 접근 가능

### G4.4 — iPhone SE (375px) 최소폭 smoke test
- 명령: 375px 뷰포트에서 `/silver/compare` 접속
- Evidence: 스크린샷 → `verification/figures/step-4-iphonese.png`
- 통과 기준: 가로 스크롤바 없음 (x-overflow hidden), KPI 숫자 잘림 없음

---

## P3-5 (S) — AssetPickerDrawer 탭별 분기 검증

**목표**: AssetPickerDrawer가 현재 활성 탭(A/B/C)에 따라 정확한 universe를 제공하는지 E2E 검증.

### Sub-steps

- [x] Tab A에서 drawer 열기 → 6종 universe 확인 (QQQ/SPY/KS200/SCHD/JEPI/WBI)
- [x] Tab B에서 drawer 열기 → 3종 universe 확인 (QQQ/SPY/KS200)
- [x] Tab C에서 preset select → 4개 preset 표시 확인
- [x] Tab A 기본 선택 (QQQ/SPY/KS200 체크) 확인
- [x] verification/step-5-drawer.md 작성

### G5.1 — Tab A universe (6종)
- 명령: Tab A 탭 → `+ 추가` 클릭 → 체크박스 목록 확인
- Evidence: drawer 스크린샷 → `verification/figures/step-5-drawer-tab-a.png`
- 통과 기준: QQQ / SPY / KS200 / SCHD / JEPI / WBI 6종만 표시, NVDA 등 미표시

### G5.2 — Tab B universe (3종)
- 명령: Tab B 탭 → `+ 추가` 클릭 → 체크박스 목록 확인
- Evidence: drawer 스크린샷 → `verification/figures/step-5-drawer-tab-b.png`
- 통과 기준: QQQ / SPY / KS200 3종만 표시

### G5.3 — Tab C preset select (4개)
- 명령: Tab C 탭 → preset select 드롭다운 열기
- Evidence: preset 목록 스크린샷 → step-5-drawer.md paste
- 통과 기준: 4개 preset 표시 (`qqqtltbtc`, `ks200tltbtc`, `techblendtltbtc`, `samsungtltbtc`), 비중 편집 UI 없음

---

## 완료 기록

| 태스크 | 완료일 | commit hash |
|---|---|---|
| P3-1 | 2026-05-10 | `eb4c821` |
| P3-2 | 2026-05-10 | `22a5b89` |
| P3-3 | 2026-05-10 | `f64b9fa` |
| P3-4 | 2026-05-10 | `200f1c0` |
| P3-5 | 2026-05-10 | (다음 커밋) |

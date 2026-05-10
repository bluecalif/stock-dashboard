# Phase 3 Plan — 프론트엔드 신규 페이지
> Gen: silver
> Last Updated: 2026-05-10
> Status: Planning

---

## 1. Summary (개요)

**목적**: Phase 2에서 완성한 시뮬레이션 API를 소비하는 `/silver/compare` 페이지와 `/silver/signals` 페이지를 신규 작성. Bronze 라우트는 이 Phase에서 redirect만 추가하며 **코드 삭제는 Phase 4**에서 진행.

**범위**:
- `App.tsx` 라우트 재편 (Silver 라우트 추가 + Bronze redirect)
- `pages/silver/CompareMainPage.tsx` — 공통 입력 패널 + 3탭 구조
- `pages/silver/components/` — 11개 컴포넌트
- `pages/silver/SignalDetailPage.tsx` — IndicatorSignalPage 단순화 후신
- 모바일 반응형 768px (Q6-20)
- SilverLayout (상단 가로 nav, D-12)

**예상 결과물** (Phase 3 종료 시):
- `/silver/compare` 접속 → Tab A/B/C 동작, QQQ 10년 적립 KPI 렌더링
- `/silver/signals` 접속 → 8종 자산 RSI/MACD/ATR 조회
- Bronze 라우트 (`/`, `/prices`, `/correlation`, `/strategy`, `/indicators`) → `/silver/compare` redirect
- 모바일 768px 기준 반응형 레이아웃
- Bronze 기존 페이지는 아직 살아있음 (Phase 4에서 삭제)

---

## 2. Current State (Phase 2 인계)

- **API 계약 확정**: `POST /v1/silver/simulate/replay|strategy|portfolio`, `GET /v1/fx/usd-krw`
- **Railway prod DB**: 61 unit tests PASSED, QQQ 10년 KPI cross-check ✅
- **현재 App.tsx**: Bronze 6페이지 (Dashboard/Price/Correlation/Strategy/IndicatorSignal) + Chat
- **레이아웃**: `Layout.tsx` — 좌측 Sidebar + main영역. Silver는 상단 nav로 전환 필요
- **기존 재사용 후보**:
  - `IndicatorSignalPage.tsx` → `SignalDetailPage.tsx` 베이스
  - `ReturnsChart.tsx`, `PriceLineChart.tsx` → EquityChart에 Recharts 패턴 참고
  - `AssetSelect.tsx`, `DateRangePicker.tsx` → CommonInputPanel 참고
  - `store/authStore.ts`, `store/profileStore.ts`, `ProtectedRoute.tsx` — 그대로 유지

---

## 3. Target State (Phase 3 종료 시)

```
frontend/src/
├── App.tsx                          (Silver 라우트 추가 + Bronze redirect)
├── pages/silver/
│   ├── CompareMainPage.tsx
│   ├── SignalDetailPage.tsx
│   └── components/
│       ├── SilverLayout.tsx          (상단 가로 nav)
│       ├── CommonInputPanel.tsx       (기간/적립금 pill)
│       ├── TabNav.tsx
│       ├── TabA_SingleAsset.tsx
│       ├── TabB_AssetVsStrategy.tsx
│       ├── TabC_AssetVsPortfolio.tsx
│       ├── AssetPickerDrawer.tsx
│       ├── EquityChart.tsx
│       ├── KpiCard.tsx
│       ├── InterpretCard.tsx
│       ├── RiskCard.tsx
│       └── IndicatorCard.tsx
└── api/
    └── simulation.ts                 (API 클라이언트 함수 신규)
```

---

## 4. Implementation Stages

| Stage | 태스크 | 범위 | 의존성 |
|---|---|---|---|
| A | P3-1 | App.tsx 라우트 + SilverLayout | Phase 2 API 동작 |
| B | P3-2 | 11개 컴포넌트 + API 연동 | Stage A |
| C | P3-3 | SignalDetailPage | Stage A |
| D | P3-4 | 모바일 반응형 768px | Stage B/C |
| E | P3-5 | AssetPickerDrawer 동작 검증 | Stage B |

**병렬 가능**: Stage B와 C는 독립적으로 진행 가능.

---

## 5. Task Breakdown

| 태스크 | Size | 내용 |
|---|---|---|
| P3-1 | M | App.tsx 라우트 재편 + SilverLayout (상단 nav) |
| P3-2 | L | 11개 컴포넌트 + API 타입 + 시뮬레이션 API 클라이언트 |
| P3-3 | M | SignalDetailPage (8종 자산, RSI/MACD/ATR) |
| P3-4 | L | 모바일 768px (nav·차트·KPI·drawer 반응형) |
| P3-5 | S | AssetPickerDrawer 탭별 universe 검증 |

**합계**: 5개 (S:1 / M:2 / L:2)

---

## 6. Risks & Mitigation

| 리스크 | 영향 | 대응 |
|---|---|---|
| SilverLayout vs Bronze Layout 충돌 | 기존 Bronze 페이지 레이아웃 깨짐 | Silver 라우트만 SilverLayout 감싸기, Bronze는 기존 Layout 유지 |
| Recharts AreaChart 멀티 시리즈 성능 | 2500행 × 최대 6자산 = 15,000 포인트 | 다운샘플링 (monthly 또는 weekly tick) 고려, dot={false} 필수 |
| Tab A/B/C API 응답 스키마 불일치 | KPI 렌더링 오류 | `api/simulation.ts` 타입 정의 Phase 2 라우터와 1:1 맞추기 |
| AssetPickerDrawer 모바일 풀스크린 | iOS Safari 100vh 이슈 | `min-h-screen` → `min-h-[100dvh]` or `min-h-[-webkit-fill-available]` |
| IndicatorSignalPage 단순화 과정 기존 훅 의존 | 단순화 후 기존 Bronze 페이지 영향 | SignalDetailPage는 신규 파일로 분리, 기존 파일은 Phase 4까지 유지 |
| JEPI padding 구간 시각화 | 사용자 혼동 | `<ReferenceArea>` 회색 영역 + "padding 구간" 라벨 |

---

## 7. Dependencies

**내부 코드 의존성**:
- `frontend/src/api/` — `prices.ts`, `factors.ts`, `analysis.ts` 패턴 참고 → `simulation.ts` 신규
- `frontend/src/store/authStore.ts` — ProtectedRoute 그대로 사용
- `frontend/src/components/common/AssetSelect.tsx` — AssetPickerDrawer UI 패턴 참고
- `backend/api/routers/simulation.py` — 응답 스키마 확인 필수

**외부 라이브러리**:
- Recharts ≥ 2.x (`AreaChart`, `defs`, `linearGradient`) — 기존 설치됨
- react-router-dom — `NavLink`, `Navigate` 사용
- Tailwind CSS — 다크 토큰 클래스

**디자인 레퍼런스**:
- `.claude/skills/frontend-dev/references/silver-design.md` — 디자인 토큰 + 컴포넌트 레시피
- `docs/UX-design-ref.JPG` — 다크 네이비 시각 레퍼런스
- `docs/silver-masterplan.md` §4, §6 — IA 와이어프레임 + 컴포넌트 명세

---

## 8. DoD (Definition of Done)

- [x] (아직 없음)
- [ ] `/silver/compare` 진입 → Tab A 기본 렌더링 (QQQ/SPY/KS200 3종, 10년, 100만)
- [ ] Tab A/B/C 전환 및 각 탭 API 호출 + KPI 카드 표시
- [ ] Bronze 라우트 → `/silver/compare` redirect 동작
- [ ] `/silver/signals` → 8종 자산 select + RSI/MACD/ATR 차트
- [ ] 모바일 768px — nav/차트/KPI 반응형 확인
- [ ] AssetPickerDrawer — Tab A 6종, Tab B 3종, Tab C preset 분기
- [ ] verification/ evidence 5종 + PNG (UI screenshot) 누적
- [ ] `project-overall-tasks.md` Phase 3 섹션 동기화

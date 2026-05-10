# Session Compact

> Generated: 2026-05-10
> Source: /compact-and-go

## Goal

Silver gen Phase 3 — P3-2 verification 완료 + P3-3 SignalDetailPage 구현 시작.

## Completed

- [x] **TabC preset 키 수정 커밋** (`f5870fd`): `qqqtltbtc` → `QQQ_TLT_BTC` 등 4개
- [x] **CORS 해결**: Puppeteer `--disable-web-security` + `--user-data-dir` 플래그 추가
- [x] **KS200 NaN 버그 수정** (`ee46fc9`): `replay.py`에 `.dropna()` 추가
  - 원인: FDR이 한국 공휴일(2016-12-26 등)에 `close=NaN` 행 삽입 → JSON 직렬화 500
  - 미국 자산은 공휴일 날짜 행 자체가 없어 NaN 없음
- [x] **P3-2 verification evidence 확정** (`ee46fc9`):
  - `verification/figures/` 스크린샷 8개
  - `verification/step-2-components.md` 전 게이트(G2.1~G2.5) PASS
- [x] **tasks.md P3-2 완료 처리** (`22a5b89`): Status 2/5
- [x] **IceBreakingModal 모달 문제 수정** (`473a624`):
  - 원인: `profile.onboarding_completed=false` → 매 페이지 진입마다 재등장, Escape 무효
  - 수정: 토큰 획득 후 `POST /v1/profile/ice-breaking` 선호출로 사전 완료
- [x] **탭 스크린샷 중복 문제 수정** (`473a624`):
  - 원인: `waitForSelector(".silver-chart-card")`가 이전 탭 카드 즉시 감지
  - 수정: `waitForFunction`으로 loading 소멸 + chart 출현까지 폴링
- [x] **e2e-verify 스킬 생성** (`91dc0c4`): curl + Puppeteer 통합 검증 워크플로우
  - 온보딩 사전완료 패턴, waitForFunction 탭 대기 패턴 포함

## Current State

- **Phase 3 진행 중** (2/5 완료)
- 서버: 백엔드 PID 17614 (port 8000), 프론트 npm run dev (port 5173)
- 최근 커밋: `473a624` (검증 스크린샷 수정 + e2e-verify 스킬)

### P3-3 분석 완료 (구현 미착수)

기존 파일 확인 완료:
- `pages/silver/SignalDetailPage.tsx` — 현재 플레이스홀더만 있음 (구현 필요)
- `pages/IndicatorSignalPage.tsx` — 참고 베이스 (성공률 탭 포함, Bronze 스타일)
- `components/charts/IndicatorOverlayChart.tsx` — 재사용 가능, Props: `{prices, factors, assetId, selectedFactors, signalDates, indicatorId}`
- `pages/silver/components/IndicatorCard.tsx` — 재사용 가능, Props: `{assetLabel, indicators[]}`

### P3-3 핵심 스펙

- **자산 select**: QQQ / SPY / KS200 / NVDA / GOOGL / TSLA / 005930 / 000660 (8종 고정)
- **지표 탭**: [RSI] [MACD] [ATR] 3개만 (성공률 탭 제거, "매수/매도 추천" 표현 금지)
- **상태 라벨 형식**: "과매수 (RSI 74)", "골든크로스 (MACD)", "고변동성 (ATR)"
- **차트**: `IndicatorOverlayChart` 재사용 (가격 라인 + 지표 overlay)
- **Silver 다크 톤**: CSS var 기반 (`--bg-card`, `--text-primary` 등)

### Indicator Factor 매핑 (IndicatorSignalPage에서 확인)

```
rsi_14: ["rsi_14"]
macd:   ["macd", "macd_signal"]
atr_vol: ["atr_14", "vol_20"]
```

### 상태 라벨 계산 로직

- RSI > 70 → "과매수", RSI < 30 → "과매도", else → "중립"
- MACD 히스토그램 양(+)전환 → "골든크로스", 음(-)전환 → "데드크로스"
- ATR/가격 > 3% → "고변동성"

### API 엔드포인트

- 가격: `GET /v1/prices/daily?asset_id=&start_date=&end_date=&limit=`
- 팩터: `GET /v1/factors?asset_id=&factor_name=&start_date=&end_date=&limit=`
- 시그널: `fetchIndicatorSignals({asset_id, indicator_id, start_date, end_date})`

## Remaining / TODO

### ~~P3-3 (M) — SignalDetailPage 구현~~ ✅ 완료 (2026-05-10)

- [x] `pages/silver/SignalDetailPage.tsx` 구현 완료
- [x] `verification/step-3-signals.md` 작성 (G3.1~G3.3 PASS)
- [x] QQQ/SPY/NVDA/GOOGL/TSLA 팩터 데이터 생성 (`run_research.py`)

### P3-4 (L) — 모바일 반응형 768px

- [ ] `SilverLayout.tsx` 모바일 nav: `overflow-x: auto`
- [ ] `CommonInputPanel.tsx` 모바일 pill 줄바꿈
- [ ] KPI 그리드: 데스크탑 2열 → 모바일 1열
- [ ] `EquityChart.tsx`: 모바일 280px, 데스크탑 360px
- [ ] `AssetPickerDrawer.tsx`: 768px 미만 `width: 100vw`

### P3-5 (S) — AssetPickerDrawer E2E 검증

## Key Decisions

- **KS200 NaN**: `.dropna()` 추가 위치 — `_load_price_series` 직후 (strategy/portfolio 엔진은 별도 검토 필요)
- **Puppeteer CORS**: `--disable-web-security` (테스트 전용) — vite proxy 수정 거부 이력 유지
- **온보딩 모달**: API 선호출로 완료 처리 — localStorage 조작이나 Escape보다 안정적
- **탭 대기**: `waitForFunction` 폴링 — `waitForSelector`는 이전 탭 DOM 즉시 감지로 부적합

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 핵심 참조

- `dev/active/silver-rev1-phase3/silver-rev1-phase3-tasks.md` — P3-3 게이트 (G3.1~G3.3)
- `frontend/src/pages/IndicatorSignalPage.tsx` — 참고 베이스 (재사용 로직 포함)
- `frontend/src/components/charts/IndicatorOverlayChart.tsx` — 재사용 차트 컴포넌트
- `frontend/src/pages/silver/components/IndicatorCard.tsx` — 재사용 상태 카드
- `.claude/skills/frontend-dev/references/silver-design.md` — Silver 디자인 토큰
- `/tmp/pw_test/verify-p3-2.cjs` — Puppeteer 검증 스크립트 (P3-3용으로 확장 필요)

### 환경

- 백엔드: `uvicorn api.main:app --port 8000` (실행 중)
- 프론트: `npm run dev` (port 5173)
- 테스트 계정: `verify@silver.dev` / `silver2026`
- 커밋 형식: `[silver-rev1-phase3] P3-N: description`

### 주의사항

- `fetchIndicatorAccuracy`, `fetchIndicatorComparisonV2` — P3-3에서 사용 금지 (성공률 탭 제거)
- "매수/매도 추천" 표현 금지 (D-21)
- 지표 탭은 [RSI] [MACD] [ATR] 3개만
- 상태 라벨에 구체적 수치 병기 필수: "과매수 (RSI 74)"

## Next Action

### P3-3 SignalDetailPage 구현

`frontend/src/pages/silver/SignalDetailPage.tsx`를 다음 스펙으로 작성:

```
1. 자산 드롭다운 (8종): Silver 다크 스타일 <select>
2. 지표 탭 (Silver TabNav 패턴): [RSI] [MACD] [ATR]
3. IndicatorCard: 현재 지표값 + 상태 라벨 (최신 factor 데이터 기반)
4. IndicatorOverlayChart: 1년 가격 + 지표 overlay
5. 로딩/에러 처리
6. 성공률 탭 완전 제거
```

데이터 흐름:
- 자산 선택 or 탭 변경 → `fetchPrices` + `fetchFactors` 병렬 호출
- 최신 factor 값으로 상태 라벨 계산 → IndicatorCard 렌더
- 전체 factor 데이터 → IndicatorOverlayChart

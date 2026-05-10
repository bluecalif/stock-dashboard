# Session Compact

> Generated: 2026-05-10
> Source: /compact-and-go

## Goal

Silver gen Phase 2 마무리 커밋 + tasks.md 동기화 + project-overall 갱신. ✅ **완료**

## Completed

- [x] **Phase 2 전체 구현** (P2-1 ~ P2-7): simulation 패키지 8파일 + API 레이어 + 61 tests PASSED
- [x] **step-7-crosscheck.md** 작성 (QQQ 10년 DCA cross-check, G7.1~G7.3 PASS)

## Current State

- **step-7-crosscheck.md**: `dev/active/silver-rev1-phase2/verification/step-7-crosscheck.md` 존재, **미커밋**
- **fixtures/**: `dev/active/silver-rev1-phase2/verification/fixtures/` **디렉토리 없음** (이전 세션에서 생성 시도했으나 context clear로 소실)
- **61 unit tests**: PASSED (fx 7 + mdd 8 + replay 10 + strategy 13 + portfolio 7 + padding 8 + wbi 8)
- **Railway prod DB**: asset_master 15행, price_daily 37,671행, fx_daily 2,603행
- **alembic head**: `d8334483342c`

### QQQ 10년 DCA KPI (verified via API)

| 지표 | 값 |
|---|---|
| 기간 | 2016-05-10 ~ 2026-05-08 |
| curve rows | 2,514 |
| 총 원금 | 121,000,000원 (121회 × 1,000,000) |
| 최종 자산 | 464,625,184원 |
| 총 수익률 | +283.99% |
| 연환산 수익률 | +14.40% |
| worst MDD | -26.24% (2020 COVID) |
| 2022 MDD | -24.62% |

### 연도별 MDD (QQQ 10년 DCA)

| 연도 | MDD |
|---|---|
| 2016 | -9.34% |
| 2017 | -5.07% |
| 2018 | -18.48% |
| 2019 | -8.06% |
| 2020 | -26.24% |
| 2021 | -8.39% |
| 2022 | -24.62% |
| 2023 | -7.27% |
| 2024 | -14.05% |
| 2025 | -20.62% |
| 2026 | -7.15% |

### 커밋 이력

| 해시 | 내용 |
|---|---|
| `f7d5f3e` | P2-1 + P2-2: simulation exports + fx.py + mdd.py + 15 tests |
| `1ff60f1` | P2-3: replay.py + 10 tests + QQQ 10Y curve PNG |
| `350376d` | P2-4: strategy_a + strategy_b + portfolio + 20 tests + lock cycle PNG |
| `a666f2d` | P2-5 + P2-6: simulation + fx API 라우터 등록 |

## Remaining / TODO

### ✅ 즉시 처리 (완료)

1. ~~fixtures/ 디렉토리 + JSON 생성~~ ✅ `1f7e426`
2. ~~P2-7 커밋~~ ✅ `1f7e426`
3. ~~tasks.md 업데이트 (P2-1~P2-7 완료 표시)~~ ✅
4. ~~project-overall 동기화~~ ✅

### Phase 3 (다음 세션)

- [ ] 프론트엔드 `/silver/compare` 페이지
  - `CompareMainPage.tsx`, `TabA_SingleAsset.tsx`, `KpiCard.tsx`, `EquityChart.tsx`, `AssetPickerDrawer.tsx`
  - `TabB_AssetVsStrategy.tsx`, `TabC_AssetVsPortfolio.tsx`
  - `SignalDetailPage.tsx`
  - 모바일 반응형 768px

## Key Decisions

- **fixtures/ 소실 원인**: 이전 세션 context clear 시 생성 전에 소실. 다음 세션에서 Write 툴로 직접 JSON 파일 생성 필요
- **fixture JSON 구조**: KPI 숫자값 + 연도별 MDD dict 포함 (cross-check 기준값)
- **fx.py API**: calendar-day forward-fill 반환
- **replay_core()**: DB 의존성 없는 순수 함수
- **simulation_service.py**: strategy 루프 직접 구현

## Context

### 핵심 참조 파일

1. `dev/active/silver-rev1-phase2/silver-rev1-phase2-tasks.md` — P2-1~P2-7 상세 게이트
2. `docs/silver-masterplan.md` §4, §6 — Phase 3 프론트엔드 명세
3. `backend/research_engine/simulation/` — Phase 2 완성 패키지
4. `backend/api/routers/simulation.py` — `/v1/silver/simulate/*` 엔드포인트

### 환경

- Railway prod DB (단일, staging 없음)
- pytest: `backend/tests/unit/` 위치
- 서버: `uvicorn api.main:app --port 8000` (backend/ 에서 실행)
- 커밋 형식: `[silver-rev1-phase2] Step X.Y: description`
- Git Bash: `/c/Users/User/Projects-2026/active/stock-dashboard`

## Next Action

### Step 1: fixtures JSON 생성 (Write 툴 사용)

파일 경로: `C:\Users\User\Projects-2026\active\stock-dashboard\dev\active\silver-rev1-phase2\verification\fixtures\qqq_10y_replay_reference.json`

내용:
```json
{
  "asset_code": "QQQ",
  "period_years": 10,
  "monthly_amount_krw": 1000000,
  "period_start": "2016-05-10",
  "period_end": "2026-05-08",
  "curve_rows": 2514,
  "total_deposit_krw": 121000000,
  "final_asset_krw": 464625184,
  "total_return": 2.8399,
  "annualized_return": 0.1440,
  "yearly_worst_mdd": -0.2624,
  "yearly_mdd": {
    "2016": -0.0934,
    "2017": -0.0507,
    "2018": -0.1848,
    "2019": -0.0806,
    "2020": -0.2624,
    "2021": -0.0839,
    "2022": -0.2462,
    "2023": -0.0727,
    "2024": -0.1405,
    "2025": -0.2062,
    "2026": -0.0715
  }
}
```

### Step 2: P2-7 커밋

```bash
git -C /c/Users/User/Projects-2026/active/stock-dashboard add "dev/active/silver-rev1-phase2/verification/step-7-crosscheck.md"
git -C /c/Users/User/Projects-2026/active/stock-dashboard add "dev/active/silver-rev1-phase2/verification/fixtures/"
git -C /c/Users/User/Projects-2026/active/stock-dashboard commit -m "[silver-rev1-phase2] P2-7: QQQ cross-check verification + fixture"
```

### Step 3: tasks.md P2-1~P2-7 체크박스 flip

`dev/active/silver-rev1-phase2/silver-rev1-phase2-tasks.md` 읽고 P2-1~P2-7 완료 표시

### Step 4: /step-update --sync-overall

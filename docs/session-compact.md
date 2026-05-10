# Session Compact

> Generated: 2026-05-10
> Source: /compact-and-go

## Goal

Silver gen Phase 4 빅뱅 Cut-over 실행 및 prod 버그 수정.
P4-1~P4-6 완료, P4-7 (1주 monitoring) 진행 중.

## Completed

- [x] **P4-1**: `git tag v-bronze-final` → `9461d8c` (rollback 앵커)
- [x] **P4-2**: App.tsx Bronze import/라우트 완전 제거 (7개 경로 → /silver/compare)
- [x] **P4-3**: Bronze 페이지 7종 삭제 (Dashboard/Price/Correlation/Strategy/IndicatorSignal/Factor/Signal)
- [x] **P4-4**: `routers/backtests.py` 삭제 + Alembic DROP migration `c9b884d01cb4` (backtest_* 3테이블)
- [x] **P4-5**: `simulation_tools.py` 신규 (replay/strategy/portfolio) + data_fetcher 정리
- [x] **P4-6**: CI `2d66c8c` PASS → Railway + Vercel 자동 배포 → prod smoke test G6.1~G6.4 PASS
- [x] **prod 버그 수정 3종** (`8fc9013`, `1d82073`):
  - WBI 배열 길이 불일치: `pd.date_range` 먼저 생성 후 `len()` 기준 맞춤
  - KS200 전략 화이트 스크린: `_load_price_and_fx`에 `r.close is not None` 필터 + `.dropna()`
  - WBI CAGR 5.63%→19.95%: zero-mean 노이즈 + drift 재스케일링 + fixture 재생성
- [x] **step-update --sync-overall** (2회): Phase docs + project-overall 동기화, debug-history 3종 버그 기록
- [x] **dev-docs**: silver-rev1-phase4 생성 (plan/context/tasks/verification)
- [x] **CI 수정** (4회): lint 71개 + backtest 테스트 삭제 + Silver gen 기준 테스트 수정

## Current State

- **Phase 4 진행률**: 6/7 (P4-7 monitoring 진행 중, 완료 목표 2026-05-17)
- **Project 진행률**: 24/29 (Phase 1~3 ✅, Phase 4 🟡 6/7)
- **최신 커밋**: `b16dc68` (step-update debug-history)
- **Branch**: master
- **Prod URLs**:
  - Backend: `https://backend-production-e5bc.up.railway.app`
  - Frontend: `https://stock-dashboard-alpha-lilac.vercel.app`

### Changed Files (이번 세션)

**P4-2~P4-5 코드 변경**:
- `frontend/src/App.tsx` — Bronze import/라우트 제거
- `frontend/src/pages/` — DashboardPage/PricePage/CorrelationPage/StrategyPage/IndicatorSignalPage/FactorPage/SignalPage 삭제
- `backend/api/main.py` — backtests 라우터 제거
- `backend/api/routers/backtests.py` — 삭제
- `backend/db/alembic/versions/c9b884d01cb4_drop_backtest_tables.py` — 신규 DROP migration
- `backend/api/services/llm/simulation_tools.py` — 신규 (Agentic 3종 tool)
- `backend/api/services/llm/agentic/data_fetcher.py` — list_backtests/backtest_strategy 제거, simulation_* 추가

**Prod 버그 수정**:
- `backend/research_engine/simulation/replay.py` — WBI 배열 불일치 수정
- `backend/api/services/simulation_service.py` — _load_price_and_fx NaN 필터 추가
- `backend/research_engine/simulation/wbi.py` — drift 재스케일링 (20% CAGR 보장)
- `backend/research_engine/simulation/fixtures/wbi_seed42_10y.npz` — fixture 재생성

**CI 수정**:
- `backend/pyproject.toml` — per-file-ignores 추가
- `backend/tests/unit/test_api/test_backtests.py` — 삭제
- `backend/tests/unit/test_agentic_data_fetcher.py` — backtest 테스트 → simulation 테스트 교체
- `backend/tests/unit/test_api/test_edge_cases.py` — backtest edge case 제거
- `backend/tests/unit/test_fdr_client.py` — 7종 → 15종
- `backend/tests/unit/test_ingest.py` — 7→15, 6→14

## Remaining / TODO

### P4-7 (S) — 1주 monitoring (2026-05-17까지)

- [ ] CI `1d82073` (WBI fix) 통과 여부 확인 → Railway 배포 완료
- [ ] prod WBI 시뮬레이션 정상 동작 확인 (annualized ≈10%)
- [ ] prod KS200 전략 Tab B 화이트 스크린 해결 확인
- [ ] simulation API P95 latency 측정 (10회 호출 → 평균/P95)
- [ ] price_daily 일일 갱신 정상 확인
- [ ] `verification/step-7-monitoring.md` 작성
- [ ] Phase 4 완전 완료 → step-update

### Phase 5 (S) — 후속 안정화 (P4-7 완료 후)

- P5-1: 사용자 피드백 수집
- P5-2: 배당락 데이터 도입 검토
- P5-3: simulation API 캐시 도입 검토 (P95 > 5초 시)
- P5-4: alerting 신규 8종 확장

## Key Decisions

- **D-P4-4**: WBI GBM은 기대값이 아닌 정확한 CAGR 달성 보장 (drift 재스케일링)
- **D-P4-5**: `_load_price_and_fx`에서 price NaN 필터링 필수
- **D-P4-6**: DCA annualized (≈10%) < 자산 CAGR (20%) = DCA 특성상 정상 (평균 투자 기간 ≈ period/2)
- **simulation_tools.py**: HTTP 경유 없이 `simulation_service` 직접 import (A-004 교훈)
- **DB 단일 구조**: 로컬 DB 없음, Railway 원격 DB 직접 연결 → alembic upgrade = prod 즉시 적용

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 환경

- 백엔드: `uvicorn api.main:app --port 8000` (종료 후 재시작 필요)
- 프론트: `npm run dev` (port 5173)
- 커밋 형식: `[silver-rev1-phase4] P4-N: description`
- Railway prod: `backend-production-e5bc.up.railway.app`
- Vercel prod: `stock-dashboard-alpha-lilac.vercel.app`
- test 계정: `verify@silver.dev` / `silver2026`

### 핵심 참조

- `dev/active/silver-rev1-phase4/silver-rev1-phase4-tasks.md` — P4-7 게이트 (G7.1~G7.2)
- `dev/active/silver-rev1-phase4/verification/` — P4-1~P4-6 evidence
- `dev/active/project-overall/project-overall-tasks.md` — 24/29 진행률

### 주의사항

- `backtests.py`는 이미 삭제됨 → git status에 `D backend/api/routers/backtests.py` 표시는 정상
- prod DB는 Railway 단일 DB → alembic upgrade가 즉시 prod에 적용됨
- WBI DCA annualized ≈10%는 버그가 아님 (DCA 특성)

## Next Action

### P4-7 monitoring 완료 및 Phase 4 종료

1. CI `1d82073` 통과 확인:
   ```bash
   gh run list --repo bluecalif/stock-dashboard --limit 3
   ```

2. Prod 최종 확인 (Puppeteer):
   ```
   - /silver/compare Tab A: WBI 추가 → 정상 시뮬레이션
   - /silver/compare Tab B: KS200 → 화이트 스크린 없음
   - simulation API latency 10회 측정
   ```

3. `verification/step-7-monitoring.md` 작성 후 `/step-update`

4. Phase 5 착수 여부 결정 (P5-3 latency 임계 초과 시 캐시 도입 우선)

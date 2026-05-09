# Project Overall Tasks — Silver Gen
> Gen: silver
> Last Updated: 2026-05-09
> Status: In Progress (Phase 1 완료 — 6/29)

## Summary

| Phase | 폴더 | 태스크 수 | Size 분포 | 상태 |
|---|---|---|---|---|
| Phase 1 | `silver-rev1-phase1` | 6 | S:2 / M:3 / L:1 | ✅ 완료 (6/6, last: `391f27f`) |
| Phase 2 | `silver-rev1-phase2` | 7 | S:1 / M:3 / L:2 / XL:1 | 미착수 |
| Phase 3 | `silver-rev1-phase3` | 5 | S:1 / M:2 / L:2 | 미착수 |
| Phase 4 | `silver-rev1-phase4` | 7 | S:3 / M:3 / L:1 | 미착수 |
| Phase 5 | `silver-rev1-phase5` | 4 | S:3 / M:1 | 미착수 |
| **합계** | — | **29** | S:10 / M:12 / L:6 / XL:1 | 6/29 |

> 각 Phase 상세 태스크는 해당 Phase 폴더의 `-tasks.md`에 commit hash 포함하여 추적. 본 파일은 Phase 단위 요약만.

### "Show, don't claim" 정책 (전 Phase 공통)

> 출처: project-overall-context.md §0. Phase dev-docs 작성 시 다음을 반드시 반영.

1. **모든 검증 게이트 = 3단 형식** — 명령 / Evidence 형식 / 통과 기준
2. **`verification/step-N-<topic>.md` 작성**을 step별 sub-step으로 의무화
3. **수치·시계열·분포 step = PNG 의무** — `verification/figures/<step>-<topic>.png`
4. **체크 표시 권한** — evidence paste + 사용자 노출 후에만 가능. Claude의 PASS 주장만으로는 금지

위 4항목이 누락된 Phase dev-docs는 정합성 검증 FAIL — 작성/리뷰 시 차단.

---

## Phase 1 — 데이터 인프라 ✅ 완료

상세: `dev/active/silver-rev1-phase1/silver-rev1-phase1-tasks.md`
Evidence: `dev/active/silver-rev1-phase1/verification/` (6 파일 + 3 PNG)

- [x] **P1-1 (M)** Alembic migration `d8334483342c` — `asset_master` 5컬럼 + `fx_daily` → `7d457a2`
- [x] **P1-2 (S)** SYMBOL_MAP 15종 (8 신규 추가, JEPI D-1) → `0eea282`
- [x] **P1-3 (M)** `fx_collector.py` USD/KRW 일봉 UPSERT → `ba574c0`
- [x] **P1-4 (L)** `seed_silver_assets.py` 15행 + 37,671행 backfill (15자산 10년) + fx_daily 2,603행 → `7d24d68` + `63ecb80`
- [x] **P1-5 (M)** `padding.py` cyclic+reverse-cumprod + JEPI fixture + 8 tests PASSED → `391f27f`
- [x] **P1-6 (S)** `wbi.py` (Warren Buffett Index) GBM seed=42 + fixture + 8 tests PASSED → `391f27f`

버그 수정: `fdr_client.py` volume int32 overflow(`astype(int64)`) + BTC high/low swap

---

## Phase 2 — 시뮬레이션 엔진 (Bronze 영향 0)

진입 조건: ✅ Phase 1 완료 → **`/dev-docs create phase 2 silver-rev1-phase2`로 시작**

- [ ] **P2-1 (S)** `backend/research_engine/simulation/` 디렉터리 + `__init__.py`
- [ ] **P2-2 (M)** `padding.py` (cyclic returns) + `wbi.py` (GBM 시드 42) + `fx.py` (USD↔KRW forward-fill) + `mdd.py` (캘린더 연도) — utility 4종
- [ ] **P2-3 (L)** `replay.py` — 적립식 replay (Tab A), 매월 첫 거래일 적립 + 배당 매일 재투자 + USD fractional 매수
- [ ] **P2-4 (XL)** `strategy_a.py` — lock 사이클 (강제 재매수 365일, lock_until_year, grace 12개월, 60거래일 ratio ≥1.20 trigger) + `strategy_b.py` (70% 정기 + 30% 대기, 20거래일 -10% 또는 12월 강제) + `portfolio.py` (60/20/20 + 연 1회 리밸런싱)
- [ ] **P2-5 (M)** `routers/simulation.py` — `POST /v1/silver/simulate/{replay,strategy,portfolio}` (Pydantic schema, FastAPI DI)
- [ ] **P2-6 (M)** `routers/fx.py` — `GET /v1/fx/usd-krw`
- [ ] **P2-7 (L)** integration test + cross-check fixture — QQQ 10년 적립 결과를 Portfoliovisualizer/curvo 외부 도구와 ±2% 일치 검증

검증: KPI 4종 산출, lock 사이클 unit test, grace period, 자산별 캘린더 forward-fill.

---

## Phase 3 — 프론트엔드 (Bronze와 병행 운영)

진입 조건: Phase 2 API 계약 확정 + `dev/active/silver-rev1-phase3/` 작성

- [ ] **P3-1 (M)** `pages/silver/CompareMainPage.tsx` + 라우트 등록 (`/silver/compare`)
- [ ] **P3-2 (L)** `components/` 10개 — CommonInputPanel / TabNav / TabA_SingleAsset / TabB_AssetVsStrategy / TabC_AssetVsPortfolio / AssetPickerDrawer / EquityChart / KpiCard / InterpretCard / RiskCard / IndicatorCard
- [ ] **P3-3 (M)** `SignalDetailPage.tsx` (`/silver/signals`) — IndicatorSignalPage 단순화 후신, 8종 자산 select + RSI/MACD/ATR
- [ ] **P3-4 (L)** 모바일 반응형 — 768px breakpoint, 차트 세로 스택, KPI 1열, drawer 풀스크린 모달, nav 가로 스크롤 (vs hamburger 결정)
- [ ] **P3-5 (S)** AssetPickerDrawer 동작 — 6종 (Tab A) / 3종 (Tab B) / preset (Tab C) 분기

검증: UI 흐름, 모바일 768px, drawer 동작, EquityChart multi-series 색 구분.

---

## Phase 4 — 빅뱅 cut-over (다운타임 수 분)

진입 조건: Phase 1~3 staging 검증 완료 + T-7d 백엔드 / T-3d 프론트 / T-1d DB 백업

- [ ] **P4-1 (S)** git tag `v-bronze-final` 생성 (master 직전 상태 보존)
- [ ] **P4-2 (M)** Bronze 라우트 → `/silver/compare` redirect 적용 (`App.tsx`)
- [ ] **P4-3 (M)** StrategyPage / DashboardPage / PricePage / CorrelationPage 코드 삭제
- [ ] **P4-4 (S)** `routers/backtests.py` 제거 + `backtest_*` 3 테이블 DROP migration
- [ ] **P4-5 (M)** Agentic tool registration 정리 (strategy_classify/report 제거 + simulation_replay/strategy/portfolio 등록)
- [ ] **P4-6 (L)** master merge + prod 빅뱅 배포 + smoke test (`/silver/compare` 노출, KPI 산출, Agentic chat tool 호출)
- [ ] **P4-7 (S)** 1주 monitoring (Agentic chat tool, simulation API P95 latency, 사용자 피드백)

검증: 라우트 redirect 일관, Agentic AI tool fallback 동작, KPI 정합 (Phase 2 fixture와 일치).

---

## Phase 5 — 후속 안정화

진입 조건: Phase 4 monitoring 1주 완료

- [ ] **P5-1 (S)** 사용자(본인) 피드백 수집 — Tab A/B/C 흐름, 모바일, 차트 가독성
- [ ] **P5-2 (M)** 실제 배당락 데이터 도입 검토 (vs 공시 균등 분할) — 우선순위 평가
- [ ] **P5-3 (S)** 시뮬레이션 결과 캐시 도입 검토 — P95 latency 임계 측정 후 결정
- [ ] **P5-4 (S)** 데이터 alerting 신규 8종 자산 확장 (`alerting.py`)

검증: 안정화 완료 시점에 후속 Gen(gold) 진입 여부 결정.

---

## 미해결 후속 결정 (Phase 진행 중 발생 시 별도 추적)

마스터플랜 §11.3 (project-overall-context.md §5에서 동일 추적):
- C-2 fractional 정밀도 자릿수 (Phase 2)
- C-4 신호 빈도 "3회/년" 폐기 (Phase 3)
- Tab A 캘린더 정렬 (Phase 3)
- 카드형 vs step형 (Phase 3)
- 모바일 nav 동작 (Phase 3)

---

**다음 작업**: Phase 1 코딩 착수 — P1-1 (Alembic migration). 상세는 `dev/active/silver-rev1-phase1/silver-rev1-phase1-tasks.md` 참조.

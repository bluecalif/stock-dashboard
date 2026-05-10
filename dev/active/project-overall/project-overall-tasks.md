# Project Overall Tasks — Silver Gen
> Gen: silver
> Last Updated: 2026-05-10
> Last Updated: 2026-05-10
> Status: In Progress (Phase 1 ✅ 완료, Phase 2 ✅ 완료, Phase 3 ✅ 완료 — 18/29)

## Summary

| Phase | 폴더 | 태스크 수 | Size 분포 | 상태 |
|---|---|---|---|---|
| Phase 1 | `silver-rev1-phase1` | 6 | S:2 / M:3 / L:1 | ✅ 완료 (6/6, last: `391f27f`) |
| Phase 2 | `silver-rev1-phase2` | 7 | S:1 / M:3 / L:2 / XL:1 | ✅ 완료 (7/7, last: `1f7e426`) |
| Phase 3 | `silver-rev1-phase3` | 5 | S:1 / M:2 / L:2 | ✅ 완료 (5/5, last: `80a23de`) |
| Phase 4 | `silver-rev1-phase4` | 7 | S:3 / M:3 / L:1 | 미착수 |
| Phase 5 | `silver-rev1-phase5` | 4 | S:3 / M:1 | 미착수 |
| **합계** | — | **29** | S:10 / M:12 / L:6 / XL:1 | 13/29 |

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

## Phase 2 — 시뮬레이션 엔진 (Bronze 영향 0) ✅ 완료

진입 조건: ✅ Phase 1 완료 + ✅ dev-docs 작성 완료 (2026-05-10)
완료일: 2026-05-10 | 61 unit tests PASSED

상세: `dev/active/silver-rev1-phase2/silver-rev1-phase2-tasks.md`

- [x] **P2-1 (S)** `simulation/` 디렉터리 구조 확인 + `__init__.py` exports 정비 — `f7d5f3e`
- [x] **P2-2 (M)** `fx.py` (USD↔KRW forward-fill) + `mdd.py` (캘린더 연도) — `f7d5f3e`
- [x] **P2-3 (L)** `replay.py` — 적립식 replay (Tab A), 매월 첫 거래일 적립 + 배당 매일 재투자 + USD fractional 매수 — `1ff60f1`
- [x] **P2-4 (XL)** `strategy_a.py` + `strategy_b.py` + `portfolio.py` (60/20/20 + 연 1회 리밸런싱) — `350376d`
- [x] **P2-5 (M)** `routers/simulation.py` — `POST /v1/silver/simulate/{replay,strategy,portfolio}` — `a666f2d`
- [x] **P2-6 (M)** `routers/fx.py` — `GET /v1/fx/usd-krw` — `a666f2d`
- [x] **P2-7 (L)** QQQ 10년 cross-check fixture (총수익률 +283.99%, 연환산 +14.40%, worst MDD -26.24%) — `1f7e426`

검증: KPI 4종 산출, lock 사이클 unit test, grace period, 자산별 캘린더 forward-fill. ✅ 전부 PASS

---

## Phase 3 — 프론트엔드 (Bronze와 병행 운영) ✅ 완료

진입 조건: ✅ Phase 2 API 계약 확정 + ✅ dev-docs 작성 완료 (2026-05-10)
완료일: 2026-05-10 | 5/5 태스크 완료

상세: `dev/active/silver-rev1-phase3/silver-rev1-phase3-tasks.md`

- [x] **P3-1 (M)** `App.tsx` 라우트 재편 + `SilverLayout` (상단 가로 nav) + `/silver/compare` 등록 → `eb4c821`
- [x] **P3-2 (L)** `pages/silver/components/` 11개 컴포넌트 + `api/simulation.ts` → `22a5b89`
- [x] **P3-3 (M)** `SignalDetailPage.tsx` (`/silver/signals`) — 8종 자산 select + RSI/MACD/ATR → `f64b9fa`
- [x] **P3-4 (L)** 모바일 반응형 — 768px KPI 1열, chart 280px, drawer 100vw, pill flex-wrap → `200f1c0`
- [x] **P3-5 (S)** AssetPickerDrawer 탭별 분기 — Tab A 6종 / Tab B 3종 / Tab C preset 4개 검증 → `29de2d3`

검증: PNG 14종 + verification/ evidence 5종 PASS ✅

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

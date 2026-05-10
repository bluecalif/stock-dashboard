# Phase 4 Plan — 빅뱅 Cut-over
> Gen: silver
> Last Updated: 2026-05-10
> Status: Planning

---

## 1. Summary (개요)

**목적**: Silver gen 프론트·백엔드가 병행 운영 상태에서 **단일 cut-over**로 Bronze 잔재를 완전 제거하고 Silver-only 운영으로 전환. 다운타임은 수 분 이내.

**범위**:
- `git tag v-bronze-final` — rollback 앵커 확보
- Bronze 페이지 코드 삭제 (StrategyPage/DashboardPage/PricePage/CorrelationPage/IndicatorSignalPage)
- `routers/backtests.py` 제거 + backtest_* 3테이블 DROP migration
- Agentic tool registration 정리 (strategy_classify/report 제거, simulation_* 3종 추가)
- master merge + prod 배포 + smoke test
- 1주 monitoring

**예상 결과물 (Phase 4 종료 시)**:
- `/silver/compare` 단일 진입, Bronze 라우트 전부 redirect
- backtest_* 테이블 삭제됨, DB는 silver-only 스키마
- Agentic chat: simulation_replay/strategy/portfolio 3종 tool 작동
- `v-bronze-final` tag로 30분 내 rollback 가능

---

## 2. Current State (Phase 3 인계)

- **Silver 페이지 완전 동작** (Phase 3 ✅):
  - `/silver/compare` Tab A/B/C + KPI + 차트
  - `/silver/signals` 8종 자산 RSI/MACD/ATR
  - 모바일 768px 반응형
  - AssetPickerDrawer 탭별 분기 검증 완료
- **Bronze 페이지 병행 운영 중**: DashboardPage/PricePage/CorrelationPage/StrategyPage/IndicatorSignalPage
- **Bronze 라우트 partial redirect**: `/prices`, `/correlation`, `/strategy`, `/indicators` → `/silver/compare` (Phase 3에서 추가)
- **삭제 대상 확인됨**:
  - `frontend/src/pages/`: StrategyPage.tsx / DashboardPage.tsx / PricePage.tsx / CorrelationPage.tsx / IndicatorSignalPage.tsx / FactorPage.tsx / SignalPage.tsx
  - `backend/api/routers/backtests.py`
  - `backend/api/services/llm/agentic/data_fetcher.py` — `list_backtests`, `backtest_strategy` tool 제거 필요
- **DB**: backtest_run, backtest_equity_curve, backtest_trade_log 테이블 현존

---

## 3. Target State (Phase 4 종료 시)

```
frontend/src/pages/
├── LoginPage.tsx           (유지)
├── SignupPage.tsx          (유지)
└── silver/                 (Silver 전용 — Phase 3 산출물)
    ├── CompareMainPage.tsx
    ├── SignalDetailPage.tsx
    └── components/

backend/api/routers/
├── assets.py               (유지)
├── prices.py               (유지 — Silver Signals 가격 조회용)
├── factors.py              (유지 — Silver Signals 팩터 조회용)
├── signals.py              (유지 — Silver Signals 신호 조회용)
├── simulation.py           (Silver 신규, Phase 2 산출물)
├── fx.py                   (Silver 신규, Phase 2 산출물)
├── correlation.py          (유지 — Dashboard 통계 유지 여부 별도 결정)
├── dashboard.py            (유지 — Agentic dashboard_summary 기반)
├── analysis.py             (유지 — Agentic analyze_indicators 기반)
├── chat.py / auth.py / profile.py / health.py  (유지)
└── backtests.py            ← 삭제됨

DB tables:
├── asset_master           (유지)
├── price_daily            (유지)
├── factor_daily           (유지)
├── signal_daily           (유지)
├── fx_daily               (Silver 신규, Phase 1 산출물)
├── job_run                (유지)
├── backtest_run           ← DROP됨
├── backtest_equity_curve  ← DROP됨
└── backtest_trade_log     ← DROP됨

Agentic _TOOL_MAP:
├── get_prices             (유지)
├── get_factors            (유지)
├── get_correlation        (유지)
├── get_signals            (유지)
├── analyze_correlation_tool (유지)
├── get_spread             (유지)
├── analyze_indicators     (유지)
├── list_backtests         ← 제거
├── backtest_strategy      ← 제거
├── simulation_replay      ← 신규 등록
├── simulation_strategy    ← 신규 등록
└── simulation_portfolio   ← 신규 등록
```

---

## 4. Implementation Stages

| Stage | 태스크 | 설명 | 위험도 |
|---|---|---|---|
| A | P4-1 | git tag `v-bronze-final` 생성 | 없음 |
| B | P4-2 | App.tsx Bronze 라우트 완전 정리 | 낮음 |
| C | P4-3 | Bronze 페이지 코드 삭제 | 낮음 (Silver 병행 완료) |
| D | P4-4 | backtests.py 제거 + DROP migration | 중간 (DB 변경) |
| E | P4-5 | Agentic tool 정리 + simulation_* 등록 | 중간 (LangGraph 영향) |
| F | P4-6 | master merge + prod 빅뱅 배포 + smoke test | 높음 (다운타임) |
| G | P4-7 | 1주 monitoring | — |

**Stage 순서**: A → B → C → D → E 병렬 → F (최종) → G

---

## 5. Task Breakdown

| 태스크 | Size | 의존성 | 주요 산출 |
|---|---|---|---|
| P4-1 | S | Phase 3 완료 | `v-bronze-final` tag |
| P4-2 | M | P4-1 | App.tsx Bronze 라우트 완전 제거 |
| P4-3 | M | P4-2 | 5개 Bronze 페이지 파일 삭제 |
| P4-4 | S | P4-1 | backtests.py 삭제 + DROP migration |
| P4-5 | M | P4-1 | data_fetcher.py tool 정리 + simulation_* tool 신규 작성 |
| P4-6 | L | P4-2~P4-5 | master merge + Railway 배포 + smoke test |
| P4-7 | S | P4-6 | 1주 monitoring 체크리스트 통과 |

**합계**: 7개 (S:3 / M:3 / L:1)

---

## 6. Risks & Mitigation

| 리스크 | 영향 | 대응 |
|---|---|---|
| DROP migration 실패 | DB 불일치 | T-1d 백업 (`pg_dump`) + alembic downgrade 확인 |
| Agentic tool 제거 후 chat 오작동 | chat 비정상 | strategy_classify/report 제거 전 fallback 동작 테스트 |
| simulation_* tool 미등록 시 chat silent fail | Agentic chat 무응답 | 등록 후 실제 chat 쿼리 smoke test |
| Bronze 코드 삭제 후 import 누락 | 빌드 에러 | TypeScript 컴파일 + ruff 검사 |
| 빅뱅 배포 중 다운타임 30분 초과 | 사용자 영향 | `v-bronze-final` rollback 절차 문서화 |

---

## 7. Dependencies

**내부**:
- Phase 1 (fx_daily, asset_master), Phase 2 (simulation/), Phase 3 (Silver 페이지) 모두 완료 전제
- `backend/api/services/llm/agentic/data_fetcher.py` — tool 정리 핵심
- `backend/api/services/llm/tools/` — simulation_* tool 신규 작성 위치
- `frontend/src/App.tsx` — 라우트 완전 정리

**외부**:
- Railway (prod DB + 웹 서비스) — migration 적용 + 재배포
- Alembic — DROP migration 스크립트

**기준 문서**:
- `docs/silver-masterplan.md` §5.3 (라우터 변경), §5.4 (Agentic 정리), §10 (배포 플랜)
- `dev/active/project-overall/project-overall-context.md` §0 (Show, don't claim)

---

## 8. DoD (Definition of Done)

- [ ] `v-bronze-final` git tag 생성
- [ ] Bronze 페이지 5종 파일 삭제, TypeScript 컴파일 통과
- [ ] backtest_* 3테이블 DROP migration 적용됨
- [ ] Agentic chat: strategy_classify/report 제거, simulation_* 3종 정상 호출
- [ ] prod 빅뱅 배포 후 `/silver/compare` KPI 정상 산출
- [ ] verification/ evidence 6종 + PNG 스크린샷 누적
- [ ] 1주 monitoring 체크리스트 완료

---

## 9. Rollback 절차 (빅뱅 실패 시)

1. Railway 웹 서비스: 이전 deploy로 롤백
2. DB: `alembic downgrade -1` (DROP 취소)
3. git: `git reset --hard v-bronze-final`
4. 예상 복구 시간: **30분 이내**

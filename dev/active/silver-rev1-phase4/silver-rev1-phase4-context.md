# Phase 4 Context — 빅뱅 Cut-over
> Gen: silver
> Last Updated: 2026-05-10 (P4-7 monitoring 완료 — Phase 4 전체 7/7)

---

## 9. P4-7 Monitoring — 완료 (2026-05-10)

**G7.1 PASS** — Simulation API latency 10회: avg=1858ms, P95=2065ms < 5000ms (캐시 도입 불필요)  
**G7.2 PASS** — 15자산 전부 2026-05-08(금, 최근 거래일) 데이터 보유, 오늘 10:05 ingest_all success  
**UI PASS** — Tab A/B/C 전 탭 정상, Tab B 화이트스크린 없음(textLen=878), 모바일 768px 반응형 정상, 콘솔 에러 없음  
**결정사항**: D-P4-7: P95=2065ms → Phase 5 캐시 도입 검토 불필요 (임계 5초 이하)

| 파일 | 내용 |
|------|------|
| `dev/active/silver-rev1-phase4/verification/step-7-monitoring.md` | G7.1+G7.2 evidence |
| `verification/figures/p4-7-tab-a-loaded.png` | Tab A 차트 스크린샷 |
| `verification/figures/p4-7-tab-b-strategy.png` | Tab B 화이트스크린 없음 확인 |
| `verification/figures/p4-7-tab-c-portfolio.png` | Tab C 포트폴리오 차트 |
| `verification/figures/p4-7-mobile-768.png` | 모바일 반응형 스크린샷 |

---

## 8. P4-7 Monitoring — prod 버그 수정 (2026-05-10)

| 파일 | 변경 내용 | 커밋 |
|------|-----------|------|
| `backend/research_engine/simulation/replay.py` | WBI: `trading_dates` 먼저 생성 후 `len()`으로 n_days 맞춤 | `8fc9013` |
| `backend/api/services/simulation_service.py` | `_load_price_and_fx`: `r.close is not None` 필터 + `.dropna()` | `8fc9013` |
| `backend/research_engine/simulation/wbi.py` | zero-mean 노이즈 + drift 보정으로 20% CAGR 보장 | `1d82073` |
| `backend/research_engine/simulation/fixtures/wbi_seed42_10y.npz` | 새 generate_wbi 기준 fixture 재생성 | `1d82073` |

**결정사항**:
- D-P4-4: WBI GBM은 기대값이 아닌 정확한 CAGR 달성을 보장해야 함 (drift 재스케일링)
- D-P4-5: `_load_price_and_fx`에서 price NaN 필터링 필수 (DB에서 가져온 Series는 항상 dropna)
- D-P4-6: DCA annualized return (10.52%)이 자산 CAGR (20%)보다 낮은 것은 DCA 특성 (정상)

---

## 0. 핵심 원칙 — "Show, don't claim"

> **검증 게이트의 체크박스는 evidence가 `verification/step-N-<topic>.md`에 paste됐을 때만 표시 가능.**
> Claude의 "PASS / 통과" 주장만으로는 mark complete 금지. 빅뱅 cut-over 이후 smoke test 결과는 반드시 curl 응답 dump + 스크린샷 형태로 paste.

---

## 1. 핵심 참조 파일

### 1.1 읽어야 할 기존 코드

| 파일 | 용도 |
|---|---|
| `frontend/src/App.tsx` | 현재 라우트 구조 — Bronze redirect 정리 대상 |
| `frontend/src/pages/StrategyPage.tsx` | 삭제 대상 (import 역추적 필요) |
| `frontend/src/pages/DashboardPage.tsx` | 삭제 대상 |
| `frontend/src/pages/PricePage.tsx` | 삭제 대상 |
| `frontend/src/pages/CorrelationPage.tsx` | 삭제 대상 |
| `frontend/src/pages/IndicatorSignalPage.tsx` | 삭제 대상 (SignalDetailPage.tsx로 대체됨) |
| `frontend/src/pages/FactorPage.tsx` | 삭제 대상 (Silver에 해당 없음) |
| `frontend/src/pages/SignalPage.tsx` | 삭제 대상 (Silver signals와 무관) |
| `backend/api/routers/backtests.py` | 삭제 대상 |
| `backend/api/services/llm/agentic/data_fetcher.py` | tool 정리 핵심 — _TOOL_MAP 수정 |
| `backend/api/services/llm/tools/` | simulation_* tool 신규 작성 위치 |
| `backend/db/models/` | backtest_* 모델 파일 — DROP migration 이후 파일도 삭제 |
| `backend/alembic/versions/` | DROP migration 스크립트 작성 위치 |

### 1.2 참조 문서

| 파일 | 용도 |
|---|---|
| `docs/silver-masterplan.md` §5.3 | 라우터 제거·유지 목록 |
| `docs/silver-masterplan.md` §5.4 | Agentic tool 정리 명세 |
| `docs/silver-masterplan.md` §10 | cut-over 절차 (T-7d~T+1w) |
| `dev/active/silver-rev1-phase2/silver-rev1-phase2-context.md` | simulation/ 모듈 구조 — tool 등록 시 참조 |
| `project-wrapup/lessons-learned.json` A-004 | Agentic ↔ Dashboard 데이터 소스 일치 교훈 |

---

## 2. 삭제 대상 전체 목록

### 2.1 Frontend 페이지 파일

| 파일 | 이유 |
|---|---|
| `frontend/src/pages/DashboardPage.tsx` | Silver 메뉴 재편으로 drop (마스터플랜 §8.3) |
| `frontend/src/pages/PricePage.tsx` | Silver에서 `/silver/compare` Tab A로 대체 |
| `frontend/src/pages/CorrelationPage.tsx` | Silver 메뉴 미포함 |
| `frontend/src/pages/StrategyPage.tsx` | backtest 테이블 drop과 함께 제거 (Q8-26) |
| `frontend/src/pages/IndicatorSignalPage.tsx` | `/silver/signals`의 `SignalDetailPage.tsx`로 대체 완료 |
| `frontend/src/pages/FactorPage.tsx` | Bronze 전용, Silver에 미사용 |
| `frontend/src/pages/SignalPage.tsx` | Bronze 전용, Silver에 미사용 |

> **주의**: 삭제 전 App.tsx 및 관련 컴포넌트에서 import 역추적 필수.

### 2.2 Backend 라우터

| 파일 | 이유 |
|---|---|
| `backend/api/routers/backtests.py` | backtest_* 테이블 drop + StrategyPage 제거 (마스터플랜 §5.3) |

### 2.3 DB 테이블 (Alembic DROP migration)

```sql
-- Phase 4 DROP migration
DROP TABLE backtest_trade_log;
DROP TABLE backtest_equity_curve;
DROP TABLE backtest_run;
```

> **순서**: FK 의존성에 따라 trade_log → equity_curve → run 순서로 DROP.

### 2.4 Agentic tool 제거

`backend/api/services/llm/agentic/data_fetcher.py`의 `_TOOL_MAP`에서:

```python
# 제거 대상
"list_backtests": list_backtests,
"backtest_strategy": backtest_strategy,
```

관련 import(`list_backtests`, `backtest_strategy`) 및 `_build_tool_args` 케이스도 정리.

---

## 3. 신규 구현 — simulation_* Agentic tools

**위치**: `backend/api/services/llm/tools/simulation_tools.py` (신규)

**등록**: `data_fetcher.py`의 `_TOOL_MAP`에 추가:

```python
from api.services.llm.tools.simulation_tools import (
    simulation_replay_tool,
    simulation_strategy_tool,
    simulation_portfolio_tool,
)

_TOOL_MAP = {
    # ... 기존 유지 tool들 ...
    "simulation_replay": simulation_replay_tool,
    "simulation_strategy": simulation_strategy_tool,
    "simulation_portfolio": simulation_portfolio_tool,
}
```

**핵심 설계 원칙** (A-004 교훈):
- 각 tool 함수는 내부적으로 simulation 모듈 함수를 직접 호출 (HTTP 경유 금지)
- 즉, `replay.run_replay(...)`, `strategy_a.run_strategy(...)`, `portfolio.run_portfolio(...)` 직접 import
- 이렇게 해야 `/v1/silver/simulate/*` 라우터와 동일한 로직을 보장

**입력 파라미터 설계**:

```python
# simulation_replay_tool
{
    "asset_codes": ["QQQ", "SPY"],  # Tab A 6종 중 선택
    "monthly_amount": 1000000,       # 원 단위
    "period_years": 10               # 3, 5, 10
}

# simulation_strategy_tool
{
    "asset_code": "QQQ",             # Tab B 3종 중 1종
    "strategy_type": "A",            # "A" or "B"
    "monthly_amount": 1000000,
    "period_years": 10
}

# simulation_portfolio_tool
{
    "preset_id": "QQQ_TLT_BTC",      # 4개 preset 중 1개
    "monthly_amount": 1000000,
    "period_years": 10
}
```

---

## 4. App.tsx 라우트 완전 정리

**Phase 3 이후 현황**: Bronze 라우트에 `<Navigate to="/silver/compare" />` 추가됨

**Phase 4 작업**: 
- Bronze 페이지 파일 삭제 후 해당 import 제거
- 불필요한 Bronze import 완전 정리
- Silver 라우트만 남기고 불필요한 redirect 코드 제거

**최종 App.tsx 구조**:
```tsx
<Routes>
  <Route path="/login" element={<LoginPage />} />
  <Route path="/signup" element={<SignupPage />} />
  <Route element={<ProtectedRoute />}>
    <Route element={<SilverLayout />}>
      <Route index element={<Navigate to="/silver/compare" replace />} />
      <Route path="silver/compare" element={<CompareMainPage />} />
      <Route path="silver/signals" element={<SignalDetailPage />} />
      <Route path="silver/chat" element={<ChatPage />} />
      {/* Bronze 경로들 → 전부 redirect */}
      <Route path="prices" element={<Navigate to="/silver/compare" replace />} />
      <Route path="correlation" element={<Navigate to="/silver/compare" replace />} />
      <Route path="strategy" element={<Navigate to="/silver/compare" replace />} />
      <Route path="indicators" element={<Navigate to="/silver/compare" replace />} />
      <Route path="factors" element={<Navigate to="/silver/compare" replace />} />
    </Route>
  </Route>
</Routes>
```

---

## 5. Cut-over 절차 (마스터플랜 §10.1)

```
T-7d  staging 환경에서 전체 검증
T-3d  Bronze 코드 삭제 + Agentic 정리 staging 확인
T-1d  DB 백업 (Railway pg_dump)
T-0   빅뱅 cut-over:
        1. git tag v-bronze-final
        2. DROP migration (Railway 콘솔)
        3. 코드 master merge → Railway 자동 배포
        4. smoke test
T+1w  monitoring 완료 → Phase 5 진입 결정
```

---

## 6. 컨벤션 체크리스트

| 항목 | 규칙 |
|---|---|
| 파일 삭제 | 삭제 전 `grep -r "파일명" frontend/src/` 로 import 역추적 |
| Migration | `alembic revision --autogenerate -m "drop backtest tables"` 후 수동 검토 |
| Tool 등록 | `simulation_*` tool 추가 후 반드시 chat 쿼리 smoke test |
| 커밋 형식 | `[silver-rev1-phase4] P4-N: description` |
| 배포 전 | TypeScript 컴파일 (`npx tsc --noEmit`) + ruff 검사 통과 필수 |
| Rollback | `v-bronze-final` → `alembic downgrade -1` 절차 30분 이내 실행 가능 확인 |

---

## 7. 주요 결정사항

| # | 결정 | 출처 | 코딩 영향 |
|---|---|---|---|
| D-14 | Bronze→Silver = 빅뱅 교체 | Q8-24 | feature flag 없이 단일 cut-over |
| D-15 | StrategyPage drop = DB 테이블도 drop | Q8-26 | backtest_* 3테이블 DROP migration |
| D-P4-1 | simulation_* tool은 HTTP 경유 금지, simulation/ 직접 import | A-004 교훈 | data_fetcher.py에서 라우터 호출 X |
| D-P4-2 | factors.py / signals.py 라우터 유지 | Silver Signals 페이지가 팩터/신호 데이터 사용 | 삭제 대상에서 제외 |
| D-P4-3 | FactorPage.tsx / SignalPage.tsx = Bronze 전용 삭제 | Silver에 해당 페이지 없음 | 해당 import 정리 |

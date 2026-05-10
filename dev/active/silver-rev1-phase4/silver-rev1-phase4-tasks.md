# Phase 4 Tasks — 빅뱅 Cut-over
> Gen: silver
> Last Updated: 2026-05-10
> Status: In Progress (6/7)

## DoD (Definition of Done)

- [ ] `v-bronze-final` git tag 생성
- [ ] Bronze 페이지 5종 + 2종 파일 삭제, TypeScript 컴파일 통과
- [ ] backtest_* 3테이블 DROP migration 적용됨
- [ ] Agentic chat: strategy_classify/report 제거 + simulation_* 3종 정상 호출
- [ ] prod 빅뱅 배포 후 `/silver/compare` KPI 정상 산출
- [ ] verification/ evidence 6종 + PNG 스크린샷 누적
- [ ] 1주 monitoring 체크리스트 완료

---

## P4-1 (S) — git tag `v-bronze-final`

**목표**: cut-over 전 현재 master 상태를 태그로 보존. 빅뱅 실패 시 30분 내 rollback 앵커.

### Sub-steps

- [x] `git tag v-bronze-final` 생성
- [x] `git push origin v-bronze-final` 원격 push
- [x] tag 존재 확인
- [x] verification/step-1-tag.md 작성

### G1.1 — git tag 생성 확인

- 명령: `git tag -l "v-bronze-final"`
- Evidence: 명령 출력 → `verification/step-1-tag.md` paste
- 통과 기준: `v-bronze-final` 태그가 출력됨

### G1.2 — 원격 tag push 확인

- 명령: `git ls-remote origin refs/tags/v-bronze-final`
- Evidence: 명령 출력 → `verification/step-1-tag.md` paste
- 통과 기준: commit hash + tag ref가 한 줄 출력됨

---

## P4-2 (M) — App.tsx Bronze 라우트 완전 정리

**목표**: 삭제된 Bronze 페이지 import 제거 + Bronze 라우트를 `/silver/compare`로 통일.

### Sub-steps

- [x] App.tsx에서 Bronze 페이지 import 제거 (DashboardPage/PricePage/CorrelationPage/StrategyPage/IndicatorSignalPage 등)
- [x] Bronze 라우트를 `<Navigate to="/silver/compare" replace />` 로 통일
- [x] TypeScript 컴파일 통과 (`npx tsc --noEmit`)
- [x] verification/step-2-routes.md 작성

### G2.1 — TypeScript 컴파일

- 명령: `cd frontend && npx tsc --noEmit 2>&1`
- Evidence: 컴파일 출력 → `verification/step-2-routes.md` paste
- 통과 기준: 에러 0개, 경고만 허용

### G2.2 — Bronze 라우트 redirect 확인

- 명령: Puppeteer 또는 curl로 `/prices`, `/strategy`, `/indicators` 접근 후 redirect URL 확인
- Evidence: 각 경로 응답 헤더 또는 최종 URL → `verification/step-2-routes.md` paste
- 통과 기준: 모든 Bronze 경로가 `/silver/compare`로 redirect됨
- PNG: `figures/step-2-redirect.png` (브라우저 스크린샷)

---

## P4-3 (M) — Bronze 페이지 코드 삭제

**목표**: Bronze 전용 페이지 7종 파일 삭제. Silver 기능에 영향 없음을 확인.

### Sub-steps

- [x] 삭제 전 각 파일 import 역추적 (`grep -r "파일명" frontend/src/`)
- [x] `DashboardPage.tsx` 삭제
- [x] `PricePage.tsx` 삭제
- [x] `CorrelationPage.tsx` 삭제
- [x] `StrategyPage.tsx` 삭제
- [x] `IndicatorSignalPage.tsx` 삭제 (SignalDetailPage.tsx로 완전 대체됨)
- [x] `FactorPage.tsx` 삭제 (Bronze 전용)
- [x] `SignalPage.tsx` 삭제 (Bronze 전용, Silver signals와 별개)
- [x] TypeScript 컴파일 통과
- [x] `/silver/compare` + `/silver/signals` 정상 동작 확인
- [x] verification/step-3-code-delete.md 작성

### G3.1 — TypeScript 컴파일 (삭제 후)

- 명령: `cd frontend && npx tsc --noEmit 2>&1`
- Evidence: 컴파일 출력 → `verification/step-3-code-delete.md` paste
- 통과 기준: 에러 0개

### G3.2 — Silver 페이지 정상 동작

- 명령: Puppeteer로 `/silver/compare` + `/silver/signals` 접근 후 스크린샷
- Evidence: PNG 스크린샷 → `verification/figures/step-3-silver-pages.png`
- 통과 기준: Tab A KPI 렌더링, Signals RSI 차트 표시

### G3.3 — 삭제된 파일 없음 확인

- 명령: `ls frontend/src/pages/ | grep -E "Dashboard|Price|Correlation|Strategy|IndicatorSignal|Factor|Signal"`
- Evidence: 명령 출력 → `verification/step-3-code-delete.md` paste
- 통과 기준: 해당 파일이 목록에 없음 (출력 없음 또는 silver/ 디렉터리만 표시)

---

## P4-4 (S) — routers/backtests.py 제거 + DROP migration

**목표**: backtests 라우터 삭제 + backtest_* 3테이블 DROP alembic migration 작성·적용.

### Sub-steps

- [x] `backend/api/routers/backtests.py` 삭제
- [x] `backend/api/main.py`에서 backtests 라우터 import/include 제거
- [x] Alembic migration 작성: revision `c9b884d01cb4` (drop_backtest_tables)
- [x] Migration SQL 검토 (DROP 순서: trade_log → equity_curve → run)
- [x] Railway prod DB에 migration 적용 확인 (단일 DB 구조)
- [x] verification/step-4-migration.md 작성

### G4.1 — Migration SQL 검증

- 명령: `cat backend/alembic/versions/<new_revision>_drop_backtest_tables.py`
- Evidence: migration 파일 내용 → `verification/step-4-migration.md` paste
- 통과 기준: DROP TABLE 3개 (backtest_trade_log, backtest_equity_curve, backtest_run) 포함

### G4.2 — Migration 적용 후 테이블 없음 확인

- 명령: (Railway psql 또는 pytest DB session) `SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'backtest_%';`
- Evidence: SQL 결과 → `verification/step-4-migration.md` paste
- 통과 기준: 결과 0행 (backtest_* 테이블 없음)

### G4.3 — backtests 라우터 제거 후 서버 기동

- 명령: `uvicorn api.main:app --port 8000` 기동 후 `curl http://localhost:8000/v1/health`
- Evidence: health 응답 JSON → `verification/step-4-migration.md` paste
- 통과 기준: `{"status": "ok"}` 또는 유사 응답, 에러 없음

---

## P4-5 (M) — Agentic tool registration 정리

**목표**: strategy_classify/report 관련 tool 제거, simulation_replay/strategy/portfolio 3종 신규 등록.

### Sub-steps

- [x] `backend/api/services/llm/simulation_tools.py` 신규 작성 (3개 tool 함수)
- [x] `data_fetcher.py` — `list_backtests`, `backtest_strategy` import 제거
- [x] `data_fetcher.py` — `_TOOL_MAP`에서 해당 키 제거
- [x] `data_fetcher.py` — `simulation_*` 3종 import + `_TOOL_MAP` 등록
- [x] `_build_tool_args()` 함수에 simulation_* 케이스 추가
- [x] simulation_replay tool QQQ 10년 total_return=2.8399 ✅
- [x] verification/step-5-agentic.md 작성

### G5.1 — simulation_replay tool 직접 호출 테스트

- 명령:
  ```python
  from api.services.llm.tools.simulation_tools import simulation_replay_tool
  result = simulation_replay_tool.invoke({"asset_codes": ["QQQ"], "monthly_amount": 1000000, "period_years": 10})
  print(result)
  ```
- Evidence: tool 결과 (final_asset_krw, total_return 포함) → `verification/step-5-agentic.md` paste
- 통과 기준: `total_return` ≈ 2.84 (Phase 2 fixture 기준 ±5%)

### G5.2 — Agentic chat 쿼리 smoke test

- 명령: POST `/v1/chat/stream` body `{"message": "QQQ 10년 적립 결과 알려줘", "session_id": "test"}`
- Evidence: SSE 스트림 응답 (tool 호출 로그 포함) → `verification/step-5-agentic.md` paste
- 통과 기준: `simulation_replay` tool 호출 확인, 최종자산 4억원대 응답

### G5.3 — strategy_classify/report 제거 후 fallback 확인

- 명령: POST `/v1/chat/stream` body `{"message": "전략 백테스트 결과 보여줘"}`
- Evidence: 응답 → `verification/step-5-agentic.md` paste
- 통과 기준: 에러 없이 graceful fallback (해당 기능 미지원 안내 or simulation으로 유도)

---

## P4-6 (L) — master merge + 빅뱅 배포 + smoke test

**목표**: T-1d 백업 → T-0 migration + 배포 → smoke test 전 과정 실행.

### Sub-steps

- [x] **T-0 Step 1**: `git tag v-bronze-final` (P4-1 완료)
- [x] **T-0 Step 2**: prod DB DROP migration 적용 (`alembic upgrade head`)
- [x] **T-0 Step 3**: CI `2d66c8c` success → Railway + Vercel 자동 배포
- [x] **T-0 Step 4**: smoke test 실행 (G6.1~G6.4)
- [x] verification/step-6-cutover.md 작성

### G6.1 — prod `/silver/compare` 렌더링

- 명령: Puppeteer로 prod URL `/silver/compare` 접속 후 스크린샷
- Evidence: PNG → `verification/figures/step-6-prod-compare.png`
- 통과 기준: Tab A KPI 렌더링, QQQ 최종자산 4억원대 표시

### G6.2 — KPI 정합성 (Phase 2 fixture 기준)

- 명령: `curl -X POST https://<prod>/v1/silver/simulate/replay -d '{"asset_codes":["QQQ"],"monthly_amount":1000000,"period_years":10}'`
- Evidence: JSON 응답 (`kpi.total_return`, `kpi.annualized_return`) → `verification/step-6-cutover.md` paste
- 통과 기준: `total_return` ≈ 2.84 (±5%), `annualized_return` ≈ 0.144 (±5%)

  ### G6.3 — Bronze 경로 redirect 확인

- 명령: `curl -I https://<prod>/prices` (Location 헤더 확인)
- Evidence: 응답 헤더 → `verification/step-6-cutover.md` paste
- 통과 기준: `Location: /silver/compare` 포함 또는 최종 URL이 `/silver/compare`

### G6.4 — backtest 테이블 없음 (prod)

- 명령: Railway psql → `SELECT table_name FROM information_schema.tables WHERE table_name LIKE 'backtest_%';`
- Evidence: SQL 결과 → `verification/step-6-cutover.md` paste
- 통과 기준: 결과 0행

---

## P4-7 (S) — 1주 monitoring

**목표**: 빅뱅 이후 1주간 시스템 안정성 확인. 주요 지표를 체크리스트 형태로 추적.

### Sub-steps

- [ ] 매일 `/silver/compare` 접속 확인 (로그인 → Tab A 시뮬레이션 응답 정상)
- [ ] Agentic chat 쿼리 2회 이상 테스트
- [ ] simulation API P95 latency 측정 (10회 호출 → 중간값 기록)
- [ ] DB row count 이상 없음 확인 (price_daily 일일 갱신 정상)
- [ ] verification/step-7-monitoring.md 작성

### G7.1 — 1주 monitoring 완료

- 명령: `curl -w "%{time_total}" -X POST https://<prod>/v1/silver/simulate/replay ...` (10회 반복)
- Evidence: latency 기록 (10회 평균, P95) → `verification/step-7-monitoring.md` paste
- 통과 기준: P95 latency ≤ 5초 (초과 시 Phase 5 캐시 도입 검토)

### G7.2 — price_daily 일일 갱신 정상

- 명령: `SELECT asset_code, MAX(date) as latest FROM price_daily GROUP BY asset_code ORDER BY asset_code;`
- Evidence: SQL 결과 → `verification/step-7-monitoring.md` paste
- 통과 기준: 모든 15자산이 monitoring 완료일 기준 최근 거래일 데이터 보유

---

## 완료 기록

| 태스크 | 완료일 | commit hash |
|---|---|---|
| P4-1 | 2026-05-10 | `9461d8c` (tag) |
| P4-2 | 2026-05-10 | `3152c2e` |
| P4-3 | 2026-05-10 | `3152c2e` |
| P4-4 | 2026-05-10 | `3152c2e` |
| P4-5 | 2026-05-10 | `3152c2e` |
| P4-6 | 2026-05-10 | `26ca5ab` (CI `2d66c8c` → 배포) |
| P4-7 | — | 진행 중 (1주 monitoring) |

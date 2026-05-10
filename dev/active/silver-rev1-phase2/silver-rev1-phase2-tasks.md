# Phase 2 Tasks — 시뮬레이션 엔진
> Gen: silver
> Last Updated: 2026-05-10
> Status: Planning (0/7)

## DoD (Definition of Done)

- [ ] simulation/ 8개 파일 완성 (`__init__` + `padding` + `wbi` + `fx` + `mdd` + `replay` + `strategy_a` + `strategy_b` + `portfolio`)
- [ ] API 4종 동작: `/v1/silver/simulate/{replay,strategy,portfolio}` + `/v1/fx/usd-krw`
- [ ] QQQ 10년 적립 KPI ↔ 외부 도구 ±2% 일치 (G7.1 evidence paste)
- [ ] verification/ evidence 7종 + PNG 3종 누적
- [ ] `project-overall-tasks.md` Phase 2 섹션 동기화 (`/step-update --sync-overall`)

---

## P2-1 (S) — 디렉터리 구조 확인 + `__init__.py` exports 정비

**목표**: Phase 1에서 생성된 `simulation/` 패키지 구조를 확인하고, Phase 2 모듈이 추가될 때 `__init__.py`가 올바른 public interface를 노출하는지 정비.

### Sub-steps

- [ ] `simulation/` 하위 파일 목록 확인 (Phase 1 산출물 존재 여부)
- [ ] `__init__.py`에 Phase 2 예정 모듈 `__all__` 플레이스홀더 추가 (구현 전 설계 명확화)
- [ ] verification/step-1-structure.md 작성

### G1.1 — 디렉터리 구조 확인
- 명령: `ls backend/research_engine/simulation/`
- Evidence: 파일 목록을 verification/step-1-structure.md 코드 블록에 paste
- 통과 기준: `__init__.py`, `padding.py`, `wbi.py`, `fixtures/` 모두 존재

### G1.2 — `__init__.py` exports 확인
- 명령: `cat backend/research_engine/simulation/__init__.py`
- Evidence: 내용 paste
- 통과 기준: `pad_returns`, `generate_wbi` 또는 상응 함수 export 확인 (또는 Phase 2 추가 계획 명시)

---

## P2-2 (M) — `fx.py` + `mdd.py` 구현

**목표**: 나머지 utility 2종 구현. `padding.py`/`wbi.py`는 Phase 1 완료.

### Sub-steps

- [ ] `fx.py` 구현 — `load_fx_series(db_session, start, end) -> pd.Series` (forward-fill)
- [ ] `mdd.py` 구현 — `mdd_by_calendar_year(curve_krw) -> dict[int, float]` (마스터플랜 §3.7)
- [ ] `test_fx.py` — 결측일 forward-fill, 날짜 범위 경계 (4 tests 이상)
- [ ] `test_mdd.py` — 알려진 drawdown 값 검증 (4 tests 이상)
- [ ] verification/step-2-fx-mdd.md + figures/step-2-mdd-bar.png 작성

### G2.1 — `fx.py` forward-fill 검증
- 명령: `python -c "from research_engine.simulation.fx import load_fx_series; ..."`  (KR 휴장일인 날짜 포함 범위 조회)
- Evidence: 결측일 전후 값 pandas Series 출력 → verification/step-2-fx-mdd.md 코드 블록
- 통과 기준: KR 휴장일(예: 2024-01-01) 값이 직전 거래일 값으로 forward-fill됨

### G2.2 — `mdd.py` 알려진 값 검증
- 명령: `python -m pytest backend/tests/unit/test_mdd.py -v`
- Evidence: pytest 출력 paste
- 통과 기준: 전체 PASSED, `mdd_by_calendar_year` 수학 검증 case 포함

### G2.3 — 전체 unit test
- 명령: `python -m pytest backend/tests/unit/test_fx.py backend/tests/unit/test_mdd.py -v`
- Evidence: pytest 출력 paste
- 통과 기준: 0 failed, 8 tests 이상 PASSED

### G2.4 — MDD bar chart PNG (의무)
- 명령: test_mdd.py 또는 별도 script로 연도별 MDD bar chart 생성
- Evidence: `verification/figures/step-2-mdd-bar.png` 생성 → Read 도구로 확인
- 통과 기준: 연도별 음수값 bar, 2022년이 가장 깊은 MDD로 표시 (QQQ 기준 약 -33%)

---

## P2-3 (L) — `replay.py` 구현

**목표**: 적립식 Tab A 핵심 엔진. 매월 첫 거래일 적립 + 배당 매일 재투자 + USD fractional 매수.

**핵심 lock**: D-4 (배당), D-16 (이벤트 순서), D-3 (fx_daily), 마스터플랜 §3.3

### Sub-steps

- [ ] `replay.py` 구현 — `replay(asset_code, monthly_amount_krw, period_years, session) -> tuple[list[EquityPoint], KpiResult]`
- [ ] WBI 경로 분기 — `asset_code == "WBI"` 시 `wbi.py` 호출
- [ ] JEPI 경로 분기 — `allow_padding=True` 시 `padding.py` 호출
- [ ] `compute_kpi()` 구현 (마스터플랜 §3.8)
- [ ] `test_replay.py` — 기본 smoke, 배당 재투자 효과, USD/KRW 환산, JEPI padding 경로 (6 tests 이상)
- [ ] verification/step-3-replay.md + figures/step-3-replay-qqq.png

### G3.1 — 기본 smoke test
- 명령: `python -m pytest backend/tests/unit/test_replay.py::test_replay_basic -v`
- Evidence: pytest 출력 paste
- 통과 기준: PASSED, `len(curve) == period_years * 252` ± 10% 범위

### G3.2 — 배당 재투자 효과 검증
- 명령: `python -m pytest backend/tests/unit/test_replay.py::test_replay_dividend -v`
- Evidence: SCHD(3.5%) vs 배당 없는 경우 최종자산 차이 수치 paste
- 통과 기준: SCHD 경로 최종자산 > 배당 없는 경우 최종자산 (방향 검증)

### G3.3 — USD 자산 환율 환산
- 명령: `python -m pytest backend/tests/unit/test_replay.py::test_replay_usd_asset -v`
- Evidence: QQQ KRW 평가액 series 샘플 (첫/중간/마지막 10행) paste
- 통과 기준: KRW 평가액이 `shares * usd_price * fx_rate`와 일치 (상대 오차 < 1e-9)

### G3.4 — JEPI padding 경로
- 명령: `python -m pytest backend/tests/unit/test_replay.py::test_replay_jepi_padding -v`
- Evidence: curve 길이 = 10년 전체 거래일 (padding 포함)
- 통과 기준: PASSED, curve 시작일이 실제 JEPI 출시일보다 이전 (padding 구간 존재)

### G3.5 — 전체 unit test
- 명령: `python -m pytest backend/tests/unit/test_replay.py -v`
- Evidence: pytest 출력 paste
- 통과 기준: 0 failed

### G3.6 — QQQ 10년 equity curve PNG (의무)
- 명령: 별도 스크립트로 QQQ 10년 KRW 평가액 curve 생성 + matplotlib 저장
- Evidence: `verification/figures/step-3-replay-qqq.png` Read 도구 확인
- 통과 기준: 우상향 곡선, 2022년 하락 구간 가시적

---

## P2-4 (XL) — `strategy_a.py` + `strategy_b.py` + `portfolio.py`

**목표**: Tab B/C 핵심 전략 엔진. lock 사이클 복잡도 최대 — 마스터플랜 §3.4~§3.6 정확히 구현.

**핵심 lock**: D-6 (현지통화 트리거), D-7 (365일 강제 재매수), D-8 (재매수 시점 lock), D-9 (grace 12개월), D-16 (이벤트 순서)

### Sub-steps

- [ ] `strategy_a.py` — `StrategyA` class (마스터플랜 §3.4 코드 그대로, D-lock 적용)
- [ ] `strategy_b.py` — `StrategyB` class (마스터플랜 §3.5)
- [ ] `portfolio.py` — `Portfolio` class (마스터플랜 §3.6, 60/20/20 preset, 연 리밸런싱)
- [ ] `test_strategy.py` — grace period, lock 사이클, 강제 재매수 365일, 12월 강제 매수 (8 tests 이상)
- [ ] `test_portfolio.py` — preset 비중, 연 리밸런싱 동작 (4 tests 이상)
- [ ] verification/step-4-strategy.md + figures/step-4-lock-cycle.png

### G4.1 — grace period (D-9)
- 명령: `python -m pytest backend/tests/unit/test_strategy.py::test_strategy_a_grace_period -v`
- Evidence: pytest 출력 + grace 기간 중 급등 이벤트가 무시되는 로그/assertion paste
- 통과 기준: PASSED — 시작 후 12개월 이내 ratio≥1.20 이벤트 발생 시 매도 미실행

### G4.2 — lock 사이클 (D-7, D-8)
- 명령: `python -m pytest backend/tests/unit/test_strategy.py::test_strategy_a_lock_cycle -v`
- Evidence: sell_date → 365일 후 강제 재매수 → lock_until_year = 재매수 연도 순서 assert paste
- 통과 기준: PASSED — D-7 365일 계산, D-8 lock_until_year = 재매수 연도

### G4.3 — 현지통화 트리거 (D-6)
- 명령: `python -m pytest backend/tests/unit/test_strategy.py::test_strategy_a_local_currency_trigger -v`
- Evidence: USD 자산(QQQ) — ratio 계산이 USD 가격 기준임을 assert
- 통과 기준: PASSED

### G4.4 — 전략 B: 70/30 분할 + 12월 강제 매수
- 명령: `python -m pytest backend/tests/unit/test_strategy.py -k "strategy_b" -v`
- Evidence: 적립 시 70% 즉시/30% reserve, 12월 강제 매수 동작 assert
- 통과 기준: PASSED

### G4.5 — 포트폴리오: 연 리밸런싱
- 명령: `python -m pytest backend/tests/unit/test_portfolio.py -v`
- Evidence: 리밸런싱 후 60/20/20 비중 회복 assert (±5% 허용)
- 통과 기준: PASSED

### G4.6 — 전체 strategy unit test
- 명령: `python -m pytest backend/tests/unit/test_strategy.py backend/tests/unit/test_portfolio.py -v`
- Evidence: pytest 출력 paste
- 통과 기준: 0 failed, 12 tests 이상

### G4.7 — lock 사이클 시각화 PNG (의무)
- 명령: 별도 스크립트로 strategy_a 시뮬레이션 결과에 매도/재매수 이벤트 마킹 차트 생성
- Evidence: `verification/figures/step-4-lock-cycle.png` Read 도구 확인
- 통과 기준: 매도(빨강), 재매수(초록) 이벤트 마킹, 365일 간격 가시적

---

## P2-5 (M) — `routers/simulation.py` + `services/simulation_service.py`

**목표**: FastAPI 라우터 등록. Pydantic schema → service → simulation 모듈 호출. Bronze 영향 0.

### Sub-steps

- [ ] `api/services/simulation_service.py` — DB 조회 + simulation 호출 조율
- [ ] `api/routers/simulation.py` — `POST /v1/silver/simulate/replay` / `strategy` / `portfolio`
- [ ] `api/main.py`에 `include_router(simulation_router)` 추가
- [ ] 기존 라우터 영향 없음 확인 (Bronze 엔드포인트 smoke)

### G5.1 — API 기동 + replay 엔드포인트 응답
- 명령: `curl -X POST http://localhost:8000/v1/silver/simulate/replay -H "Content-Type: application/json" -d '{"asset_codes":["QQQ"],"monthly_amount":1000000,"period_years":3,"base_currency":"KRW"}'`
- Evidence: HTTP 200 + JSON 응답 구조 (curve 샘플 5행 + KPI) paste → verification/step-5-api.md
- 통과 기준: 200 OK, `curve` 배열 존재, `kpi.final_asset_krw` 양수

### G5.2 — Pydantic validation 오류 처리
- 명령: `curl -X POST http://localhost:8000/v1/silver/simulate/replay -d '{"asset_codes":["INVALID"],...}'`
- Evidence: 422 Unprocessable Entity 응답 paste
- 통과 기준: 422, `detail` 필드에 validation 오류 메시지

### G5.3 — 기존 Bronze 엔드포인트 영향 없음
- 명령: `curl http://localhost:8000/v1/prices?asset_id=KS200&limit=5`
- Evidence: 200 + Bronze 데이터 정상 응답 paste
- 통과 기준: 200 OK, 기존 Bronze 라우트 정상

---

## P2-6 (M) — `routers/fx.py` + `services/fx_service.py`

**목표**: `GET /v1/fx/usd-krw` 라우터. 날짜 범위 필터 지원. P2-5와 병렬 구현 가능.

### Sub-steps

- [ ] `api/services/fx_service.py` — fx_daily 조회 + forward-fill
- [ ] `api/routers/fx.py` — `GET /v1/fx/usd-krw?start=YYYY-MM-DD&end=YYYY-MM-DD`
- [ ] `api/main.py`에 `include_router(fx_router)` 추가

### G6.1 — fx 엔드포인트 기본 동작
- 명령: `curl "http://localhost:8000/v1/fx/usd-krw?start=2024-01-01&end=2024-01-31"`
- Evidence: 200 + JSON 응답 (행 수 + 첫/마지막 날짜) paste → verification/step-6-fx-api.md
- 통과 기준: 200 OK, 2024-01 거래일 수 ≈ 22, `usd_krw_close` 필드 존재

### G6.2 — row 수 DB 일치
- 명령: SQL `SELECT count(*) FROM fx_daily WHERE date BETWEEN '2024-01-01' AND '2024-01-31'` + curl count 비교
- Evidence: DB count == API 응답 count paste
- 통과 기준: 동일 (± forward-fill 차이 없음)

---

## P2-7 (L) — Integration Test + QQQ Cross-check

**목표**: QQQ 10년 적립 결과를 Portfoliovisualizer/curvo 외부 도구와 비교해 ±2% 이내 일치 검증.

### Sub-steps

- [ ] integration test 스크립트 작성 — API 호출 → KPI 추출
- [ ] Portfoliovisualizer에서 QQQ 10년 100만원/월 적립 결과 수동 캡처 (참고값)
- [ ] cross-check fixture 저장 (`fixtures/qqq_10y_replay_reference.json`)
- [ ] verification/step-7-crosscheck.md + figures/step-7-crosscheck.png

### G7.1 — QQQ 10년 KPI cross-check (의무)
- 명령: `curl -X POST http://localhost:8000/v1/silver/simulate/replay -d '{"asset_codes":["QQQ"],"monthly_amount":1000000,"period_years":10}'`
- Evidence: KPI 4종 수치 paste + Portfoliovisualizer 참고값 병기 → verification/step-7-crosscheck.md 표 형식
- 통과 기준: 최종자산 또는 총수익률이 외부 참고값과 ±2% 이내

### G7.2 — MDD 2022 합리성
- 명령: Python 스크립트로 QQQ 10년 curve에서 연도별 MDD 추출
- Evidence: 연도별 MDD dict paste (2022년 MDD 포함)
- 통과 기준: 2022년 MDD가 -25% ~ -35% 범위 (QQQ 실제 2022 하락 약 -32%)

### G7.3 — verification/ 전수 확인
- 명령: `ls dev/active/silver-rev1-phase2/verification/` + `ls dev/active/silver-rev1-phase2/verification/figures/`
- Evidence: 파일 목록 paste
- 통과 기준: step-1~step-7.md 7종 + figures/ PNG 3종 이상 존재

---

## 완료 기록

| 태스크 | 완료일 | commit hash |
|---|---|---|
| P2-1 | — | — |
| P2-2 | — | — |
| P2-3 | — | — |
| P2-4 | — | — |
| P2-5 | — | — |
| P2-6 | — | — |
| P2-7 | — | — |

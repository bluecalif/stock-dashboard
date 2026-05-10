# Phase 2 — 시뮬레이션 엔진
> Gen: silver
> Last Updated: 2026-05-10
> Status: Planning

## 1. Summary

**목적**: `research_engine/simulation/` 모듈 6개 파일 신규 작성 + API 라우터 2개 구현. Bronze 영향 0 (신규 라우트만 추가).

**범위**: 마스터플랜 §3 (시뮬레이션 엔진 명세) + §5.3 (API 라우터)

**예상 산출물**:
- `simulation/` 신규 파일: `fx.py`, `mdd.py`, `replay.py`, `strategy_a.py`, `strategy_b.py`, `portfolio.py`
- `api/routers/simulation.py`, `api/routers/fx.py`
- `api/services/simulation_service.py`, `api/services/fx_service.py`
- unit tests: `test_fx.py`, `test_mdd.py`, `test_replay.py`, `test_strategy.py`
- cross-check fixture: QQQ 10년 적립 KPI (Portfoliovisualizer ±2%)
- `verification/` evidence 7종 + PNG (lock 사이클, MDD bar chart, equity curve, cross-check)

## 2. Current State (Phase 1 인계)

Phase 1 완료 산출물 — Phase 2 즉시 사용 가능:

| 산출물 | 경로 | 상태 |
|---|---|---|
| simulation 패키지 | `simulation/__init__.py` | ✅ Phase 1 |
| cyclic padding | `simulation/padding.py` | ✅ Phase 1 (8 tests) |
| WBI synthetic | `simulation/wbi.py` | ✅ Phase 1 (8 tests) |
| JEPI fixture | `simulation/fixtures/jepi_5y_returns.npy` | ✅ |
| WBI fixture | `simulation/fixtures/wbi_seed42_10y.npz` | ✅ |
| fx_daily 테이블 | DB (2,603행, 2016~2026) | ✅ |
| price_daily | DB (15자산, 37,671행, 10년) | ✅ |
| asset_master | DB (15행, currency/annual_yield/allow_padding) | ✅ |

## 3. Target State

Phase 2 완료 시:
- `simulation/` 8개 파일 완성: `__init__` + `padding` + `wbi` + `fx` + `mdd` + `replay` + `strategy_a` + `strategy_b` + `portfolio`
- API 엔드포인트 4종 동작:
  - `POST /v1/silver/simulate/replay` — Tab A 적립식
  - `POST /v1/silver/simulate/strategy` — Tab B (전략 A/B)
  - `POST /v1/silver/simulate/portfolio` — Tab C
  - `GET /v1/fx/usd-krw` — 환율 시계열 조회
- QQQ 10년 적립 KPI가 Portfoliovisualizer/curvo 외부 도구와 ±2% 일치
- lock 사이클 unit test PASSED, grace period 검증 PASSED
- verification/ evidence 7종 + PNG 3종 누적

## 4. Implementation Stages

| Stage | 태스크 | 핵심 내용 | Bronze 영향 |
|---|---|---|---|
| A | P2-1, P2-2 | 디렉터리 확인 + `fx.py` + `mdd.py` | 0 |
| B | P2-3 | `replay.py` (적립식 Tab A 엔진) | 0 |
| C | P2-4 | `strategy_a.py` + `strategy_b.py` + `portfolio.py` | 0 |
| D | P2-5, P2-6 | API 라우터 + 서비스 계층 등록 | 0 (신규 라우트) |
| E | P2-7 | integration test + QQQ cross-check | 0 |

## 5. Task Breakdown

| # | 태스크 | Size | 의존성 | 비고 |
|---|---|---|---|---|
| P2-1 | 디렉터리 구조 확인 + `__init__.py` exports 정비 | S | Phase 1 | `simulation/` 이미 존재 — 확인 + 정비 |
| P2-2 | `fx.py` + `mdd.py` (utility 나머지 2종) | M | P2-1 | padding/wbi는 Phase 1 완료 |
| P2-3 | `replay.py` — 적립식 Tab A | L | P2-2, fx_daily, asset_master | D-4/D-16/D-3 락 |
| P2-4 | `strategy_a.py` + `strategy_b.py` + `portfolio.py` | XL | P2-3 | D-6/D-7/D-8/D-9 lock 복잡도 최대 |
| P2-5 | `routers/simulation.py` + `services/simulation_service.py` | M | P2-4 | Pydantic schema + FastAPI DI |
| P2-6 | `routers/fx.py` + `services/fx_service.py` | M | fx_daily | 독립 라우터 (P2-5와 병렬 가능) |
| P2-7 | integration test + QQQ cross-check fixture | L | P2-5 | Portfoliovisualizer ±2% |

## 6. Risks & Mitigation

| 리스크 | 영향 | 대응 |
|---|---|---|
| lock 사이클 복잡도 (D-7~D-9) | replay 결과 오차 | 마스터플랜 §3.4 코드 스니펫 그대로 구현, 단계별 unit test |
| fractional 정밀도 미확정 (C-2) | 결과 불일치 | float64 가정으로 진행, 사용자 확인 후 조정 |
| QQQ cross-check ±2% 초과 | 출시 기준 미충족 | 배당 처리 / 환율 forward-fill / 적립일 정의 재확인 |
| USD 자산 KR 휴장일 결측 | forward-fill 누락 | `fx.py` + `prices.py` forward-fill 로직 + 시각 검증 PNG |
| 매 요청 재계산 latency | UX 체감 | Phase 5로 defer (P95 임계 미초과 가정) |
| FastAPI router 등록 순서 | 경로 충돌 | main.py include_router 순서 + 기존 라우트 영향 없음 확인 |

## 7. Dependencies

**내부 (Phase 1 완성)**:
- `backend/research_engine/simulation/padding.py`
- `backend/research_engine/simulation/wbi.py`
- `backend/db/models/` — `FxDaily`, `AssetMaster`
- `backend/api/main.py` — 라우터 등록 위치

**외부**:
- numpy — MDD `np.maximum.accumulate`, fx forward-fill
- pandas — trading_days groupby, resample
- FastAPI — Pydantic v2 schema, DI
- dateutil.relativedelta — grace period 12개월 계산

**기준 문서**:
1. `docs/silver-masterplan.md` §3 — 시뮬레이션 엔진 명세 (single SoT)
2. `docs/silver-masterplan.md` §5.3 — API 라우터 변경
3. `dev/active/project-overall/project-overall-context.md` — D-1~D-21 결정표

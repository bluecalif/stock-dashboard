# Project Overall Plan — Silver Gen
> Gen: silver
> Last Updated: 2026-05-10
> Status: In Progress (Phase 1 ✅ 완료, Phase 2 ✅ 완료, Phase 3 미착수)

## 1. Summary (개요)

**목적**: Bronze gen(MVP + Post-MVP)에서 운영 중인 Stock Dashboard를 **초보 투자자용 적립식 비교 도구**로 재설계. IA/데이터/시뮬레이션을 모두 다시 짜는 별개 제품 — Bronze 폴리시가 아니라 **다른 제품**으로 cut-over.

**범위**: `docs/silver-masterplan.md` §1~§12를 single source of truth로 따른다.
- 자산 universe 7종 → **13종 + WBI synthetic** (QQQ/SPY/SCHD/JEPI/TLT/NVDA/GOOGL/TSLA 신규)
- 메인 진입을 **`/silver/compare` 적립식 비교 (Tab A/B/C)** 단일 메뉴로 재편
- 기존 페이지 4종(Dashboard/Price/Correlation/Strategy) drop, IndicatorSignalPage는 단순화 후 `/silver/signals`로 이전
- Agentic AI(Bronze Phase F)는 유지하되 tool 정리

**예상 결과물 (Silver gen 종료 시)**:
- `fx_daily` 테이블, `asset_master` 5컬럼 추가, backtest_* 3테이블 drop
- `backend/research_engine/simulation/` 모듈 (replay/strategy_a/strategy_b/portfolio/padding/wbi/fx/mdd)
- `/v1/silver/simulate/{replay,strategy,portfolio}` + `/v1/fx/usd-krw` 라우터
- `pages/silver/CompareMainPage.tsx` + 10개 컴포넌트 + `SignalDetailPage.tsx`
- 빅뱅 cut-over 완료 (`v-bronze-final` tag로 보존)

## 2. Current State (Phase 2 ✅ 완료, 2026-05-10)

### Phase 2 산출물 (2026-05-10)
- `simulation/` 패키지 8파일 완성 (`__init__` + `padding` + `wbi` + `fx` + `mdd` + `replay` + `strategy_a` + `strategy_b` + `portfolio`)
- API 4종 동작: `/v1/silver/simulate/{replay,strategy,portfolio}` + `/v1/fx/usd-krw`
- 61 unit tests PASSED (fx 7 + mdd 8 + replay 10 + strategy 13 + portfolio 7 + padding 8 + wbi 8)
- QQQ 10년 DCA cross-check: 총수익률 +283.99%, 연환산 +14.40%, worst MDD -26.24% (2020 COVID)
- verification/ evidence 7종 + PNG 3종 + fixtures/qqq_10y_replay_reference.json

### Phase 3 진입 조건
- ✅ Phase 2 API 계약 확정 (`/v1/silver/simulate/*`, `/v1/fx/usd-krw`)
- dev/active/silver-rev1-phase3/ 작성 필요 (미착수)

### Phase 1 산출물 (2026-05-09)
- `asset_master` 10컬럼 (5+5), 15행 (Bronze 7 + Silver 8), alembic head `d8334483342c`
- `fx_daily` 2,603행 (2016~2026 USD/KRW)
- `price_daily` 37,671행 / 15자산 (전체 10년 backfill)
- `fdr_client.py` 15종 SYMBOL_MAP + int32 overflow / high-low swap 버그 수정
- `fx_collector.py` + `seed_silver_assets.py` + `backfill_silver_phase1.py` 신규
- `research_engine/simulation/` 패키지 초기화: `padding.py` + `wbi.py` + fixtures 2종
- 16 unit tests PASSED (test_padding 8 + test_wbi 8)
- verification/ 6 evidence 파일 + 3 PNG

## 2b. Original Current State (Bronze gen 종료 시점 인계 사항)

- **Bronze 운영중**: master 배포 + GitHub Actions 일일 자동 수집 + Agentic chat 운영
- **자산 7종**: KS200/005930/000660/SOXL/BTC/GC=F/SI=F (FDR 기반)
- **DB 테이블 8종**: asset_master, price_daily, factor_daily, signal_daily, backtest_run, backtest_equity_curve, backtest_trade_log, job_run
- **API 12개 엔드포인트** + Agentic tool 5종 (dashboard_summary, price_lookup, correlation_matrix, strategy_classify, strategy_report)
- **프론트 6 페이지**: Dashboard/Price/Correlation/Strategy/IndicatorSignal/Chat
- **Bronze archive**: `dev/archive/bronze-gen/` (phase1-skeleton ~ phaseG-context, project-overall)

## 3. Target State (Silver gen 종료 시점)

- **자산 universe 13종 + WBI synthetic** (KRW/USD 혼재, 환율 변환 적용)
- **DB**: fx_daily 신규, asset_master 5컬럼 확장, backtest_* 3테이블 drop
- **API**: simulation/* 3종 + fx/* 1종 신규, backtests 라우터 제거
- **프론트**: `/silver/compare` 메인(3탭) + `/silver/signals` + chat/login/profile. 기타 라우트는 `/silver/compare` redirect.
- **Agentic tool**: simulation_replay/strategy/portfolio 3종 신규, strategy_classify/report 제거
- **운영**: 빅뱅 cut-over 완료, 1주 monitoring 안정화 종료

## 4. Implementation Stages

마스터플랜 §8 그대로:

| Stage | Phase 폴더 | 범위 | Bronze 영향 |
|---|---|---|---|
| A | `silver-rev1-phase1` | 데이터 인프라 (스키마 + collector + backfill) | **0** (DEFAULT 컬럼 + 신규 테이블) |
| B | `silver-rev1-phase2` | 시뮬레이션 엔진 + simulation/fx 라우터 | **0** (Silver 라우트 신규) |
| C | `silver-rev1-phase3` | 프론트 신규 페이지 (병행 운영) | **0** (Bronze 라우트 동시 노출) |
| D | `silver-rev1-phase4` | **빅뱅 cut-over** (코드/DB drop + redirect) | **다운타임 수 분** |
| E | `silver-rev1-phase5` | 후속 안정화 (배당락 데이터, 캐시) | 없음 |

### 4.1 모든 Stage 공통 종료 조건 — "Show, don't claim" (context.md §0)
- 모든 검증 게이트 = 명령 / Evidence / 통과 기준 3단 형식
- 각 step 종료 시 `dev/active/silver-rev1-phaseN/verification/step-K-<topic>.md` 작성
- 수치·시계열·분포 step = PNG 차트 의무 (`verification/figures/`)
- 체크 표시는 evidence paste + 사용자 노출 시에만 가능

## 5. Task Breakdown (Phase별 요약)

> 상세 태스크는 `project-overall-tasks.md` + 각 Phase의 `-tasks.md`. 여기는 Phase 단위 사이즈만 표기.

| Phase | Size | 의존성 | 주요 산출 |
|---|---|---|---|
| Phase 1 | L | 마스터플랜 §2/§5.1/§7 | migration, SYMBOL_MAP 8종, fx_collector, padding fixture, WBI fixture |
| Phase 2 | XL | Phase 1 (데이터 + fx_daily) | simulation 모듈 8개 파일 + 라우터 2개 + cross-check fixture |
| Phase 3 | L | Phase 2 (API 계약 확정) | CompareMainPage + 10 컴포넌트 + SignalDetailPage + 모바일 반응형 |
| Phase 4 | M | Phase 1~3 staging 검증 완료 | git tag, 코드 삭제, 테이블 drop, redirect, Agentic tool 정리 |
| Phase 5 | S | Phase 4 안정화 (1주) | 배당락 도입 검토, 캐시 도입 검토, alerting 확장 |

## 6. Risks & Mitigation

마스터플랜 §11.4 + Part B 7대 허들 매핑:

| 리스크 | 영향 | 대응 |
|---|---|---|
| JEPI 5년 padding 거부감 | UX 신뢰도 | 차트 padding 구간 회색 처리 + 라벨 (`§2.6`) |
| 빅뱅 cut-over 실패 | 다운타임 연장 | T-1d DB 백업 + `v-bronze-final` tag로 30분 내 rollback |
| Agentic tool 정리 누락 | chat 오작동 | LangGraph fallback 동작 검증 + simulation_* tool 등록 후 smoke test |
| Tab A 캘린더 정렬 | 차트 왜곡 | forward-fill 가정 + 시각적 검증 (Phase 3) |
| 시뮬레이션 P95 latency | 사용자 체감 | 매 요청 재계산 → P95 임계 초과 시 캐시 도입 (Phase 5) |
| fractional 정밀도 미확정 | 결과 reproducibility | 12자리 가정으로 진행, 사용자 확인 후 조정 |

## 7. Dependencies

**내부**:
- `backend/collector/fdr_client.py` — SYMBOL_MAP 확장 시작점
- `backend/db/models/` — asset_master 모델, fx_daily 신규 모델
- `backend/research_engine/` — simulation/ 신규 디렉터리
- `backend/api/routers/` — simulation.py, fx.py 신규 / backtests.py 제거
- `backend/api/services/llm/agentic/` — tool registration 정리
- `frontend/src/pages/` — silver/ 디렉터리 신규, 기타 페이지 drop
- `frontend/src/App.tsx` — 라우트 재편

**외부**:
- FinanceDataReader (FDR) — 신규 8종 + USD/KRW 일봉
- numpy — WBI GBM 시뮬레이션, padding cyclic
- Recharts — EquityChart multi-series
- Alembic — schema migration

**기준 문서**:
1. `docs/silver-masterplan.md` (단일 source of truth)
2. `docs/draft-rev1.md` (§1.1 lock 항목 인용)
3. `docs/silver-rev1-analysis.md` (Part B/C/D)
4. `docs/UX-design-ref.JPG` (다크톤 디자인 레퍼런스)

## 8. Bronze gen 인계 / 보존 사항

- `dev/archive/bronze-gen/` — Phase 1~7, A~G 완료 상태 보존
- `project-wrapup/` — 교훈 41건, 재사용 패턴 9개, 설계 순서도 (Silver 작업 시 참조)
- 빅뱅 직전 git tag `v-bronze-final` 생성 예정 (Phase 4)
- A-004 교훈: **대시보드 ↔ Agentic 데이터 소스 일치** — Silver에서도 simulation API 단일 소스 유지

# Session Compact

> Generated: 2026-05-09
> Source: /close-day

## Goal

Silver gen Phase 1 (Data Infra) 완전 완료 + "Show, don't claim" 검증 정책 도입 + WBI 명칭 확정 (Warren Buffett Index) + hook 절대 경로 버그 수정 + Bronze 7종 10년 backfill 추가.

## Completed

- [x] **Phase 1 전체 완료 (6/6 태스크)**
  - P1-1: Alembic migration `d8334483342c` — asset_master 5컬럼 + fx_daily (`7d457a2`)
  - P1-2: SYMBOL_MAP 15종 (Silver 8 신규, D-1 JEPI 통일) (`0eea282`)
  - P1-3: `fx_collector.py` USD/KRW UPSERT + idempotent (`ba574c0`)
  - P1-4: seed 15행 + 15자산 37,671행 backfill + fx_daily 2,603행 (`7d24d68`, `63ecb80`)
  - P1-5: `padding.py` cyclic+reverse-cumprod + JEPI fixture + 8 tests PASSED (`391f27f`)
  - P1-6: `wbi.py` Warren Buffett Index GBM seed=42 + fixture + 8 tests PASSED (`391f27f`)

- [x] **"Show, don't claim" 검증 정책 도입** (`4843ffa`)
  - project-overall-context.md §0 + phase1 context §0 + tasks 3단 게이트 형식
  - verification/ 디렉터리: README + 6 evidence 파일 + 3 PNG
  - /dev-docs, /step-update 슬래시 명령에 baked-in (`ac36b62`)

- [x] **버그 수정 2건** (`63ecb80`)
  - `fdr_client.py` volume `astype(int)` → `astype("int64")` (NVDA int32 overflow)
  - `fdr_client.py` BTC high/low inversion swap (2016~2017 FDR 아티팩트)

- [x] **WBI → Warren Buffett Index 명칭 확정** (`9c135ca`)
  - silver-masterplan.md, SKILL.md, wbi.py 등 8개 파일 업데이트

- [x] **Hook 절대 경로 수정** — `.claude/settings.json` 상대 경로 → 절대 경로
  - 원인: PowerShell `-File` spawn CWD != 프로젝트 루트
  - User CLAUDE.md + Projects CLAUDE.md에 규칙 추가 + memory 저장

- [x] **Bronze 7종 10년 backfill 추가** (`63ecb80`)
  - Railway prod: price_daily 37,671행 / 15자산 (모두 10년)

- [x] **bird-view.md 신규 생성** — 전체 파이프라인 + Silver gen 신규 모듈 포함

- [x] **step-update --sync-overall** + push (remote: `9980052`)

## Current State

- **Railway prod DB**: asset_master 15행, price_daily 37,671행, fx_daily 2,603행
- **alembic head**: `d8334483342c` (silver_rev1_schema_changes)
- **simulation 패키지**: `padding.py` + `wbi.py` + fixtures 2종 (Phase 2 즉시 사용 가능)
- **Bronze 운영 중** (Agentic AI, 일일 수집 cron) — Phase 4 cut-over 전까지 영향 0
- **Phase 1 DoD**: 전체 ✅ (Bronze cron G4.5 24h 확인만 내일 체크)

### Changed Files (오늘 세션)
- `backend/db/models.py` — AssetMaster 5컬럼 + FxDaily 모델
- `backend/db/alembic/versions/d8334483342c_*.py` — migration
- `backend/collector/fdr_client.py` — SYMBOL_MAP 15종 + int64 + high/low swap
- `backend/collector/fx_collector.py` *(신규)*
- `backend/collector/seed_silver_assets.py` *(신규)*
- `backend/research_engine/simulation/__init__.py` *(신규)*
- `backend/research_engine/simulation/padding.py` *(신규)*
- `backend/research_engine/simulation/wbi.py` *(신규)*
- `backend/research_engine/simulation/fixtures/jepi_5y_returns.npy` *(신규)*
- `backend/research_engine/simulation/fixtures/wbi_seed42_10y.npz` *(신규)*
- `backend/tests/unit/test_padding.py` *(신규)* — 8 tests
- `backend/tests/unit/test_wbi.py` *(신규)* — 8 tests
- `docs/silver-masterplan.md` — WBI 명칭 갱신
- `docs/bird-view.md` *(신규)*
- `.claude/settings.json` — hook 절대 경로
- `~/.claude/commands/dev-docs.md`, `step-update.md` — "Show, don't claim" 정책
- `dev/active/silver-rev1-phase1/` 전체 (tasks/plan/context/debug-history/verification/)
- `dev/active/project-overall/` 전체 (tasks 6/29, plan Phase1 완료)

## Remaining / TODO

### Phase 1 후속 (소규모)
- [ ] G4.5 Bronze cron 24h 확인 — tomorrow: `select asset_id, max(date) from price_daily where asset_id in ('KS200','005930','000660','SOXL','BTC','GC=F','SI=F') group by asset_id`

### Phase 2 진입 필요 (시뮬레이션 엔진)
- [ ] `/dev-docs create phase 2 silver-rev1-phase2` — dev-docs 작성
- [ ] P2-1: `simulation/` 디렉터리 구조 완성 (`replay.py` / `strategy_a.py` / `strategy_b.py` / `portfolio.py` / `fx.py` / `mdd.py`)
- [ ] P2-2: utility 4종 (fx.py USD↔KRW forward-fill, mdd.py 캘린더 연도 MDD)
- [ ] P2-3: `replay.py` — 적립식 Tab A (매월 첫 거래일 + 배당 재투자 D-4)
- [ ] P2-4 (XL): `strategy_a.py` lock 사이클 (D-6~D-9) + `strategy_b.py` + `portfolio.py`

## Key Decisions

### 오늘 확정된 결정
- **WBI = Warren Buffett Index** (연 20% 복리 가정, KRW, GBM seed=42)
- **GBM 검증**: seed=42 단일 경로 ≠ 20% (정상). log-drift + 100-seed ensemble로 검증
- **volume int64**: `fdr_client._standardize`에서 `astype("int64")` — US 고거래량 int32 overflow
- **Hook 절대 경로**: PowerShell `-File`은 spawn CWD 기준 → settings.json 절대 경로 필수
- **prod = staging**: Railway 단일 DB, backward-compatible 변경만 prod에 직접 적용
- **asset_master 15행** (Bronze 7 + Silver 8, WBI 제외): 계획서 13행 오기

### Silver gen D-lock (핵심, Phase 2 필수 확인)
- **D-7**: 강제 재매수 = 매도일 + 365일 (12월 말 X)
- **D-8**: lock_until_year 갱신 = **재매수 시점** (매도 시점 X)
- **D-9**: grace period = 12개월 (적립 시작 후)
- **D-6**: 트리거 ratio = **현지통화 가격** 기준 (USD 자산 = USD 가격)
- **D-16**: 이벤트 순서 = **정기 적립 먼저** → strategy.step()
- **D-4**: 배당 = annual_yield / 252 × 보유평가액 (매 거래일)

## Context

다음 세션에서는 답변에 한국어를 사용하세요.

### 핵심 참조 파일
1. `docs/silver-masterplan.md` — single source of truth (871줄)
2. `dev/active/project-overall/project-overall-context.md` — D-1~D-21 결정표
3. `dev/active/project-overall/project-overall-tasks.md` — 6/29 완료
4. `dev/active/silver-rev1-phase1/` — Phase 1 완료 상태 (verification/ 포함)
5. `docs/bird-view.md` — 전체 파이프라인 조감도 (오늘 신규)
6. `.claude/skills/silver-simulation/SKILL.md` — Phase 2 코딩 시 자동 활성화

### 환경
- Railway prod DB (단일, staging 없음)
- GitHub Actions 일일 cron (Bronze 운영 중)
- pytest: `backend/tests/unit/test_padding.py` + `test_wbi.py` 16/16 PASSED

## Next Action

### 단기 (내일/다음 세션)
- **G4.5 확인** (2분): Bronze 7자산 max(date) = 오늘 T-1 영업일 확인
- **`/dev-docs create phase 2 silver-rev1-phase2`** 호출 → Phase 2 dev-docs 작성 (M)
- **P2-2 utility 4종** 착수 — `fx.py` (USD↔KRW forward-fill) + `mdd.py` (캘린더 MDD)

### 중기 (이번 주)
- Phase 2 P2-1~P2-4 (시뮬레이션 엔진 핵심): replay / strategy_a / strategy_b / portfolio
- `/v1/silver/simulate/*` 라우터 등록 (P2-5~P2-6)
- QQQ 10년 적립 cross-check fixture (P2-7, Portfoliovisualizer 비교 ±2%)

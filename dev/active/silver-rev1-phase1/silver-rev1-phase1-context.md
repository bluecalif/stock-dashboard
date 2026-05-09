# Silver rev1 — Phase 1: Context
> Gen: silver
> Last Updated: 2026-05-09

## 1. 핵심 파일 (Phase 1에서 매번 열어야 함)

### 1.1 기준 문서
| 파일 | 섹션 | 용도 |
|---|---|---|
| `docs/silver-masterplan.md` | §2.1~§2.7 | 자산 13종 + WBI 정의, padding 알고리즘, asset_master 스키마 |
| `docs/silver-masterplan.md` | §5.1 | migration SQL — copy-paste 시작점 |
| `docs/silver-masterplan.md` | §5.2 | SYMBOL_MAP / fx_collector 코드 예시 |
| `docs/silver-masterplan.md` | §7 | backfill 우선순위 + 검증 항목 |
| `docs/silver-masterplan.md` | §9.1 | Unit test 명세 (padding/wbi) |
| `dev/active/project-overall/project-overall-context.md` | §3 D-1~D-5 | Phase 1과 직결되는 lock 결정 |

### 1.2 코드 진입점
| 파일 | 위치 | 작업 |
|---|---|---|
| `backend/db/models.py` | `class AssetMaster` (line 25) | 5컬럼 추가 |
| `backend/db/models.py` | 파일 끝 또는 `PriceDaily` 다음 | `class FxDaily` 신규 |
| `backend/db/alembic/env.py` | `target_metadata` | `Base.metadata` 자동 인식 확인 |
| `backend/db/alembic/versions/c4d2e5f6a789_*` | head revision | Phase 1 migration의 `down_revision` |
| `backend/collector/fdr_client.py:14` | `SYMBOL_MAP` | 8 엔트리 추가 |
| `backend/collector/fdr_client.py:33` | `_fetch_raw` | fx_collector에서 재사용 (FDR 호출) |
| `backend/collector/ingest.py:30` | `_upsert` | UPSERT 패턴 참조 (fx는 source PK 없음) |
| `backend/collector/alerting.py` | `send_discord_alert` | fx_collector 실패 알림 재사용 |
| `backend/collector/__init__.py` | export | `fx_collector` 추가 시 노출 검토 |

### 1.3 신규 작성 파일
| 경로 | 역할 | Phase |
|---|---|---|
| `backend/db/alembic/versions/<hash>_silver_rev1_schema_changes.py` | migration | P1-1 |
| `backend/collector/fx_collector.py` | USD/KRW 수집기 | P1-3 |
| `backend/collector/seed_silver_assets.py` | asset_master 13행 시드 | P1-4 |
| `backend/scripts/verify_phase1_backfill.sql` | row count / 결측 검증 | P1-4 |
| `backend/research_engine/simulation/__init__.py` | 빈 패키지 마커 | P1-5 |
| `backend/research_engine/simulation/padding.py` | cyclic returns 알고리즘 | P1-5 |
| `backend/research_engine/simulation/wbi.py` | GBM 시드 42 함수 | P1-6 |
| `backend/research_engine/simulation/fixtures/wbi_seed42_10y.npz` | WBI 사전계산 결과 | P1-6 |
| `backend/research_engine/simulation/fixtures/jepi_5y_returns.parquet` (or `.npy`) | padding test fixture | P1-5 |
| `backend/tests/test_padding.py` | unit test | P1-5 |
| `backend/tests/test_wbi.py` | unit test | P1-6 |

## 2. 데이터 인터페이스

### 2.1 입력
- **FDR (FinanceDataReader)**:
  - 신규 8 자산 일봉: `QQQ / SPY / SCHD / JEPI / TLT / NVDA / GOOGL / TSLA` (모두 `<TICKER>` 그대로)
  - USD/KRW 환율: `fdr.DataReader("USD/KRW", start, end)` → DataFrame `Close` 컬럼 사용
  - JEPI 실제 상장일: 2020-05-20 (약 6년 history) → `history_start_date` 컬럼에 명시
- **마스터플랜 §2.4 fixture**: 자산별 `annual_yield` (SCHD 3.5%, JEPI 8.0%, TLT 3.8%, SPY 1.3%, QQQ 0.6%, KS200 1.5%, 005930 2.5%, 000660 1.0%, NVDA/GOOGL/TSLA/BTC/WBI 0.0%) — `seed_silver_assets.py` 상수

### 2.2 출력
- `asset_master` (10컬럼) — 13행 (Bronze 7 + 신규 6 — JEPI 포함; WBI는 row 미생성, Phase 2 fixture 처리)
- `fx_daily` — 10년치 row, `(date PK, usd_krw_close)`
- `price_daily` (staging) — 신규 8 자산 × 10년 (JEPI ≈ 6년 실제 데이터, padding은 시뮬레이션 시점에 적용)
- 코드 export:
  - `from research_engine.simulation.padding import pad_returns, prices_with_padding`
  - `from research_engine.simulation.wbi import generate_wbi`
  - `from collector.fx_collector import collect_usd_krw, upsert_fx_daily`

### 2.3 Phase 2 인계
- Phase 2 `simulation/replay.py`는 다음을 가정:
  - `asset_master.currency`로 자산 통화 분기 (USD → fx_daily 환산)
  - `asset_master.annual_yield`로 일별 배당 계산 (`/252`)
  - `asset_master.allow_padding=True`인 자산만 padding 적용
  - WBI는 fixture 파일 직접 import (DB 조회 X)

## 3. 주요 결정사항 (Phase 1 적용)

| ID | 결정 | 출처 | Phase 1 코딩 영향 |
|---|---|---|---|
| D-1 | JEPY → JEPI 통일 | Q1-1 | `SYMBOL_MAP` 키 = "JEPI", `display_name` = "JEPI" |
| D-2 | padding = 일별 수익률 cyclic + reverse-cumprod | Q1-2 | `padding.py` 알고리즘 — 가격 직접 복제 X |
| D-3 | USD/KRW 신규 테이블 | Q1-3 | `fx_daily` 테이블 + `fx_collector.py` |
| D-4 | 배당 = 공시률 / 252 | Q1-4 | `asset_master.annual_yield` 컬럼 + fixture 시드 |
| D-5 | WBI = GBM σ=1%/일, 시드 42, KRW | Q2-5/6 | `wbi.py` `default_rng(42)`, fixture pre-compute |
| D-22 | fractional 정밀도 12자리 (가정) | 후속 | Phase 1은 영향 없음 — Phase 2에서 사용자 확인 |

### 3.1 Phase 1에서 결정해야 할 (Phase 2/3 영향 X)
- **migration revision id**: alembic 자동 생성 hash 사용 (수동 지정 X)
- **fx_daily에 source 컬럼 추가 여부**: **추가 안 함** — 마스터플랜 §2.3은 `(date, usd_krw_close)` 2컬럼 + `created_at`. 향후 source 다양화 시 별도 migration
- **JEPI history slice**: FDR 응답 그대로 적재(`2020-05-20~`), padding은 시뮬레이션 시점에 적용 (저장 시 패딩 X) — DB는 raw 유지가 원칙
- **WBI fixture 파일 형식**: `.npz` (numpy 표준, 외부 의존 없음) — parquet은 padding fixture에만 사용
- **seed 스크립트 위치**: `backend/collector/seed_silver_assets.py` (collector 패키지 안) — 추후 Phase 4 cut-over 시 prod로 동일 스크립트 실행

### 3.2 트레이드오프 메모
- **`fx_daily`에 source 컬럼 미포함**: PK 단순화. 향후 멀티 source 필요 시 새 컬럼 추가 migration으로 해결
- **`AssetMaster.allow_padding` 기본값 False**: 기존 7자산은 모두 10년+ → False, 신규 자산도 JEPI만 True. Bronze 영향 0
- **JEPI fixture 5년 vs 실제 6년**: 마스터플랜 §2.6은 "5년"으로 기술. 실제 데이터는 약 6년이지만 test fixture는 정확히 5년(1260 거래일)으로 슬라이스해 결정성 확보
- **WBI fixture pre-compute**: 매 시뮬레이션 호출마다 GBM 재실행하면 속도/결정성 저하 → 10년 fixture 한 번 만들어두고 재사용. 시드 42 + numpy 버전 고정으로 reproducibility

## 4. 컨벤션 체크리스트 (Phase 1 적용)

### 4.1 인코딩 (CLAUDE.md)
- `seed_silver_assets.py`의 `display_name` 한국어 ("엔비디아", "구글", "테슬라" 등) → 파일 상단 `# -*- coding: utf-8 -*-` 또는 Python 3 기본 UTF-8
- DB 클라이언트 인코딩: `psycopg2` 기본 UTF-8 — 추가 설정 불필요. 단, `.csv` fixture 읽을 때 `encoding='utf-8-sig'`

### 4.2 커밋 / 브랜치
- 브랜치: `feature/silver-rev1` (Phase 4까지 단일 브랜치 유지, Phase 5는 별 브랜치 가능)
- 커밋 단위 (`/step-update` 호출 기준):
  ```
  [silver-rev1-phase1] Step 1.1: AssetMaster 5컬럼 + FxDaily 모델 추가
  [silver-rev1-phase1] Step 1.2: alembic migration silver_rev1_schema_changes
  [silver-rev1-phase1] Step 2.1: SYMBOL_MAP 8 엔트리 추가 (QQQ/SPY/SCHD/JEPI/TLT/NVDA/GOOGL/TSLA)
  [silver-rev1-phase1] Step 3.1: fx_collector USD/KRW 일봉 수집기
  [silver-rev1-phase1] Step 4.1: seed_silver_assets 13행 + staging backfill 스크립트
  [silver-rev1-phase1] Step 5.1: padding 알고리즘 + JEPI fixture + unit test
  [silver-rev1-phase1] Step 6.1: WBI generate_wbi + 시드 42 fixture + unit test
  ```

### 4.3 Bash / PowerShell (CLAUDE.md)
- Git Bash에서 alembic 실행: `cd /c/Projects-2026/active/stock-dashboard/backend && alembic upgrade head`
- PowerShell `$` 변수 → Bash tool에서 `.ps1` 분리 작성, `&&` 체인 금지
- staging DB 접속 검증 시 `.env.staging` (PowerShell `$env:DATABASE_URL` 직접 노출 금지)

### 4.4 데이터 / 스키마
- `asset_master` 모든 신규 컬럼은 **DEFAULT 또는 nullable** — Bronze 영향 0 보장
- `fx_daily.created_at`은 `server_default=func.now()` (마스터플랜 §5.1 `TIMESTAMPTZ DEFAULT NOW()` 와 일치)
- `price_daily` 변경 X — 신규 자산 데이터는 기존 스키마로 적재
- migration downgrade는 항상 reversible (Phase 1은 destructive 변경 없음)

### 4.5 Test
- `pytest backend/tests/test_padding.py backend/tests/test_wbi.py -v`
- fixture 파일 경로: 테스트에서 `Path(__file__).parent.parent / "research_engine/simulation/fixtures" / "..."`
- numpy reproducibility: `np.random.default_rng(seed=42)` 사용. legacy `np.random.seed` 사용 X
- 부동소수 비교: `np.testing.assert_allclose(actual, expected, rtol=1e-3)` (±0.1% padding 평균)

### 4.6 Convention ENFORCEMENT (project-wrapup 패턴)
- collector: `idempotent-upsert.py` 패턴 차용 (`fx_collector.upsert_fx_daily`)
- model: `cascade-fk-models.py` 영향 없음 (Phase 1은 FK 추가 X)
- API: Phase 1은 라우터 작성 X (Phase 2)

## 5. Phase 1 미해결 → Phase 2/3 이월

| 이월 항목 | Phase | 사유 |
|---|---|---|
| 자산 calendar forward-fill 정책 | Phase 2 (`fx.py`) | Phase 1은 raw 저장에 집중. 캘린더 비대칭 처리는 시뮬레이션 시점 |
| fractional 정밀도 12자리 (D-22) | Phase 2 | Phase 1은 정밀도 무관 (row 적재만) |
| 알림(`alerting.py`) 신규 자산 확장 | Phase 1 후반 (P1-4 종료 후) | backfill 안정화 확인 후 일일 cron에 신규 자산 합류 |
| 실제 배당락 데이터 도입 | Phase 5 | rev1은 공시 균등 분할 (D-4) |

## 6. Bronze 교훈 적용 (project-wrapup/lessons-learned.json)

- **A-004**: Phase 1 시점에는 frontend 영향 없음, 단 Phase 2 simulation API가 Agentic tool과 단일 source가 되어야 하므로 **Phase 1 fixture는 Phase 2 코드가 그대로 import** (file-based fixture로 Agentic↔frontend 동일성 보장 첫 단계)
- **idempotent-upsert.py** (재사용 패턴): `_upsert` 함수 그대로 fx_collector에 적용
- **cascade-fk-models.py**: Phase 1은 FK 변경 X — 패턴 미적용
- **운영 안정성**: migration apply 후 Bronze 일일 cron 1회는 staging에서 dry-run, 1회는 prod에서 모니터링 후 다음 단계 진행

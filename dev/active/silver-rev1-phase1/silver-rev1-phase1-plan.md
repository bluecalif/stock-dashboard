# Silver rev1 — Phase 1: 데이터 인프라
> Gen: silver
> Last Updated: 2026-05-09
> Status: Planning (코딩 진입 직전, 0/6 태스크)

## 1. Summary

**목적**: Silver gen이 요구하는 자산 universe(13종 + WBI synthetic) 및 환율(USD/KRW) 데이터 인프라를 Bronze 운영에 영향 0으로 마련한다. Phase 2 시뮬레이션 엔진이 즉시 호출 가능한 상태(스키마 + 일봉 10년 + asset_master 메타 + 검증된 padding/WBI fixture)까지가 본 Phase의 종착선이다.

**범위**:
- Alembic migration 1건 — `asset_master` 5컬럼 추가 + `fx_daily` 테이블 신규 (마스터플랜 §5.1)
- `backend/collector/fdr_client.py` `SYMBOL_MAP` 8종 확장 (QQQ/SPY/SCHD/JEPI/TLT/NVDA/GOOGL/TSLA, §5.2)
- `backend/collector/fx_collector.py` 신규 — FDR `USD/KRW` 일봉 수집 (§2.3)
- 신규 자산 8종 + USD/KRW 10년 backfill (staging) + asset_master 13행 시드/갱신 (§7.1)
- padding 알고리즘 unit test (JEPI 5년 → 10년 cyclic returns, §2.6 / §9.1)
- WBI synthetic fixture (시드 42, 10년, 평균 연 20% ±0.5%, §2.5)

**Bronze 운영 영향**: **0**
- `asset_master` 컬럼 추가는 모두 `DEFAULT` 또는 nullable → 기존 INSERT/SELECT 호환
- `fx_daily`는 신규 테이블 → 기존 라우터 무영향
- `SYMBOL_MAP` 확장은 기존 7종 키 변경 X → 기존 Bronze collector job 무영향
- 신규 자산 backfill은 staging DB에서 진행 (Phase 4 cut-over 시 prod 일괄 import)

**예상 결과물**:
| 산출물 | 위치 |
|---|---|
| migration 파일 | `backend/db/alembic/versions/<hash>_silver_rev1_schema_changes.py` |
| `AssetMaster` 모델 5컬럼 | `backend/db/models.py` (수정) |
| `FxDaily` 모델 신규 | `backend/db/models.py` |
| `SYMBOL_MAP` 15종 | `backend/collector/fdr_client.py:14` |
| `fx_collector.py` | `backend/collector/fx_collector.py` (신규) |
| 자산 메타 시드 스크립트 | `backend/collector/seed_silver_assets.py` (신규) |
| padding fixture + test | `backend/research_engine/simulation/padding_fixture.py` + `tests/test_padding.py` |
| WBI fixture | `backend/research_engine/simulation/wbi_fixture.parquet` (or .npz) + `tests/test_wbi.py` |

## 2. Current State (Bronze gen 인계)

- **`asset_master`** 5컬럼 (`asset_id PK / name / category / source_priority JSON / is_active`) — Bronze 8 자산 시드됨
- **`price_daily`** (`asset_id, date, source` 복합 PK) — Bronze 7 자산 일봉 누적
- **`SYMBOL_MAP`** dict-of-dicts 형태 (`fdr_symbol / category / fallbacks?`), 7개 엔트리
- **Alembic head**: `c4d2e5f6a789` (`add_conversation_summaries`) — Phase 1 migration의 `down_revision` 이 됨
- **collector orchestration**: `collector/ingest.py` (FDR fetch → validate → UPSERT, 멱등)
- **alerting**: `collector/alerting.py` Discord webhook
- **scheduler**: GitHub Actions 일일 cron (Bronze 운영 중)
- **fx 데이터 없음**: USD 자산이 없었기에 환율 테이블/collector 부재

## 3. Target State (Phase 1 종료 시)

| 항목 | 종착 상태 |
|---|---|
| `asset_master` 컬럼 | 기존 5 + 신규 5 (`currency / annual_yield / history_start_date / allow_padding / display_name`) |
| `asset_master` 행 | 13행 (Bronze 7 + 신규 6: QQQ/SPY/SCHD/JEPI/TLT/NVDA/GOOGL/TSLA 중 staging에서 활성) — WBI는 synthetic이라 row 미생성 (Phase 2 fixture로 처리) |
| `fx_daily` | 10년치 row (≈ 2520행), `date PK`, `usd_krw_close` |
| `price_daily` (staging) | 신규 8 자산 × 10년 (각 ≈ 2520행, JEPI는 ≈ 1260행) |
| `SYMBOL_MAP` | 15 엔트리 (기존 7 + 신규 8) |
| `fx_collector.collect_usd_krw(start, end)` | FDR `USD/KRW` 호출 → `FxDaily` 객체 list 반환, UPSERT 함수 포함 |
| padding unit test | JEPI 5년 → 10년 변환 시 길이 / 평균 일별 수익률 보존(±0.1%) / reverse-cumprod 가격 연속성 검증 |
| WBI fixture | 시드 42, 10년 ≈ 2520거래일, 평균 연환산 수익률 20% ±0.5%, σ ≈ 1%/일 — Phase 2가 그대로 import |
| Phase 2 진입 가능 여부 | 모든 데이터 의존성 해소, simulation 모듈은 빈 디렉터리만 있으면 즉시 작성 가능 |

**검증 게이트** (모두 PASS해야 Phase 2 진입):
1. `alembic upgrade head` 후 `\d asset_master` 10컬럼 확인 + `\d fx_daily` 존재 확인
2. Bronze prod 시뮬레이션: head 직후 `select * from asset_master limit 1` 정상 (DEFAULT 적용)
3. staging `select count(*) from price_daily where asset_id='QQQ'` ≥ 2400
4. staging `select count(*) from fx_daily` ≥ 2400, 결측 거래일 0 또는 forward-fill 처리됨
5. `pytest backend/tests/test_padding.py backend/tests/test_wbi.py` 100% 통과

## 4. Implementation Stages

### Stage 1.A — Schema 변경 (P1-1)
1. `backend/db/models.py`에 `AssetMaster` 5컬럼 + `FxDaily` 신규 클래스 작성
2. `alembic revision -m "silver_rev1_schema_changes" --autogenerate` 후 수동 검수
   - 자동생성된 컬럼/테이블 외 불필요한 변경 제거 (Bronze 모델 변경분이 끼어들면 분리)
   - `down_revision = 'c4d2e5f6a789'` 확인
3. `op.add_column` 5개, `op.create_table('fx_daily', ...)` 1개 명시
4. downgrade는 역순(`drop_table('fx_daily')` + `op.drop_column` 5개) — Bronze 영향 0이라 reversible
5. 로컬 sqlite/postgres에서 `alembic upgrade head` → `alembic downgrade -1` → `alembic upgrade head` 라운드트립 검증

### Stage 1.B — Collector 확장 (P1-2, P1-3)
1. `SYMBOL_MAP`에 8 엔트리 추가
   - 기존 dict-of-dicts 패턴 유지: `{"fdr_symbol": "QQQ", "category": "etf"}` 형태
   - JEPI 카테고리 = "etf" (JEPY 표기 X, D-1)
   - NVDA/GOOGL/TSLA 카테고리 = "stock"
   - SCHD/TLT 카테고리 = "etf"
2. `backend/collector/fx_collector.py` 신규
   - `collect_usd_krw(start: str, end: str) -> pd.DataFrame` — FDR `USD/KRW` 호출 후 `(date, usd_krw_close)` 컬럼 표준화
   - `upsert_fx_daily(session, df)` — `fx_daily` ON CONFLICT(date) DO UPDATE 패턴 (Bronze `_upsert` 재사용 가능)
   - 기존 `collector/ingest.py` 패턴(retry, alerting) 차용 — 단, fx_daily는 source 컬럼 없음 → 독립 함수
3. retry/alerting은 Bronze `fdr_client._fetch_raw` 그대로 활용 가능 (USD/KRW도 FDR 단일 source)

### Stage 1.C — Backfill (P1-4)
1. `backend/collector/seed_silver_assets.py` 신규 — asset_master 13행 upsert 스크립트
   - 8 신규 자산: `(asset_id, name, category, currency, annual_yield, history_start_date, allow_padding, display_name)` 명시
   - JEPI: `allow_padding=True`, `history_start_date='2020-05-20'` (FDR 실제 상장일)
   - 나머지 7 신규: `allow_padding=False`, 실제 상장일 (TSLA 2010-06-29, 그 외 10년+)
   - Bronze 7종도 `currency`(KRW/USD) + `display_name`(한국어) 채움 — `annual_yield`는 §2.4 fixture
2. backfill 절차 (staging DB 대상):
   - `python -m collector.seed_silver_assets` 먼저 실행 (FK 의존성 위함)
   - 신규 8자산 각각 `python -m collector.ingest --asset QQQ --start 2016-05-09 --end 2026-05-09`
   - USD/KRW: `python -m collector.fx_collector --start 2016-05-09 --end 2026-05-09`
3. 검증 SQL fixture (`backend/scripts/verify_phase1_backfill.sql`):
   - 자산별 `count(*)`, 첫/마지막 date, 결측 거래일
   - `fx_daily`: 거래일 수, KR 휴장일 처리 확인

### Stage 1.D — Fixture & Test (P1-5, P1-6)
1. `backend/research_engine/simulation/__init__.py` 빈 파일 생성 (Phase 2가 채움)
2. `backend/research_engine/simulation/padding.py` **알고리즘만** 작성 (Phase 2에서 사용처 추가)
   - `pad_returns(actual_returns: np.ndarray, target_days: int) -> np.ndarray` — cyclic 복제 후 prepend
   - `prices_with_padding(actual_prices: np.ndarray, padded_returns: np.ndarray) -> np.ndarray` — reverse-cumprod
3. `backend/tests/test_padding.py` (P1-5):
   - JEPI fixture: 실제 5년 일별 수익률 `.parquet` 또는 `.npy` 저장
   - 검증: 길이 == TARGET_DAYS, 평균 일별 수익률 보존(±0.1%), 가격 연속성(첫 actual price와 padding 끝 가격 일치)
   - edge cases: actual = 1년, actual = TARGET_DAYS+1 (no padding), actual = 정확히 절반
4. `backend/research_engine/simulation/wbi.py` **GBM 함수만** 작성
   - `generate_wbi(n_days: int, seed: int = 42, annual_return: float = 0.20, sigma: float = 0.01) -> np.ndarray`
5. `backend/tests/test_wbi.py` (P1-6):
   - 시드 42 reproducibility (두 번 호출 결과 동일)
   - 10년 (2520일) 평균 연환산 수익률 20% ±0.5%
   - σ ≈ 1%/일 (±5% 허용)
6. WBI fixture 저장: `backend/research_engine/simulation/fixtures/wbi_seed42_10y.npz` — Phase 2가 import해서 매번 재계산 회피

## 5. Task Breakdown

| ID | Size | 의존 | 산출 | 검증 |
|---|---|---|---|---|
| P1-1 | M | — | migration 파일 + 모델 수정 | upgrade/downgrade 라운드트립 |
| P1-2 | S | — | SYMBOL_MAP 8 엔트리 | 신규 자산 1개 fetch smoke |
| P1-3 | M | P1-1 (fx_daily) | `fx_collector.py` + UPSERT | USD/KRW 5일치 fetch 후 row 확인 |
| P1-4 | L | P1-1, P1-2, P1-3 | seed 스크립트 + staging 데이터 | row count, asset_master 13행 |
| P1-5 | M | (P1-4 JEPI 데이터 권장) | `padding.py` + JEPI fixture + test | unit test 통과 |
| P1-6 | S | — | `wbi.py` + fixture | unit test 통과 + fixture 파일 |

**Size 분포**: S:2 / M:3 / L:1 (총 6개)

**권장 진행 순서**: P1-1 → (P1-2, P1-3 병렬) → P1-4 → (P1-5, P1-6 병렬)
- P1-5는 JEPI 실데이터를 쓰면 P1-4에 의존, mock fixture로만 쓰면 독립 (실데이터 권장)
- P1-6은 외부 데이터 무관 (numpy seed) → P1-4와 병렬 가능

## 6. Risks & Mitigation

| 리스크 | 영향 | 대응 |
|---|---|---|
| FDR `USD/KRW` 결측 / 휴장일 비대칭 | fx_daily 행 부족 | KRX/NYSE 캘린더 비교 후 forward-fill 정책을 Phase 2 `fx.py`에서 처리, Phase 1은 raw row 저장에 집중 |
| JEPI 상장일 < 5년 미만 | padding test fixture 부족 | FDR `JEPI` 실제 상장일 확인(2020-05-20, 약 6년) → 정확히 5년 슬라이스 사용 |
| migration `--autogenerate`가 다른 모델 변경 감지 | migration 오염 | autogen 결과 수동 검수, 의도한 5컬럼 + 1테이블 외 모두 제거 |
| asset_master `display_name` 한국어 인코딩 | DB 저장 깨짐 | `VARCHAR(64)` + UTF-8 클라이언트 인코딩 (CLAUDE.md §Encoding) — staging insert 직후 `select` 검증 |
| 신규 자산 backfill API rate limit | 시간 지연 | FDR fetch 사이 `BASE_DELAY` 유지, 1자산씩 순차 — 8자산 × 10년 ≈ 30분 예상 |
| WBI 시드 42 결과 numpy 버전 의존 | reproducibility 흔들림 | `np.random.default_rng(42)` 사용 (legacy `np.random.seed` 회피), `numpy>=1.17` requirement |

## 7. Dependencies

**내부**:
- `backend/db/models.py:25` (`AssetMaster`) — 컬럼 추가
- `backend/db/models.py:35` (`PriceDaily`) — 변경 없음, 신규 자산 데이터만 적재
- `backend/db/alembic/env.py` — `target_metadata` 모델 import 경로 확인
- `backend/collector/fdr_client.py:14` (`SYMBOL_MAP`)
- `backend/collector/ingest.py:30` (`_upsert`) — fx_daily UPSERT 시 패턴 차용
- `backend/collector/alerting.py` — fx_collector 실패 시 재사용
- `backend/research_engine/` — `simulation/` 신규 디렉터리 (Phase 2 본격 사용)

**외부**:
- `FinanceDataReader>=0.9` — `USD/KRW` 심볼 + 신규 8자산 모두 지원 확인됨
- `alembic` — schema migration
- `numpy>=1.17` — `default_rng(seed=42)` (WBI)
- `pandas` — collector DataFrame 표준화
- `pytest` — unit test
- `pyarrow` (선택) — JEPI fixture parquet 저장 시 (.npy 사용하면 불필요)

**기준 문서**:
1. `docs/silver-masterplan.md` §2 / §5.1 / §5.2 / §7 / §9.1 / §12 Phase 1 체크리스트
2. `dev/active/project-overall/project-overall-context.md` D-1~D-5, D-22 (fractional 정밀도, Phase 2로 이월)
3. `docs/session-compact.md` Step 1 SQL 스니펫
4. CLAUDE.md `Encoding (Windows + Korean)` — 한국어 display_name UTF-8 처리

## 8. Phase 1 종료 조건 (Definition of Done)

- [ ] migration이 staging과 prod에서 reversible하게 적용됨 (라운드트립 1회 검증)
- [ ] Bronze 일일 수집 cron이 신규 컬럼 영향 없이 정상 동작 (1일 모니터링)
- [ ] `pytest backend/tests/test_padding.py backend/tests/test_wbi.py` 통과
- [ ] staging DB에서 13개 자산(WBI 제외) asset_master 메타 정합 + 일봉 row 수 검증 통과
- [ ] Phase 2가 import할 fixture(`wbi_seed42_10y.npz` + JEPI returns) 커밋됨
- [ ] `dev/active/silver-rev1-phase1/silver-rev1-phase1-tasks.md`의 6개 태스크 모두 commit hash 기재
- [ ] `debug-history.md`에 Phase 1 발생 이슈/해결 정리

# Silver rev1 — Phase 1: Tasks
> Gen: silver
> Last Updated: 2026-05-09
> Status: 1/6 (P1-1 완료)
> Branch: master (단일 사용자, feature 브랜치 미사용)
> 정책: **"Show, don't claim"** — context.md §0 / project-overall §0 참조

## Summary

| ID | Title | Size | Depends | Status | Commit |
|---|---|---|---|---|---|
| P1-1 | Alembic migration: asset_master 5컬럼 + fx_daily | M | — | ✅ Done | `7d457a2` |
| P1-2 | SYMBOL_MAP 8종 추가 | S | — | ✅ Done | (다음 commit) |
| P1-3 | fx_collector USD/KRW 일봉 | M | P1-1 | TODO | — |
| P1-4 | 신규 자산 + USD/KRW 10년 backfill (prod) | L | P1-1, P1-2, P1-3 | TODO | — |
| P1-5 | padding 알고리즘 + JEPI fixture + unit test | M | (P1-4 권장) | TODO | — |
| P1-6 | WBI synthetic 시드 42 fixture + unit test | S | — | TODO | — |

**Size 분포**: S:2 / M:3 / L:1 (총 6개)

권장 진행 순서: **P1-1 ✅ → P1-2 ✅ → P1-3 → P1-4 → (P1-5 ∥ P1-6)**

### 검증 게이트 형식 (전 Phase 표준 — project-overall-context.md §0)

각 게이트는 다음 3단 형식:

```markdown
- [ ] <검증 항목>
  - 명령: <실행 가능한 1줄>
  - Evidence: <어디에 어떤 형식으로 paste — verification/step-N-*.md 권장>
  - 통과 기준: <PASS/FAIL 가르는 구체 임계>
```

각 step 종료 시 `verification/step-N-<topic>.md` 작성 sub-step 의무.
P1-4 / P1-5 / P1-6은 PNG 차트 추가 의무 (`verification/figures/`).

---

## P1-1 (M) Alembic migration: asset_master 5컬럼 + fx_daily

**목표**: Bronze 영향 0으로 schema를 Silver gen이 요구하는 상태로 확장.

### Sub-steps
- [ ] **Step 1.1** `backend/db/models.py:25` `AssetMaster`에 5컬럼 추가
  - `currency: Mapped[str] = mapped_column(String(8), nullable=False, server_default='KRW')`
  - `annual_yield: Mapped[Decimal] = mapped_column(Numeric(6, 4), nullable=False, server_default='0')`
  - `history_start_date: Mapped[Date | None] = mapped_column(Date, nullable=True)`
  - `allow_padding: Mapped[bool] = mapped_column(Boolean, server_default=expression.false())`
  - `display_name: Mapped[str | None] = mapped_column(String(64), nullable=True)`
- [ ] **Step 1.2** `backend/db/models.py` 끝에 `class FxDaily(Base)` 추가
  - `__tablename__ = "fx_daily"`
  - `date: Mapped[Date] = mapped_column(Date, primary_key=True)`
  - `usd_krw_close: Mapped[Decimal] = mapped_column(Numeric(10, 4), nullable=False)`
  - `created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())`
- [ ] **Step 1.3** migration 생성:
  ```
  cd /c/Projects-2026/active/stock-dashboard/backend
  alembic revision --autogenerate -m "silver_rev1_schema_changes"
  ```
- [ ] **Step 1.4** 자동 생성된 migration 검수
  - `down_revision = 'c4d2e5f6a789'` 확인
  - upgrade: `op.add_column('asset_master', ...)` 5건 + `op.create_table('fx_daily', ...)` 1건
  - downgrade: 역순 (`op.drop_table('fx_daily')` → `op.drop_column('asset_master', ...)` 5건)
  - 의도하지 않은 변경(다른 모델 자동 감지) 모두 제거
- [ ] **Step 1.5** 라운드트립 검증 (로컬 staging)
  - `alembic upgrade head` → schema 확인 (`\d asset_master`, `\d fx_daily`)
  - `alembic downgrade -1` → 원상 복구 확인
  - `alembic upgrade head` → 재적용

### 검증 게이트 (3단 형식)

- [x] **G1.1 asset_master 10컬럼 등록**
  - 명령: `python -c "from sqlalchemy import inspect; from db.session import engine; print([c['name'] for c in inspect(engine).get_columns('asset_master')])"`
  - Evidence: column 표 (name | type | nullable | default) → `verification/step-1-schema.md`에 paste
  - 통과 기준: 컬럼 10개 (기존 5 + 신규 5), 신규 5컬럼 모두 nullable=True 또는 server_default 명시

- [x] **G1.2 fx_daily 신규 + PK=date**
  - 명령: `python -c "from sqlalchemy import inspect; from db.session import engine; insp=inspect(engine); print('exists:', 'fx_daily' in insp.get_table_names()); print('pk:', insp.get_pk_constraint('fx_daily'))"`
  - Evidence: 테이블 존재 여부 + PK 제약 → `verification/step-1-schema.md`
  - 통과 기준: `fx_daily` 존재, PK constrained_columns == `['date']`

- [x] **G1.3 기존 row DEFAULT 자동 적용**
  - 명령: `python -c "..."` — `select asset_id, currency, annual_yield, allow_padding, display_name from asset_master limit 1`
  - Evidence: 결과 row(s) → `verification/step-1-schema.md` (sample row 표)
  - 통과 기준: `currency='KRW'`, `annual_yield=0.0000`, `allow_padding=False` (server_default 적용 확인)

- [ ] **G1.4 downgrade reversibility (offline SQL)**
  - 명령: `alembic downgrade d8334483342c:c4d2e5f6a789 --sql`
  - Evidence: SQL dump → `verification/step-1-schema.md` (downgrade SQL block)
  - 통과 기준: 5건 `DROP COLUMN` + `DROP TABLE fx_daily` + `UPDATE alembic_version` 포함

- [ ] **G1.5 verification/step-1-schema.md 작성**
  - Evidence: 본 파일 자체
  - 통과 기준: G1.1~G1.4 모두 paste된 markdown 파일 존재

### 예상 commit
- `[silver-rev1-phase1] Step 1: AssetMaster 5컬럼 + FxDaily + migration` ✅ `7d457a2`
- `[silver-rev1-phase1] Step 1 verify: schema inspect evidence` (verification/step-1-schema.md 추가)

---

## P1-2 (S) SYMBOL_MAP 8종 추가

**목표**: collector가 신규 8 자산을 인식하도록 매핑 확장.

### Sub-steps
- [ ] **Step 2.1** `backend/collector/fdr_client.py:14` `SYMBOL_MAP`에 8 엔트리 추가
  ```python
  "QQQ":   {"fdr_symbol": "QQQ",   "category": "etf"},
  "SPY":   {"fdr_symbol": "SPY",   "category": "etf"},
  "SCHD":  {"fdr_symbol": "SCHD",  "category": "etf"},
  "JEPI":  {"fdr_symbol": "JEPI",  "category": "etf"},
  "TLT":   {"fdr_symbol": "TLT",   "category": "etf"},
  "NVDA":  {"fdr_symbol": "NVDA",  "category": "stock"},
  "GOOGL": {"fdr_symbol": "GOOGL", "category": "stock"},
  "TSLA":  {"fdr_symbol": "TSLA",  "category": "stock"},
  ```
- [ ] **Step 2.2** smoke test: `python -c "from collector.fdr_client import fetch_ohlcv; df = fetch_ohlcv('QQQ', '2026-04-01', '2026-04-10'); print(df.head())"`
- [ ] **Step 2.3** 기존 7 엔트리 키/값 미변경 확인 (Bronze 영향 0)

### 검증 게이트 (3단 형식)

- [x] **G2.1 SYMBOL_MAP 키 개수 = 15** — `verification/step-2-symbol-map.md#g21`
- [x] **G2.2 기존 7 엔트리 무변경 (Bronze 영향 0)** — `verification/step-2-symbol-map.md#g22`
- [x] **G2.3 신규 8 자산 1주일치 fetch smoke** — 8자산 모두 5 row, 가격 sanity 통과
- [x] **G2.4 verification/step-2-symbol-map.md 작성** ✅

### 예상 commit
- `[silver-rev1-phase1] Step 2: SYMBOL_MAP 8 엔트리 추가 + verify`

---

## P1-3 (M) fx_collector USD/KRW 일봉

**목표**: FDR `USD/KRW` 일봉을 `fx_daily`로 적재하는 collector + UPSERT 함수.

**의존**: P1-1 (`fx_daily` 테이블 + `FxDaily` 모델)

### Sub-steps
- [ ] **Step 3.1** `backend/collector/fx_collector.py` 신규
  - `collect_usd_krw(start: str, end: str) -> pd.DataFrame`
    - FDR `DataReader("USD/KRW", start, end)` 호출
    - 표준화: `(date, usd_krw_close)` 2컬럼 DataFrame
  - `upsert_fx_daily(session, df: pd.DataFrame) -> int`
    - `from sqlalchemy.dialects.postgresql import insert`
    - `ON CONFLICT (date) DO UPDATE SET usd_krw_close = EXCLUDED.usd_krw_close`
    - chunk_size 1000 (기존 `_upsert` 패턴)
- [ ] **Step 3.2** alerting 연결 — fetch 실패 시 `send_discord_alert` 호출 (`collector/alerting.py` 재사용)
- [ ] **Step 3.3** CLI entrypoint: `python -m collector.fx_collector --start 2016-05-09 --end 2026-05-09`
- [ ] **Step 3.4** smoke test: 5일치 fetch → staging insert → row count 확인

### 검증 게이트 (3단 형식)

- [ ] **G3.1 fx_daily smoke insert (5일치)**
  - 명령: `python -m collector.fx_collector --start 2026-05-01 --end 2026-05-09`
  - Evidence: 명령 stdout (insert row 수) → `verification/step-3-fx.md`
  - 통과 기준: 거래일 ≥ 3 insert 성공, 에러 0

- [ ] **G3.2 최근 5일 row 출력**
  - 명령: `psql ... -c "select date, usd_krw_close from fx_daily order by date desc limit 5"`
  - Evidence: 표 (date | usd_krw_close) → `verification/step-3-fx.md`
  - 통과 기준: 5 row 출력, usd_krw_close 1100~1500 범위 (sanity check)

- [ ] **G3.3 idempotent 재실행 (UPSERT 검증)**
  - 명령: 동일 구간 두 번 실행 → 전후 `count(*)` 비교
  - Evidence: before/after count 표 → `verification/step-3-fx.md`
  - 통과 기준: 두 count 동일 (row 중복 생성 0)

- [ ] **G3.4 verification/step-3-fx.md 작성**
  - 통과 기준: G3.1~G3.3 paste

### 예상 commit
- `[silver-rev1-phase1] Step 3: fx_collector USD/KRW + UPSERT + verify`

---

## P1-4 (L) 신규 자산 + USD/KRW 10년 backfill (staging)

**목표**: staging DB에 13자산 메타 + 신규 8자산 일봉 + USD/KRW 10년 적재.

**의존**: P1-1, P1-2, P1-3

### Sub-steps
- [ ] **Step 4.1** `backend/collector/seed_silver_assets.py` 신규
  - 13자산 (Bronze 7 + 신규 6 active, JEPI 포함) — `(asset_id, name, category, currency, annual_yield, history_start_date, allow_padding, display_name)` 명시
  - WBI는 row 미생성 (Phase 2 fixture 처리)
  - `annual_yield` 마스터플랜 §2.4 fixture 그대로:
    - SCHD 0.035, JEPI 0.080, TLT 0.038, SPY 0.013, QQQ 0.006
    - KS200 0.015, 005930 0.025, 000660 0.010
    - NVDA/GOOGL/TSLA/BTC 0.0
  - JEPI: `allow_padding=True`, `history_start_date='2020-05-20'`
  - 한국어 `display_name`: 엔비디아 / 구글 / 테슬라 / 삼성전자 / 하이닉스 / 비트코인 / KOSPI200 등
  - upsert 패턴 (asset_id 기준 ON CONFLICT DO UPDATE)
- [ ] **Step 4.2** seed 실행: `python -m collector.seed_silver_assets`
- [ ] **Step 4.3** 신규 8자산 backfill (각각 순차):
  ```
  for asset in QQQ SPY SCHD JEPI TLT NVDA GOOGL TSLA; do
    python -m collector.ingest --asset $asset --start 2016-05-09 --end 2026-05-09
  done
  ```
  - JEPI는 상장일(2020-05-20) 이후만 데이터 적재 (FDR 자체 처리)
- [ ] **Step 4.4** USD/KRW backfill: `python -m collector.fx_collector --start 2016-05-09 --end 2026-05-09`
- [ ] **Step 4.5** `backend/scripts/verify_phase1_backfill.sql` 작성 + 실행
  - 자산별 `count(*)`, `min(date)`, `max(date)` 출력
  - 결측 거래일 검사 (자산별 캘린더 차이)
  - asset_master 13행 정합 (currency / annual_yield / display_name 누락 0)
- [ ] **Step 4.6** Bronze cron 영향 확인 (1일 모니터링)
  - 신규 컬럼 DEFAULT 적용으로 기존 INSERT 정상
  - alerting 채널에 신규 자산 실패 알림 없음

### 검증 게이트 (3단 형식 + PNG)

- [ ] **G4.1 asset_master 13행 + 메타 정합**
  - 명령: `select asset_id, name, currency, annual_yield, allow_padding, display_name, history_start_date from asset_master order by asset_id`
  - Evidence: 13행 표 (7컬럼) → `verification/step-4-backfill.md`
  - 통과 기준: 13행, JEPI `allow_padding=True` + `history_start_date='2020-05-20'`, 한국어 display_name 모두 존재(KS200/005930/000660/BTC + 신규 6)

- [ ] **G4.2 신규 8자산 row count + 시작일/종료일**
  - 명령: `select asset_id, count(*) as rows, min(date) as first, max(date) as last from price_daily where asset_id in (...) group by asset_id`
  - Evidence: 표 → `verification/step-4-backfill.md`
  - 통과 기준: QQQ/SPY/SCHD/TLT/NVDA/GOOGL/TSLA ≥ 2400, JEPI ≥ 1200, 모든 last_date ≥ 2026-05-08

- [ ] **G4.3 fx_daily 10년 + 결측 분석**
  - 명령: row count + 평일 휴일 비교 SQL (KR/US 휴일 비대칭 측정)
  - Evidence: 결측 거래일 list (있으면) + count → `verification/step-4-backfill.md`
  - 통과 기준: count ≥ 2400, 결측은 KR/US 휴일과 일치

- [ ] **G4.4 [PNG] 자산별 row count bar chart**
  - 명령: matplotlib 스크립트 → `backend/scripts/plot_backfill_rowcount.py`
  - Evidence: `verification/figures/step-4-backfill-rowcount.png` 저장 + 본 markdown에 ![]() 임베드
  - 통과 기준: 13 자산 bar chart, JEPI 짧음(padding 대상) 시각적 확인

- [ ] **G4.5 Bronze cron 24h 정상 (회귀 검증)**
  - 명령: `select asset_id, max(date) from price_daily where source='fdr' group by asset_id` (24h 후)
  - Evidence: Bronze 7자산 max(date) = T-1 영업일 → `verification/step-4-backfill.md`
  - 통과 기준: Bronze 7자산 모두 어제 데이터 적재 + Discord alerting silent

- [ ] **G4.6 verification/step-4-backfill.md 작성**
  - 통과 기준: G4.1~G4.5 paste + PNG 1개 임베드

### 예상 commit
- `[silver-rev1-phase1] Step 4: seed_silver_assets 13행 + backfill (prod)`
- `[silver-rev1-phase1] Step 4 verify: backfill rowcount + PNG`

---

## P1-5 (M) padding 알고리즘 + JEPI fixture + unit test

**목표**: cyclic returns + reverse-cumprod padding 알고리즘 + JEPI 5년 → 10년 fixture 검증.

**의존**: (P1-4 권장 — JEPI 실데이터)

### Sub-steps
- [ ] **Step 5.1** `backend/research_engine/simulation/__init__.py` 빈 파일
- [ ] **Step 5.2** `backend/research_engine/simulation/padding.py`
  - `pad_returns(actual_returns: np.ndarray, target_days: int) -> np.ndarray`
    - `target_days <= len(actual_returns)`이면 actual 그대로 반환 (no padding)
    - cyclic 복제: `padding = []`, `while len(padding) < needed: padding.extend(actual[: min(needed-len(padding), len(actual))])`
    - 결과: `padding + actual.tolist()`
  - `prices_with_padding(actual_first_price: float, padded_returns: np.ndarray, padding_len: int) -> np.ndarray`
    - reverse-cumprod: padding 종료 시점 가격 = `actual_first_price`, 거꾸로 거슬러 올라가 padding 가격 산정
    - actual 구간은 cumprod 그대로
    - 반환: 전체 길이 가격 시계열
- [ ] **Step 5.3** JEPI fixture 추출
  - staging `price_daily where asset_id='JEPI' order by date` → 정확히 1260 거래일(5년) 슬라이스
  - 일별 수익률 = `close[t] / close[t-1] - 1`
  - 저장: `backend/research_engine/simulation/fixtures/jepi_5y_returns.parquet` (또는 `.npy`)
- [ ] **Step 5.4** `backend/tests/test_padding.py`
  - **test_no_padding_when_sufficient**: `pad_returns(actual_10y, 2520)` == `actual_10y`
  - **test_jepi_5y_to_10y_length**: `len(pad_returns(jepi_5y, 2520)) == 2520`
  - **test_mean_return_preserved**: `np.mean(padded) ≈ np.mean(actual)` ±0.1%
  - **test_reverse_cumprod_continuity**: padding 마지막 가격 == actual 첫 가격 (np.allclose rtol=1e-9)
  - **test_edge_half_length**: actual = 1260일, target = 2520일 → padding 정확히 1260
  - **test_partial_cycle**: actual = 1000일, target = 2520일 → padding 1520 (cyclic 부분 절단)

### 검증 게이트 (3단 형식 + PNG)

- [ ] **G5.1 pytest 6 케이스 통과**
  - 명령: `pytest backend/tests/test_padding.py -v --tb=short`
  - Evidence: pytest 출력 (6 PASSED) → `verification/step-5-padding.md` (코드 블록)
  - 통과 기준: 6 케이스 모두 PASSED, FAILED/ERROR 0

- [ ] **G5.2 평균 일별 수익률 보존 표**
  - 명령: `python -c "import numpy as np; from research_engine.simulation.padding import pad_returns; ... print(actual_mean, padded_mean, diff_pct)"`
  - Evidence: 표 (actual_mean | padded_mean | diff_pct) → `verification/step-5-padding.md`
  - 통과 기준: |diff_pct| < 0.1%

- [ ] **G5.3 [PNG] padding 시계열 차트**
  - 명령: `python backend/scripts/plot_padding_jepi.py` (matplotlib)
  - Evidence: `verification/figures/step-5-padding-jepi.png` + 본 markdown에 ![]() 임베드
  - 통과 기준: 10년 line chart, padding 구간(앞 5년) 회색 영역 + actual 5년 색상 구분, 가격 연속성(점프 없음) 시각 확인

- [ ] **G5.4 의존성 numpy 단독**
  - 명령: `python -c "import ast; print({n.module for n in ast.walk(ast.parse(open('backend/research_engine/simulation/padding.py').read())) if isinstance(n, ast.ImportFrom)})"`
  - Evidence: import set → `verification/step-5-padding.md`
  - 통과 기준: numpy 외 외부 의존 0

- [ ] **G5.5 verification/step-5-padding.md 작성**
  - 통과 기준: G5.1~G5.4 paste + PNG 1개 임베드

### 예상 commit
- `[silver-rev1-phase1] Step 5: padding cyclic + reverse-cumprod + JEPI fixture + test`
- `[silver-rev1-phase1] Step 5 verify: padding evidence + PNG`

---

## P1-6 (S) WBI synthetic 시드 42 fixture + unit test

**목표**: GBM σ=1%/일 + drift 보정으로 평균 정확히 연 20% 보존, 시드 42 reproducibility 검증.

### Sub-steps
- [ ] **Step 6.1** `backend/research_engine/simulation/wbi.py`
  - `generate_wbi(n_days: int, seed: int = 42, annual_return: float = 0.20, sigma: float = 0.01, initial_price: float = 100.0) -> np.ndarray`
    - `mu = (1 + annual_return) ** (1 / 252) - 1`
    - `mu_adj = mu - 0.5 * sigma ** 2` (GBM drift 보정)
    - `rng = np.random.default_rng(seed)`
    - `returns = rng.normal(loc=mu_adj, scale=sigma, size=n_days)`
    - `prices = np.cumprod(1 + returns) * initial_price`
    - 반환: prices array (length = n_days)
- [ ] **Step 6.2** fixture pre-compute + 저장
  - `python -c "import numpy as np; from research_engine.simulation.wbi import generate_wbi; p = generate_wbi(2520); np.savez('backend/research_engine/simulation/fixtures/wbi_seed42_10y.npz', prices=p)"`
  - 또는 별도 스크립트 `backend/scripts/build_wbi_fixture.py`
- [ ] **Step 6.3** `backend/tests/test_wbi.py`
  - **test_reproducibility**: 두 번 호출 결과 `np.array_equal`
  - **test_length**: `len(generate_wbi(2520)) == 2520`
  - **test_mean_annual_return**: 10년 fixture (2520일)
    - 연환산 수익률 = `(prices[-1] / prices[0]) ** (252/2520) - 1` ≈ 0.20 ±0.005
  - **test_sigma_approx**: 일별 수익률 표준편차 ≈ 0.01 ±0.001
  - **test_fixture_loadable**: `np.load('.../wbi_seed42_10y.npz')['prices']` length == 2520

### 검증 게이트 (3단 형식 + PNG)

- [ ] **G6.1 pytest 5 케이스 통과**
  - 명령: `pytest backend/tests/test_wbi.py -v --tb=short`
  - Evidence: pytest 출력 → `verification/step-6-wbi.md`
  - 통과 기준: 5 케이스 모두 PASSED

- [ ] **G6.2 시드 42 reproducibility**
  - 명령: `python -c "from research_engine.simulation.wbi import generate_wbi; import numpy as np; a=generate_wbi(2520); b=generate_wbi(2520); print('equal:', np.array_equal(a,b)); print('first 3:', a[:3])"`
  - Evidence: equal=True + 첫 3개 가격 → `verification/step-6-wbi.md`
  - 통과 기준: equal == True

- [ ] **G6.3 평균 연환산 수익률 + σ 통계**
  - 명령: `python -c "..."` — fixture load 후 연환산/σ 계산
  - Evidence: 표 (annual_return | sigma_daily | n_days) → `verification/step-6-wbi.md`
  - 통과 기준: annual_return ∈ [0.195, 0.205], sigma_daily ∈ [0.0095, 0.0105]

- [ ] **G6.4 [PNG] WBI 가격 시계열 + 일별 수익률 히스토그램**
  - 명령: `python backend/scripts/plot_wbi_visual.py` (matplotlib subplot 2개)
  - Evidence: `verification/figures/step-6-wbi-visual.png` + 본 markdown 임베드
  - 통과 기준: 10년 가격 line chart (우상향 추세) + 일별 수익률 히스토그램 (정규분포 종 모양, 평균 ~0.0007)

- [ ] **G6.5 fixture .npz load 검증**
  - 명령: `python -c "import numpy as np; d=np.load('backend/research_engine/simulation/fixtures/wbi_seed42_10y.npz'); print(list(d.keys()), d['prices'].shape)"`
  - Evidence: keys + shape → `verification/step-6-wbi.md`
  - 통과 기준: `prices` 키 존재, shape == (2520,)

- [ ] **G6.6 verification/step-6-wbi.md 작성**
  - 통과 기준: G6.1~G6.5 paste + PNG 1개

### 예상 commit
- `[silver-rev1-phase1] Step 6: WBI generate_wbi 시드 42 + fixture + test`
- `[silver-rev1-phase1] Step 6 verify: WBI evidence + PNG`

---

## Phase 1 Definition of Done

- [ ] 6개 태스크 모두 완료 + commit hash 본 파일에 기록 (P1-1 ✅ 7d457a2)
- [ ] migration reversible 확인 (offline SQL — P1-1 G1.4)
- [ ] Bronze 일일 cron 1회 모니터링 통과 (P1-4 G4.5)
- [ ] `pytest backend/tests/test_padding.py backend/tests/test_wbi.py` 100% (P1-5 G5.1, P1-6 G6.1)
- [ ] Phase 2 진입 가능 — `research_engine/simulation/`에 padding.py + wbi.py + fixture 2종 존재
- [ ] `debug-history.md`에 Phase 1 디버깅 정리

### Evidence 누적 (Show, don't claim)
- [ ] `verification/step-1-schema.md` (P1-1)
- [ ] `verification/step-2-symbol-map.md` (P1-2)
- [ ] `verification/step-3-fx.md` (P1-3)
- [ ] `verification/step-4-backfill.md` + `figures/step-4-backfill-rowcount.png` (P1-4)
- [ ] `verification/step-5-padding.md` + `figures/step-5-padding-jepi.png` (P1-5)
- [ ] `verification/step-6-wbi.md` + `figures/step-6-wbi-visual.png` (P1-6)
- [ ] 사용자가 6개 evidence 파일 모두 확인 후 Phase 1 closure

---

## 미해결 후속 결정 (Phase 1에서 보류)

| 항목 | 이월 시점 |
|---|---|
| 자산별 캘린더 forward-fill 정책 | Phase 2 (`fx.py`) |
| fractional 정밀도 12자리 (D-22) | Phase 2 |
| `alerting.py` 신규 자산 확장 | Phase 1 종료 직후 (P1-4 안정화 후) |

# Silver rev1 — Phase 1: Tasks
> Gen: silver
> Last Updated: 2026-05-09
> Status: 0/6 (Planning)
> Branch: `feature/silver-rev1`

## Summary

| ID | Title | Size | Depends | Status | Commit |
|---|---|---|---|---|---|
| P1-1 | Alembic migration: asset_master 5컬럼 + fx_daily | M | — | TODO | — |
| P1-2 | SYMBOL_MAP 8종 추가 | S | — | TODO | — |
| P1-3 | fx_collector USD/KRW 일봉 | M | P1-1 | TODO | — |
| P1-4 | 신규 자산 + USD/KRW 10년 backfill (staging) | L | P1-1, P1-2, P1-3 | TODO | — |
| P1-5 | padding 알고리즘 + JEPI fixture + unit test | M | (P1-4 권장) | TODO | — |
| P1-6 | WBI synthetic 시드 42 fixture + unit test | S | — | TODO | — |

**Size 분포**: S:2 / M:3 / L:1 (총 6개)

권장 진행 순서: **P1-1 → (P1-2 ∥ P1-3) → P1-4 → (P1-5 ∥ P1-6)**

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

### 검증 게이트
- [ ] staging DB `\d asset_master`에 10컬럼 존재 (기존 5 + 신규 5)
- [ ] staging DB `\d fx_daily` 존재 + PK = `date`
- [ ] Bronze prod 시뮬레이션: `select * from asset_master limit 1` 정상 (DEFAULT 적용)
- [ ] downgrade 후 `\d asset_master` 5컬럼 (원상 복구) 확인

### 예상 commit
- `[silver-rev1-phase1] Step 1.1: AssetMaster 5컬럼 + FxDaily 모델 추가`
- `[silver-rev1-phase1] Step 1.2: alembic migration silver_rev1_schema_changes`

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

### 검증 게이트
- [ ] `SYMBOL_MAP` 키 개수 = 15
- [ ] 기존 7 엔트리 dict 동일 (diff로 확인)
- [ ] 신규 8 자산 각각 1주일치 fetch smoke 통과

### 예상 commit
- `[silver-rev1-phase1] Step 2.1: SYMBOL_MAP 8 엔트리 추가`

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

### 검증 게이트
- [ ] `select count(*) from fx_daily` ≥ 1 (smoke)
- [ ] `select * from fx_daily order by date desc limit 5` 최근 5일 출력
- [ ] 동일 구간 재실행 시 row 수 변화 없음 (idempotent)

### 예상 commit
- `[silver-rev1-phase1] Step 3.1: fx_collector USD/KRW 일봉 수집기 + UPSERT`

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

### 검증 게이트
- [ ] staging `select count(*) from asset_master` = 13
- [ ] `select count(*) from price_daily where asset_id='QQQ'` ≥ 2400
- [ ] `select count(*) from price_daily where asset_id='JEPI'` ≥ 1200 (≈ 5년+)
- [ ] `select count(*) from fx_daily` ≥ 2400
- [ ] Bronze 일일 cron 1회 정상 (24h 후 확인)

### 예상 commit
- `[silver-rev1-phase1] Step 4.1: seed_silver_assets 13행 메타`
- `[silver-rev1-phase1] Step 4.2: staging backfill verify SQL`

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

### 검증 게이트
- [ ] `pytest backend/tests/test_padding.py -v` 100% 통과
- [ ] fixture 파일 저장됨 (size > 0)
- [ ] `padding.py` 외부 의존 = numpy만

### 예상 commit
- `[silver-rev1-phase1] Step 5.1: padding cyclic + reverse-cumprod 알고리즘 + JEPI fixture + unit test`

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

### 검증 게이트
- [ ] `pytest backend/tests/test_wbi.py -v` 100% 통과
- [ ] fixture `.npz` 파일 존재 + 정상 load
- [ ] reproducibility 두 번 실행 동일

### 예상 commit
- `[silver-rev1-phase1] Step 6.1: WBI generate_wbi GBM 시드 42 + fixture + unit test`

---

## Phase 1 Definition of Done

- [ ] 6개 태스크 모두 완료 + commit hash 본 파일에 기록
- [ ] migration이 staging → prod 양쪽에서 reversible 확인
- [ ] Bronze 일일 cron 1회 모니터링 통과
- [ ] `pytest backend/tests/test_padding.py backend/tests/test_wbi.py` 100%
- [ ] staging DB 검증 SQL (P1-4 Step 4.5) 통과
- [ ] Phase 2 진입 가능 (`research_engine/simulation/`에 padding.py + wbi.py + fixture 2종 존재)
- [ ] `debug-history.md`에 Phase 1 디버깅 정리

---

## 미해결 후속 결정 (Phase 1에서 보류)

| 항목 | 이월 시점 |
|---|---|
| 자산별 캘린더 forward-fill 정책 | Phase 2 (`fx.py`) |
| fractional 정밀도 12자리 (D-22) | Phase 2 |
| `alerting.py` 신규 자산 확장 | Phase 1 종료 직후 (P1-4 안정화 후) |

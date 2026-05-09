# Bird View — Stock Dashboard
> Updated: 2026-05-09
> Gen: Silver (Phase 1 완료, Phase 2 진입 직전)

## 전체 파이프라인

```
[GitHub Actions Cron] ─→ scripts/collect.py
                               │
                    ┌──────────┴──────────────────────┐
                    ▼                                  ▼
         collector/ingest.py               collector/fx_collector.py
         (Bronze 7 + Silver 8)             (USD/KRW → fx_daily)
              FDR fetch → validate → UPSERT
                    │
              price_daily (15자산, 37,671행)
                    │
         research_engine/factors.py ──→ factor_daily
         research_engine/strategies/ ──→ signal_daily
                    │
              FastAPI (api/main.py)
              ├─ /v1/prices  /v1/factors  /v1/signals
              ├─ /v1/backtests  /v1/dashboard  /v1/correlation
              ├─ /v1/auth  /v1/profile
              └─ /v1/chat ──→ Agentic AI (Classifier→DataFetcher→Reporter)
                    │
              React Frontend (Recharts)
```

**Silver gen 추가 예정 (Phase 2)**:
```
research_engine/simulation/ ──→ /v1/silver/simulate/{replay,strategy,portfolio}
                            └──→ /v1/fx/usd-krw
```

---

## DB 스키마 (현재 head: d8334483342c)

| 테이블 | 행 수 | 핵심 컬럼 | 용도 |
|---|---|---|---|
| `asset_master` | 15 | asset_id(PK), currency, annual_yield, allow_padding, display_name | 자산 메타 |
| `price_daily` | 37,671 | (asset_id, date, source) PK, OHLCV | Bronze+Silver 15자산 10년 |
| `fx_daily` | 2,603 | date(PK), usd_krw_close | USD/KRW 10년 (Silver gen 신규) |
| `factor_daily` | — | (asset_id, date, factor_name, version) PK | 팩터 |
| `signal_daily` | — | id, asset_id, date, strategy_id | 전략 신호 |
| `backtest_run` / `_equity_curve` / `_trade_log` | — | — | Bronze 백테스트 (Phase 4에서 drop) |
| `users` / `user_sessions` / `chat_sessions` / `chat_messages` | — | — | 인증·채팅 |

---

## Modules

### collector/fdr_client.py
**역할**: FDR 래퍼. retry, fallback, DataFrame 표준화.
**SYMBOL_MAP**: 15종 (Bronze 7 + Silver 8) dict-of-dicts.

```python
SYMBOL_MAP = {"QQQ": {"fdr_symbol": "QQQ", "category": "etf"}, ...}

def fetch_ohlcv(asset_id, start, end) -> pd.DataFrame:
    # retry 3회, fallback 지원
    # _standardize: volume.astype("int64") — int32 overflow 방지 (NVDA 등)
    #               high < low → swap (BTC 2016 아티팩트)
```

**주의**: `astype(int)` 대신 `astype("int64")` 필수. int32 max = 2,147,483,647 → NVDA 초과.

---

### collector/ingest.py
**역할**: fetch → validate → price_daily UPSERT 파이프라인.
**핵심 함수**: `ingest_asset(asset_id, start, end, session)` → `IngestResult`

```python
def ingest_asset(asset_id, start, end, session=None):
    df = fetch_ohlcv(...)           # 1. Fetch
    result = validate_ohlcv(df)    # 2. Validate
    if not result.is_valid: return  # validation_failed → skip store
    _upsert(session, df)           # 3. Store (ON CONFLICT DO UPDATE)
```

**date_gap 경고**: US 공휴일(95일/10년), KR 공휴일(156일/10년) — 정상.

---

### collector/fx_collector.py *(Silver gen 신규)*
**역할**: FDR `USD/KRW` → `fx_daily` UPSERT. Idempotent.
**핵심 함수**: `collect_usd_krw(start, end)` + `upsert_fx_daily(session, df)` + `run(start, end)`

```python
def collect_usd_krw(start, end) -> pd.DataFrame:
    df = _fetch_raw("USD/KRW", start, end)
    # (date, usd_krw_close) 표준화 + Decimal 변환

def upsert_fx_daily(session, df):
    stmt = insert(FxDaily).on_conflict_do_update(
        index_elements=["date"],
        set_={"usd_krw_close": stmt.excluded.usd_krw_close}
    )
```

---

### collector/seed_silver_assets.py *(Silver gen 신규)*
**역할**: asset_master 15행 upsert (Bronze 7 갱신 + Silver 8 신규). 1회성.

```python
ASSETS = [
    {"asset_id": "JEPI", "annual_yield": Decimal("0.08"), "allow_padding": True,
     "history_start_date": "2020-05-20", "currency": "USD", ...},
    # + 14 more
]
def seed(session): insert(AssetMaster).on_conflict_do_update(...)
```

---

### research_engine/simulation/padding.py *(Silver gen 신규)*
**역할**: history 부족 자산(JEPI 등) 10년 패딩. D-2.

```python
def pad_returns(actual_returns, target_days) -> np.ndarray:
    # cyclic 복제: while len(padding) < needed: padding.extend(actual[:take])
    # return np.concatenate([padding, actual])

def prices_with_padding(actual_first_price, padded_returns, padding_len):
    # actual 구간: P0 * cumprod(1 + actual_r[:-1])
    # padding 구간: P0 / cumprod(1 + pad_r[::-1]) → reverse
```

**주의**: `padded_returns[padding_len:]` 전체가 actual returns (인덱스 off-by-one 주의).

---

### research_engine/simulation/wbi.py *(Silver gen 신규)*
**역할**: WBI (Warren Buffett Index) synthetic 가격 시계열 생성. D-5.

```python
def generate_wbi(n_days=2520, seed=42, annual_return=0.20, sigma=0.01):
    mu = (1 + annual_return)**(1/252) - 1
    mu_adj = mu - 0.5 * sigma**2   # Itô drift 보정
    rng = np.random.default_rng(seed)  # 42 고정 — reproducibility
    returns = rng.normal(loc=mu_adj, scale=sigma, size=n_days)
    return 100.0 * np.cumprod(1 + returns)
```

**주의**: seed=42 단일 경로 연환산 ≠ 20% (GBM 분산 정상). 100-seed 앙상블 평균 ≈ 20%.
**Fixture**: `simulation/fixtures/wbi_seed42_10y.npz` (shape 2520) — Phase 2가 import.

---

### research_engine/factors.py
**역할**: OHLCV → 팩터 계산 (returns, SMA, EMA, MACD, RSI, volatility, ATR).

```python
def compute_returns(df) -> pd.DataFrame    # pct_change
def compute_rsi(df, period=14)             # RS = avg_gain / avg_loss
def compute_macd(df)                       # EMA12 - EMA26, signal EMA9
```

---

### api/main.py
**역할**: FastAPI 앱 진입점. 라우터 등록, CORS, 에러 핸들러.

```python
app.include_router(prices.router, prefix="/v1/prices")
app.include_router(factors.router, prefix="/v1/factors")
app.include_router(signals.router, prefix="/v1/signals")
app.include_router(chat.router, prefix="/v1/chat")   # Agentic AI
# ... backtests, dashboard, correlation, auth, profile, analysis
```

**Silver gen 예정**: `simulation.router` + `fx.router` 추가 (Phase 2).

---

### api/services/chat/chat_service.py (Agentic AI)
**역할**: Classifier → DataFetcher → Reporter 파이프라인 (Bronze Phase F 유지).

```python
async def stream_chat(msg, session_id, session, user):
    classification = await llm_classify(msg)  # GPT: strategy/price/correlation/...
    data = await fetch_data(classification)   # price_daily, factor_daily 조회
    report = await generate_report(data)      # GPT-4.1-mini Reporter (PERF-1)
    # LangGraph fallback → build_graph() 호출
```

**Silver gen Phase 4**: `strategy_classify`, `strategy_report` 제거 → `simulation_*` 3종 추가.

---

## Debugging Hints

| 상황 | 힌트 |
|---|---|
| NVDA/고거래량 US 주식 `validation_failed: negative_volume` | `fdr_client._standardize`의 `astype("int64")` 확인. int32 overflow. |
| BTC `high_low_inversion` | `_standardize`의 high/low swap 코드 확인 (2016~2017 FDR 아티팩트). |
| padding 가격 점프 | `prices_with_padding`에서 `padded_returns[padding_len:]` 인덱스 확인. |
| WBI seed=42 수익률이 낮음 | 정상 (GBM 분산). 이론값은 log-drift + 100-seed 앙상블으로 검증. |
| uvicorn --reload 미반영 | `tasklist \| grep python` → `taskkill //F //PID` 전부 종료 후 재시작. |
| DB 세션 background task 에러 | 요청 스코프 세션 전달 금지 → `SessionLocal()` 자체 생성. |
| PowerShell hook `파일 없습니다` | `.claude/settings.json` hook 경로를 절대 경로로 변경. |

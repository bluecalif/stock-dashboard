# Phase 5 Frontend Debug History

> Session: 2026-02-14

## Step 5.11: Frontend Code Bug Fixes

| Bug # | Page | Issue | Fix | File |
|-------|------|-------|-----|------|
| 1 | Home | MiniChart X축 역순 | chartData ASC 정렬 | `DashboardPage.tsx` |
| 5 | Signal | X축 역순 | ASC 정렬 | `SignalOverlay.tsx` |
| 6 | Signal | 마커 설명 없음 | SignalLegend 컴포넌트 추가 | `SignalOverlay.tsx` |
| 7 | Signal | 관망/무신호 구분 불가 | signal=0 회색 원(●) 마커 추가 | `SignalOverlay.tsx` |
| 8 | Signal | 추세추종 미표시 | `trend_follow` → `trend` | `SignalPage.tsx` |
| 10 | Strategy | 전략 ID 불일치 | `trend_follow` → `trend` | `StrategyPage.tsx` |
| 11 | Dashboard | 백테스트 상태 배지 | `completed` → `success` | `DashboardPage.tsx` |

## Step 5.12: Gold/Silver + Volume Chart

| Bug # | Page | Issue | Fix | File |
|-------|------|-------|-----|------|
| 2 | Price | Gold/Silver Network Error | `Promise.allSettled` 방어 처리 + mergeByDate에 volume 포함 | `PricePage.tsx` |
| 3 | Price | 거래량 미표시 | `LineChart` → `ComposedChart` + `Bar`(거래량) + 이중 YAxis, 단일 자산일 때만 표시 | `PriceLineChart.tsx` |

## Step 5.13: Pipeline Fixes + API Bug Fixes

### 5.13-1: Missing Threshold (preprocess_failed)

**증상**: KS200/005930/000660 Factor/Signal/Backtest 전부 생성 실패
```
Missing data for KS200: 6.5% (19 rows) exceeds threshold 5.0%
```

**원인**: `preprocess()` 기본 `missing_threshold=0.05` (5%). 한국 주식은 공휴일 캘린더 차이로 결측치 6.7% 발생.

**수정**:
- `backend/research_engine/factor_store.py`: `store_factors_for_asset()`에 `missing_threshold` 파라미터 추가, `preprocess()` 호출 시 전달
- `backend/scripts/run_research.py`: `store_factors_for_asset()` 및 `preprocess()` 호출에 `missing_threshold=0.10` 전달

### 5.13-2: Backtest store_failed (numpy type)

**증상**: 백테스트 실행은 성공하지만 DB 저장 실패
```
backtest_trade_log INSERT 시 numpy.float64, pandas Timestamp 타입이 SQL에 직접 전달
```

**원인**: `_trades_to_records()`에서 TradeRecord의 필드를 Python native 타입으로 변환하지 않음

**수정**: `backend/research_engine/backtest_store.py`
- `_to_date()` 헬퍼: pandas Timestamp → `datetime.date`
- `_to_float()` 헬퍼: numpy.float64 → Python `float`
- `_trades_to_records()`에서 모든 날짜/숫자 필드에 변환 적용

### 5.13-3: CORS 차단 (Network Error)

**증상**: 프론트엔드 전 페이지 "Network Error" (브라우저 콘솔에서 CORS 에러)

**원인**: CORS `allow_origins`에 `localhost:5173`만 등록. Vite가 포트 충돌으로 `5174`에서 실행되어 CORS 차단.

**추가 이슈**: Windows에서 uvicorn `--reload` (WatchFiles) 리로더가 파일 변경 감지 후 재시작을 완료하지 못하는 현상. 수동 서버 재시작 필요.

**수정**: `backend/api/main.py`
```python
allow_origins=[
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
],
```

### 5.13-4: NaN JSON Serialization Error

**증상**: 시그널 페이지에서 특정 자산/전략 조합 Network Error
```
ValueError: Out of range float values are not JSON compliant: nan
```

**원인**: DB `signal_daily.score` 및 `factor_daily.value` 컬럼에 `NaN` 값 존재. Pydantic → JSON 직렬화 시 실패.

**수정**:
- `backend/api/schemas/signal.py`: `score` 필드에 `@field_validator` 추가 — `math.isnan()` → `None`
- `backend/api/schemas/factor.py`: `value` 필드를 `float | None`으로 변경 + 동일 validator 추가

## Modified Files Summary

### Backend
```
backend/
├── api/
│   ├── main.py                    — CORS: 5174 포트 추가
│   └── schemas/
│       ├── signal.py              — score NaN→None validator
│       └── factor.py              — value NaN→None validator
├── research_engine/
│   ├── backtest_store.py          — _to_date(), _to_float() + _trades_to_records() 타입 변환
│   └── factor_store.py            — missing_threshold 파라미터 추가
└── scripts/
    └── run_research.py            — missing_threshold=0.10 전달
```

### Frontend (previous session)
```
frontend/src/
├── components/charts/
│   ├── PriceLineChart.tsx         — ComposedChart+Bar(거래량), 이중 YAxis
│   └── SignalOverlay.tsx          — ASC정렬, 관망마커, SignalLegend, 툴팁
└── pages/
    ├── DashboardPage.tsx          — ASC정렬, status badge 수정
    ├── PricePage.tsx              — Promise.allSettled, volume 병합
    ├── SignalPage.tsx             — trend_follow→trend
    └── StrategyPage.tsx           — trend_follow→trend
```

## Step 5.14: Bug #9 — mean_reversion close 컬럼 누락

| Bug # | Page/Module | Issue | Fix | File |
|-------|-------------|-------|-----|------|
| 9 | Signal | mean_reversion 시그널 0개 생성 | `df_factors`에 `close` 컬럼 포함 | `run_research.py` |

### 5.14-1: mean_reversion Missing 'close' Column

**증상**: 전 자산에서 mean_reversion 전략 시그널 0개 생성
```
Missing 'close' column for mean_reversion
```

**원인**: `compute_all_factors()`는 팩터 컬럼만 반환 (close 미포함). `run_research.py:125`에서 `df_factors`를 그대로 시그널 생성에 전달하므로 `mean_reversion._raw_signals()`에서 `close` 컬럼 부재로 빈 DataFrame 반환.

**수정**: `run_research.py` — `compute_all_factors()` 호출 후 `df_factors["close"] = df_preprocessed["close"]` 추가

**결과**: 전체 7개 자산 mean_reversion 시그널+백테스트 성공
| 자산 | CAGR | 상태 |
|------|------|------|
| KS200 | 7.64% | ✅ |
| 005930 | 3.94% | ✅ |
| 000660 | 9.93% | ✅ |
| SOXL | 8.90% | ✅ |
| BTC | 2.26% | ✅ |
| GC=F | 3.21% | ✅ |
| SI=F | 12.31% | ✅ |

## Remaining UX Bugs

| # | Page | Issue | Status |
|---|------|-------|--------|
| 4 | Factor | KS200/005930/000660 미표시 | ✅ 파이프라인 수정 완료 |
| 9 | Signal | 평균회귀 마커만 표시 | ✅ close 컬럼 포함으로 수정 완료 |

## Lessons Learned

1. **Windows uvicorn --reload 불안정**: WatchFiles 리로더가 파일 변경 후 재시작 미완료. 코드 변경 시 수동 재시작 권장.
2. **Vite 포트 충돌**: 5173 점유 시 자동으로 5174 사용. CORS에 연속 포트 미리 등록 필요.
3. **NaN in DB**: pandas/numpy 계산 결과에 NaN이 DB에 저장됨. API 스키마 레벨에서 방어적 변환 필수.
4. **numpy 타입 → SQL**: SQLAlchemy bulk_insert_mappings에 numpy.float64/Timestamp 직접 전달 시 실패. Python native 타입 변환 필요.
5. **팩터 DF에 원시 컬럼 누락**: `compute_all_factors()`는 파생 팩터만 반환. 전략이 원시 OHLCV 컬럼을 필요로 하면 별도로 합쳐줘야 함.

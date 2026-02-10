---
name: backend-dev
description: Stock Dashboard 백엔드 개발 가이드. Python, FastAPI, SQLAlchemy, PostgreSQL (Railway). FDR 수집기(collector), 분석 엔진(research_engine), REST API. OHLCV 스키마, 팩터 생성, 전략 엔진, 백테스트. Router-Service-Repository 패턴.
---

# Backend Development Guidelines

## Purpose

Stock Dashboard(7개 자산 → 일봉 수집/분석/시각화) 백엔드 개발 가이드.
Python + FastAPI + SQLAlchemy + PostgreSQL (Railway) + FinanceDataReader 기반.

## When to Use This Skill

- collector 모듈 구현 (FDR 데이터 수집, 정합성 검증, UPSERT)
- research_engine 모듈 구현 (팩터 생성, 전략 신호, 백테스트)
- API 엔드포인트/라우터 생성
- 서비스/리포지토리 구현
- Pydantic 스키마 정의
- DB 모델/마이그레이션

---

## Architecture Overview

```
scheduler (Task Scheduler)
    ↓
collector (FDR REST → 정합성 검증 → UPSERT)
    ↓
PostgreSQL (Railway)
    ↓
research_engine (팩터 → 전략 신호 → 백테스트)
    ↓
API (FastAPI: 조회)
    ↓
dashboard (시각화)
```

## Directory Structure

```
collector/
  fdr_client.py         # FDR 데이터 조회
  validators.py         # 정합성 검증 (고가/저가 역전, 음수, 중복)
  upserter.py           # DB UPSERT 로직
  scheduler.py          # 배치 스케줄링

research_engine/
  factors.py            # 팩터 생성 (ret, sma, ema, macd, rsi, vol, atr)
  strategies/           # 전략 엔진
    momentum.py
    trend.py
    mean_reversion.py
  backtest.py           # 백테스트 실행기
  metrics.py            # 성과 평가 (Sharpe, MDD, CAGR 등)

api/
  main.py               # FastAPI 앱
  routers/              # 라우터
    prices.py
    factors.py
    signals.py
    backtests.py
  services/             # 비즈니스 로직
  repositories/         # DB 접근
  schemas/              # Pydantic 스키마

config/
  settings.py           # Pydantic Settings (DATABASE_URL, etc.)

tests/
  test_collector/
  test_research_engine/
  test_api/
```

---

## Core Rules (6 Rules)

### 1. OHLCV 표준 스키마 준수

```python
# price_daily 필수 필드
asset_id: str       # "KS200", "005930", "SOXL", etc.
date: date
open: float
high: float
low: float
close: float
volume: int
source: str          # "fdr", "hantoo"
ingested_at: datetime
# PK: (asset_id, date, source)
```

### 2. FDR Primary Source

```python
# 전 자산(7종) FDR 1순위
ASSETS = {
    "KS200": {"symbol": "KS200", "source": "fdr"},
    "005930": {"symbol": "005930", "source": "fdr"},
    "000660": {"symbol": "000660", "source": "fdr"},
    "SOXL": {"symbol": "SOXL", "source": "fdr"},
    "BTC/KRW": {"symbol": "BTC/KRW", "source": "fdr", "fallback": "BTC/USD"},
    "GC=F": {"symbol": "GC=F", "source": "fdr"},
    "SI=F": {"symbol": "SI=F", "source": "fdr"},
}
# Hantoo fallback은 v0.9+에서 추가
```

### 3. Idempotent UPSERT

```python
# Bad: INSERT 중복 시 에러
session.add(PriceDaily(...))

# Good: UPSERT (ON CONFLICT DO UPDATE)
from sqlalchemy.dialects.postgresql import insert
stmt = insert(PriceDaily).values(rows)
stmt = stmt.on_conflict_do_update(
    index_elements=["asset_id", "date", "source"],
    set_={col: stmt.excluded[col] for col in update_cols}
)
```

### 4. 정합성 검증

```python
def validate_ohlcv(df: pd.DataFrame) -> list[str]:
    errors = []
    if (df["high"] < df["low"]).any():
        errors.append("high_low_inversion")
    if (df[["open","high","low","close"]] < 0).any().any():
        errors.append("negative_price")
    if df.duplicated(subset=["asset_id", "date"]).any():
        errors.append("duplicate_key")
    return errors
```

### 5. Router → Service → Repository 분리

```python
# Router: 라우팅만
@router.get("/v1/prices/daily")
async def get_prices(asset_id: str, service=Depends(get_price_service)):
    return await service.get_daily(asset_id)

# Service: 비즈니스 로직
class PriceService:
    async def get_daily(self, asset_id: str):
        return await self.repo.find_daily(asset_id)

# Repository: DB 접근
class PriceRepository:
    async def find_daily(self, asset_id: str):
        stmt = select(PriceDaily).where(PriceDaily.asset_id == asset_id)
        return (await self.session.execute(stmt)).scalars().all()
```

### 6. Pydantic Settings

```python
# Bad
db_url = os.environ.get("DATABASE_URL")

# Good
from config.settings import settings
db_url = settings.database_url
```

---

## Collector Patterns

### FDR Data Fetch with Retry

```python
import FinanceDataReader as fdr
import time

def fetch_with_retry(symbol: str, start: str, end: str, max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            df = fdr.DataReader(symbol, start, end)
            if df.empty:
                raise ValueError(f"Empty result for {symbol}")
            return df
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # 지수 백오프
```

---

## Research Engine Patterns

### Factor Generation

```python
def compute_factors(df: pd.DataFrame) -> pd.DataFrame:
    df["ret_1d"] = df["close"].pct_change(1)
    df["sma_20"] = df["close"].rolling(20).mean()
    df["rsi_14"] = compute_rsi(df["close"], 14)
    df["vol_20"] = df["ret_1d"].rolling(20).std()
    return df
```

---

## Anti-Patterns

| Pattern | Problem |
|---------|---------|
| Router에 비즈니스 로직 | 테스트 어려움, 재사용 불가 |
| INSERT without UPSERT | 재실행 시 중복 에러 |
| 정합성 검증 없이 저장 | 잘못된 데이터 적재 |
| 환경변수 직접 접근 | 타입 안전성 없음 |
| Service에서 HTTPException | 레이어 결합 |

---

## Related Docs

- `docs/masterplan-v0.md` - 전체 설계 (스키마, API 명세, 마일스톤)
- `docs/data-accessibility-report.md` - FDR 접근성 검증 결과
- `docs/guide_financereader.md` - FDR 사용법
- `docs/guide_hantoo.md` - Hantoo API 참조 (v0.9+용)

---

**Skill Status**: Core guide complete.

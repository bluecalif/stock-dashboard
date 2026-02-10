# Phase 1: Project Skeleton + DB + Collector
> Last Updated: 2026-02-10
> Status: Planning

## 1. Summary (개요)

**목적**: 코드 없는 문서 전용 상태에서 실제 동작하는 프로젝트 골격을 구축한다.
Python 프로젝트 설정, DB 모델 정의, Alembic 마이그레이션, FDR 기반 데이터 수집 파이프라인(래퍼 + 검증 + 오케스트레이션)까지 완성한다.

**범위**: Task 1.1 ~ 1.9 (9개 태스크)

**예상 결과물**:
- `pyproject.toml` + 가상환경 + 전체 의존성 설치
- `.env.example` + `config/settings.py` (Pydantic Settings)
- `db/models.py` — SQLAlchemy 모델 8개 테이블
- Alembic 초기화 + 초기 마이그레이션
- `asset_master` 시드 데이터 (7개 자산)
- `collector/fdr_client.py` — FDR 래퍼 (지수 백오프 기본 재시도)
- `collector/validators.py` — OHLCV 정합성 검증
- `collector/ingest.py` — 수집 오케스트레이션 (fetch → validate → store)
- `tests/unit/` — 심볼 매핑, 검증, 수집 단위 테스트

## 2. Current State (현재 상태)

- **Phase 0 완료**: 문서 전용 상태. 앱 코드 없음.
- **Git**: `master` 브랜치, 마지막 커밋 `c9a70f7`
- **데이터 접근성**: Conditional Go — FDR 전 자산 PASS, `DATABASE_URL` 미설정
- **기존 파일**: 마스터플랜, 데이터 접근성 보고서, CLAUDE.md, Skills, 온보딩 문서

## 3. Target State (목표 상태)

| 영역 | 목표 |
|------|------|
| 프로젝트 | `pyproject.toml` 기반 Python 프로젝트, ruff/pytest 설정 완료 |
| 설정 | Pydantic Settings 기반 환경변수 관리, `.env.example` 제공 |
| DB 모델 | 8개 테이블 SQLAlchemy ORM 모델 정의 완료 |
| 마이그레이션 | Alembic 초기화, 초기 revision 생성 |
| 시드 | 7개 자산 `asset_master` 시드 스크립트 |
| 수집기 | FDR 래퍼 + 정합성 검증 + 기본 수집 오케스트레이션 |
| 테스트 | 심볼 매핑, 검증, 수집 단위 테스트 통과 |

## 4. Implementation Steps (구현 단계)

### Step 1: 프로젝트 초기화 (Task 1.1)

**목표**: Python 프로젝트 골격 + 의존성 설치

**파일 생성**:
- `pyproject.toml` — 프로젝트 메타데이터 + 의존성 + 도구 설정
- 패키지 `__init__.py` 파일들: `collector/`, `research_engine/`, `api/`, `db/`, `config/`, `tests/`

**의존성**:
```toml
[project]
name = "stock-dashboard"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "financedatareader",
    "sqlalchemy[asyncio]>=2.0",
    "psycopg2-binary",
    "fastapi>=0.100",
    "uvicorn[standard]",
    "pydantic>=2.0",
    "pydantic-settings",
    "alembic",
    "pandas>=2.0",
    "numpy",
    "python-dotenv",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0",
    "pytest-asyncio",
    "httpx",
    "ruff",
]
```

**도구 설정** (pyproject.toml 내):
```toml
[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

**검증 기준**:
- `pip install -e ".[dev]"` 성공
- `ruff check .` 에러 없음
- `python -c "import collector; import db; import config"` 성공

---

### Step 2: 환경 설정 (Task 1.2)

**목표**: `.env.example` + Pydantic Settings 기반 설정 모듈

**파일 생성**:
- `.env.example` — 환경변수 템플릿
- `config/__init__.py`
- `config/settings.py` — Pydantic Settings 클래스

**`.env.example`**:
```env
DATABASE_URL=postgresql://user:pass@host:port/dbname
FDR_TIMEOUT=30
LOG_LEVEL=INFO
ALERT_WEBHOOK_URL=
PYTHONUTF8=1
```

**`config/settings.py`**:
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = ""
    fdr_timeout: int = 30
    log_level: str = "INFO"
    alert_webhook_url: str = ""
    pythonutf8: int = 1

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
```

**핵심 규칙**:
- 환경변수 직접 `os.environ` 접근 금지 → `settings.database_url` 사용
- `.env` 파일은 `.gitignore`에 포함, `.env.example`만 커밋
- `DATABASE_URL` 빈 값 허용 (Task 1.4 전까지 DB 없이 진행 가능)

**검증 기준**:
- `.env.example` 존재
- `from config.settings import settings` import 성공
- `.gitignore`에 `.env` 포함 확인

---

### Step 3: DB 모델 정의 (Task 1.3)

**목표**: SQLAlchemy ORM으로 8개 테이블 모델 정의

**파일 생성**:
- `db/__init__.py`
- `db/models.py` — 전체 모델
- `db/session.py` — 엔진 + 세션 팩토리

**8개 테이블 상세 스키마**:

#### `asset_master`
| Column | Type | Constraint |
|--------|------|-----------|
| asset_id | String(20) | PK |
| name | String(100) | NOT NULL |
| category | String(20) | NOT NULL (stock/index/etf/crypto/commodity) |
| source_priority | JSON | NOT NULL |
| is_active | Boolean | DEFAULT True |

#### `price_daily`
| Column | Type | Constraint |
|--------|------|-----------|
| asset_id | String(20) | PK, FK(asset_master) |
| date | Date | PK |
| source | String(20) | PK |
| open | Float | NOT NULL |
| high | Float | NOT NULL |
| low | Float | NOT NULL |
| close | Float | NOT NULL |
| volume | BigInteger | NOT NULL |
| ingested_at | DateTime(timezone=True) | NOT NULL, DEFAULT now() |

인덱스: `(asset_id, date DESC)`, `(date)`

#### `factor_daily`
| Column | Type | Constraint |
|--------|------|-----------|
| asset_id | String(20) | PK, FK(asset_master) |
| date | Date | PK |
| factor_name | String(50) | PK |
| version | String(10) | PK |
| value | Float | NOT NULL |

#### `signal_daily`
| Column | Type | Constraint |
|--------|------|-----------|
| id | Integer | PK, AUTO |
| asset_id | String(20) | FK(asset_master), NOT NULL |
| date | Date | NOT NULL |
| strategy_id | String(50) | NOT NULL |
| signal | Integer | NOT NULL |
| score | Float | |
| action | String(10) | |
| meta_json | JSON | |

#### `backtest_run`
| Column | Type | Constraint |
|--------|------|-----------|
| run_id | UUID | PK, DEFAULT uuid4 |
| strategy_id | String(50) | NOT NULL |
| config_json | JSON | NOT NULL |
| started_at | DateTime(tz) | NOT NULL |
| ended_at | DateTime(tz) | |
| status | String(20) | NOT NULL (pending/running/done/failed) |

#### `backtest_equity_curve`
| Column | Type | Constraint |
|--------|------|-----------|
| run_id | UUID | PK, FK(backtest_run) |
| date | Date | PK |
| equity | Float | NOT NULL |
| drawdown | Float | NOT NULL |

#### `backtest_trade_log`
| Column | Type | Constraint |
|--------|------|-----------|
| id | Integer | PK, AUTO |
| run_id | UUID | FK(backtest_run), NOT NULL |
| asset_id | String(20) | FK(asset_master), NOT NULL |
| entry_date | Date | NOT NULL |
| exit_date | Date | |
| side | String(10) | NOT NULL (long/short) |
| pnl | Float | |
| cost | Float | |

#### `job_run`
| Column | Type | Constraint |
|--------|------|-----------|
| job_id | UUID | PK, DEFAULT uuid4 |
| job_name | String(100) | NOT NULL |
| started_at | DateTime(tz) | NOT NULL |
| ended_at | DateTime(tz) | |
| status | String(20) | NOT NULL (pending/running/done/failed) |
| error_message | Text | |

**`db/session.py` 패턴**:
```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config.settings import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=(settings.log_level == "DEBUG"),
) if settings.database_url else None

SessionLocal = sessionmaker(bind=engine) if engine else None
```

**핵심 규칙**:
- 모든 DateTime은 timezone-aware (`timezone=True`)
- `price_daily` PK: `(asset_id, date, source)` — 복합 PK
- FK는 `asset_master.asset_id` 참조
- `engine = None` 허용 (DB 없이 모델 import 가능하도록)

**검증 기준**:
- `from db.models import AssetMaster, PriceDaily, ...` import 성공 (DB 연결 없이)
- 8개 테이블 모델 클래스 존재
- PK/FK/인덱스 정의 일치

---

### Step 4: Alembic 초기화 (Task 1.4)

**목표**: Alembic 초기 설정 + 첫 마이그레이션 생성

**선행 조건**: `DATABASE_URL` 설정 필수

**파일 생성/수정**:
- `alembic.ini` — Alembic 설정 (sqlalchemy.url은 env.py에서 동적 설정)
- `db/alembic/env.py` — target_metadata 설정 + DATABASE_URL 동적 로드
- `db/alembic/versions/xxxx_initial.py` — 초기 마이그레이션

**alembic.ini 핵심 설정**:
```ini
[alembic]
script_location = db/alembic
sqlalchemy.url = # env.py에서 동적 설정
```

**env.py 핵심 패턴**:
```python
from db.models import Base
from config.settings import settings

target_metadata = Base.metadata

def run_migrations_online():
    connectable = create_engine(settings.database_url)
    # ...
```

**실행 명령**:
```bash
alembic init db/alembic
alembic revision --autogenerate -m "initial: 8 tables"
alembic upgrade head
```

**검증 기준**:
- `alembic current` 실행 성공
- DB에 8개 테이블 생성 확인
- `alembic downgrade -1` + `alembic upgrade head` 왕복 성공

---

### Step 5: Asset Master 시드 (Task 1.5)

**목표**: 7개 자산 마스터 데이터 삽입

**파일 생성**:
- `scripts/seed_assets.py`

**시드 데이터**:
```python
ASSETS = [
    {"asset_id": "KS200", "name": "KOSPI200", "category": "index",
     "source_priority": ["fdr"], "is_active": True},
    {"asset_id": "005930", "name": "삼성전자", "category": "stock",
     "source_priority": ["fdr", "hantoo"], "is_active": True},
    {"asset_id": "000660", "name": "SK하이닉스", "category": "stock",
     "source_priority": ["fdr", "hantoo"], "is_active": True},
    {"asset_id": "SOXL", "name": "SOXL ETF", "category": "etf",
     "source_priority": ["fdr"], "is_active": True},
    {"asset_id": "BTC", "name": "Bitcoin", "category": "crypto",
     "source_priority": ["fdr"], "is_active": True},
    {"asset_id": "GC=F", "name": "Gold Futures", "category": "commodity",
     "source_priority": ["fdr"], "is_active": True},
    {"asset_id": "SI=F", "name": "Silver Futures", "category": "commodity",
     "source_priority": ["fdr"], "is_active": True},
]
```

**핵심 규칙**:
- idempotent: 재실행 시 중복 에러 없음 (UPSERT 또는 존재 시 skip)
- `encoding='utf-8'` 명시 (한글 이름)

**검증 기준**:
- 스크립트 실행 후 `asset_master` 테이블에 7개 행 존재
- 재실행 시 에러 없음

---

### Step 6: FDR 래퍼 (Task 1.6)

**목표**: FinanceDataReader 호출 래핑 + 기본 재시도 + DataFrame 표준화

**파일 생성**:
- `collector/__init__.py`
- `collector/fdr_client.py`

**FDR 심볼 매핑**:
```python
SYMBOL_MAP = {
    "KS200":  {"fdr_symbol": "KS200",   "category": "index"},
    "005930": {"fdr_symbol": "005930",   "category": "stock"},
    "000660": {"fdr_symbol": "000660",   "category": "stock"},
    "SOXL":   {"fdr_symbol": "SOXL",    "category": "etf"},
    "BTC":    {"fdr_symbol": "BTC/KRW",  "category": "crypto", "fallback": "BTC/USD"},
    "GC=F":   {"fdr_symbol": "GC=F",    "category": "commodity"},
    "SI=F":   {"fdr_symbol": "SI=F",    "category": "commodity"},
}
```

**핵심 함수**:
```python
def fetch_ohlcv(asset_id: str, start: str, end: str) -> pd.DataFrame:
    """
    FDR에서 OHLCV 데이터 가져오기.
    - 기본 재시도 (3회, 지수 백오프)
    - BTC fallback (BTC/KRW → BTC/USD)
    - 반환 DataFrame 표준화: 컬럼명 소문자, asset_id/source 컬럼 추가
    """
```

**DataFrame 표준화 규칙**:
1. FDR 반환 컬럼(`Open`, `High`, `Low`, `Close`, `Volume`) → 소문자 변환
2. 인덱스(`Date`) → `date` 컬럼으로 변환
3. `asset_id`, `source="fdr"` 컬럼 추가
4. `volume`을 `int`로 변환 (NaN → 0)
5. `ingested_at` 컬럼 추가 (현재 UTC 시각)

**검증 기준**:
- 7개 자산 각각 `fetch_ohlcv` 호출 성공
- 반환 DataFrame에 `asset_id, date, open, high, low, close, volume, source, ingested_at` 컬럼 존재
- 빈 결과 시 명확한 에러 메시지

---

### Step 7: 정합성 검증 (Task 1.7)

**목표**: OHLCV 데이터 정합성 검증 함수

**파일 생성**:
- `collector/validators.py`

**검증 항목**:
| 검증 | 조건 | 처리 |
|------|------|------|
| 고가/저가 역전 | `high < low` | 에러 리포트 |
| 음수 가격 | `open/high/low/close < 0` | 에러 리포트 |
| 중복 키 | `(asset_id, date)` 중복 | 에러 리포트 |
| 필수 컬럼 누락 | 7개 필수 컬럼 중 누락 | 에러 리포트 |
| 빈 DataFrame | `len(df) == 0` | 에러 리포트 |
| volume 음수 | `volume < 0` | 에러 리포트 |

**반환 구조**:
```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]      # ["high_low_inversion:3rows", "negative_price:1rows"]
    warnings: list[str]    # ["zero_volume:5rows"]
    row_count: int
    error_row_count: int
```

**핵심 규칙**:
- 검증 실패 시 데이터를 저장하지 않음 (fail-fast)
- 경고(warning)는 로깅만, 저장은 허용 (예: volume=0)
- 검증 함수는 순수 함수 (DB 의존 없음, DataFrame만 입력)

**검증 기준**:
- 정상 데이터 → `is_valid=True`
- 고가/저가 역전 데이터 → `is_valid=False`, `"high_low_inversion"` 에러
- 음수 가격 → `is_valid=False`, `"negative_price"` 에러
- 빈 DataFrame → `is_valid=False`, `"empty_dataframe"` 에러

---

### Step 8: 수집 오케스트레이션 (Task 1.8)

**목표**: fetch → validate → store 파이프라인 통합

**파일 생성**:
- `collector/ingest.py`

**핵심 함수**:
```python
def ingest_asset(asset_id: str, start: str, end: str, session) -> IngestResult:
    """단일 자산 수집 파이프라인: fetch → validate → store"""
    # 1. FDR에서 데이터 fetch
    # 2. 정합성 검증
    # 3. DB 저장 (bulk insert, 아직 UPSERT 아님 — Phase 2에서 구현)
    # 4. 결과 반환

def ingest_all(start: str, end: str, session) -> list[IngestResult]:
    """전체 활성 자산 수집"""
    # asset_master에서 is_active=True 조회
    # 각 자산 ingest_asset 실행
    # 결과 집계
```

**IngestResult 구조**:
```python
@dataclass
class IngestResult:
    asset_id: str
    status: str          # "success" | "validation_failed" | "fetch_failed"
    row_count: int
    errors: list[str]
    elapsed_ms: float
```

**파이프라인 흐름**:
```
ingest_all()
  ├─ for asset in active_assets:
  │    ├─ fetch_ohlcv(asset_id, start, end)
  │    ├─ validate_ohlcv(df)
  │    ├─ if valid: bulk_insert(session, df)
  │    └─ collect IngestResult
  └─ return results
```

**핵심 규칙**:
- 자산 단위 독립 실행 (한 자산 실패 시 다른 자산 계속 진행)
- 이 단계에서는 단순 INSERT (UPSERT는 Phase 2 Task 2.2)
- 로깅: 자산별 시작/종료/결과 로그 출력

**검증 기준**:
- 단일 자산 수집 성공 → `status="success"`, `row_count > 0`
- 검증 실패 시 → `status="validation_failed"`, DB 저장 안 됨
- FDR 호출 실패 시 → `status="fetch_failed"`

---

### Step 9: 단위 테스트 (Task 1.9)

**목표**: 수집기 핵심 로직 테스트

**파일 생성**:
- `tests/__init__.py`
- `tests/unit/__init__.py`
- `tests/unit/test_fdr_client.py`
- `tests/unit/test_validators.py`
- `tests/unit/test_ingest.py`
- `tests/conftest.py` — 공통 fixture

**테스트 케이스**:

#### `test_fdr_client.py`
| 테스트 | 설명 |
|--------|------|
| `test_symbol_map_completeness` | 7개 자산 모두 SYMBOL_MAP에 존재 |
| `test_symbol_map_fdr_symbol` | FDR 심볼이 올바른 형식 |
| `test_fetch_ohlcv_columns` | 반환 DataFrame 컬럼 검증 |
| `test_fetch_ohlcv_btc_fallback` | BTC/KRW 실패 시 BTC/USD fallback |
| `test_fetch_ohlcv_empty_raises` | 빈 결과 시 에러 |

#### `test_validators.py`
| 테스트 | 설명 |
|--------|------|
| `test_valid_data_passes` | 정상 데이터 통과 |
| `test_high_low_inversion` | 고가 < 저가 탐지 |
| `test_negative_price` | 음수 가격 탐지 |
| `test_duplicate_key` | 중복 키 탐지 |
| `test_empty_dataframe` | 빈 DataFrame 탐지 |
| `test_missing_columns` | 필수 컬럼 누락 탐지 |
| `test_zero_volume_warning` | volume=0 경고 (에러 아님) |

#### `test_ingest.py`
| 테스트 | 설명 |
|--------|------|
| `test_ingest_asset_success` | 정상 수집 결과 |
| `test_ingest_asset_validation_failure` | 검증 실패 시 미저장 |
| `test_ingest_asset_fetch_failure` | FDR 호출 실패 처리 |
| `test_ingest_all_partial_failure` | 한 자산 실패 시 나머지 계속 |

**테스트 전략**:
- FDR 호출은 mock (외부 API 의존 제거)
- DB 저장은 SQLite in-memory 또는 mock session
- fixture: `sample_ohlcv_df`, `invalid_ohlcv_df`, `mock_fdr_client`

**검증 기준**:
- `python -m pytest tests/unit/ -v` 전체 통과
- `ruff check .` 린트 통과

---

## 5. 의존성 그래프

```
1.1 (pyproject.toml) ─────────────────────┐
 ├── 1.2 (.env + settings) ──────────────┐│
 ├── 1.3 (DB models) ──────────────────┐ ││
 ├── 1.6 (FDR client) ──────────────┐  │ ││
 └── 1.7 (validators) ───────────┐  │  │ ││
                                  │  │  │ ││
                                  ↓  ↓  ↓ ↓↓
                            1.8 (ingest) ←─┤
                                  │        │
                                  ↓        ↓
                            1.9 (tests)  1.4 (Alembic) ← DB 필요
                                            ↓
                                         1.5 (seed)
```

**병렬 실행 가능 그룹**:
- **Group A** (DB 불필요): 1.1 → [1.2, 1.3, 1.6, 1.7] 병렬 → 1.8 → 1.9
- **Group B** (DB 필수): 1.2 + 1.3 완료 후 → 1.4 → 1.5

## 6. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| `DATABASE_URL` 미설정으로 Task 1.4 블록 | 1.4/1.5 지연 | 1.1/1.3/1.6/1.7/1.8/1.9는 DB 없이 선행. 1.4는 DB 설정 후 진행 |
| FDR API 변경/장애 | fetch 실패 | 재시도 로직, mock 테스트로 개발 진행 |
| SQLAlchemy 2.x 호환 이슈 | 모델 정의 오류 | Mapped Column 패턴 사용, 공식 문서 참조 |
| Windows 인코딩 이슈 | 한글 깨짐 | `PYTHONUTF8=1`, 명시적 encoding 파라미터 |
| FDR DataFrame 컬럼명 변경 | 표준화 로직 파손 | 컬럼명 매핑 딕셔너리로 유연하게 처리 |

## 7. Convention Checklist

### 데이터 관련
- [ ] OHLCV 표준 스키마 준수 (asset_id, date, open, high, low, close, volume, source, ingested_at)
- [ ] FDR primary source 사용 (모든 자산)
- [ ] price_daily PK: (asset_id, date, source)

### 수집 관련
- [ ] 정합성 검증 (고가/저가 역전, 음수 가격, 중복)
- [ ] 자산 단위 독립 실행 (부분 실패 허용)
- [ ] DataFrame 표준화 (소문자 컬럼, asset_id/source 추가)

### 코드 관련
- [ ] Pydantic Settings 사용 (os.environ 직접 접근 금지)
- [ ] 인코딩 명시 (utf-8 / utf-8-sig)
- [ ] ruff lint 통과
- [ ] pytest 전체 통과

## 8. 생성 파일 목록 (Phase 1 완료 시)

```
stock-dashboard/
├── pyproject.toml                    # 1.1
├── .env.example                      # 1.2
├── .gitignore                        # 1.2 (수정)
├── alembic.ini                       # 1.4
├── config/
│   ├── __init__.py                   # 1.2
│   └── settings.py                   # 1.2
├── db/
│   ├── __init__.py                   # 1.3
│   ├── models.py                     # 1.3
│   ├── session.py                    # 1.3
│   └── alembic/                      # 1.4
│       ├── env.py
│       ├── script.py.mako
│       └── versions/
│           └── xxxx_initial.py
├── collector/
│   ├── __init__.py                   # 1.6
│   ├── fdr_client.py                 # 1.6
│   ├── validators.py                 # 1.7
│   └── ingest.py                     # 1.8
├── research_engine/
│   └── __init__.py                   # 1.1
├── api/
│   └── __init__.py                   # 1.1
├── scripts/
│   └── seed_assets.py                # 1.5
└── tests/
    ├── __init__.py                   # 1.9
    ├── conftest.py                   # 1.9
    └── unit/
        ├── __init__.py               # 1.9
        ├── test_fdr_client.py        # 1.9
        ├── test_validators.py        # 1.9
        └── test_ingest.py            # 1.9
```

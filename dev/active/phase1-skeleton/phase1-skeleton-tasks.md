# Phase 1 Tasks
> Last Updated: 2026-02-10
> Status: Planning

## Overview
- **Total Tasks**: 9
- **Size Distribution**: S: 2, M: 5, L: 1, XL: 0 (+ 테스트 M: 1)
- **DB 불필요**: 1.1, 1.2, 1.3, 1.6, 1.7, 1.8, 1.9
- **DB 필수**: 1.4, 1.5

---

## Task 1.1: `pyproject.toml` + 의존성 설치 `[S]`
- **Dependencies**: 없음
- **Branch**: `feature/phase1-skeleton`
- **Commit**: `[phase1-skeleton] Step 1.1: pyproject.toml + 의존성 설치`

### Checklist
- [ ] `pyproject.toml` 생성 (PEP 621)
  - [ ] project metadata (name, version, requires-python)
  - [ ] dependencies (core 11개)
  - [ ] optional-dependencies.dev (4개)
  - [ ] [tool.ruff] 설정
  - [ ] [tool.pytest.ini_options] 설정
- [ ] 패키지 `__init__.py` 생성
  - [ ] `collector/__init__.py`
  - [ ] `research_engine/__init__.py`
  - [ ] `api/__init__.py`
  - [ ] `db/__init__.py`
  - [ ] `config/__init__.py`
  - [ ] `tests/__init__.py`
  - [ ] `tests/unit/__init__.py`
- [ ] `pip install -e ".[dev]"` 성공
- [ ] `ruff check .` 통과
- [ ] `python -c "import collector; import db; import config"` 성공

---

## Task 1.2: `.env.example` + 환경 설정 `[S]`
- **Dependencies**: 1.1
- **Commit**: `[phase1-skeleton] Step 1.2: .env.example + Pydantic Settings`

### Checklist
- [ ] `.env.example` 생성
  - [ ] DATABASE_URL
  - [ ] FDR_TIMEOUT
  - [ ] LOG_LEVEL
  - [ ] ALERT_WEBHOOK_URL
  - [ ] PYTHONUTF8
- [ ] `config/settings.py` 생성
  - [ ] Settings 클래스 (BaseSettings 상속)
  - [ ] 모든 필드 기본값 설정 (DATABASE_URL="" 포함)
  - [ ] model_config env_file 설정
  - [ ] settings 싱글턴 인스턴스
- [ ] `.gitignore` 수정: `.env` 추가
- [ ] `from config.settings import settings` import 성공
- [ ] DATABASE_URL 빈 값에서도 import 에러 없음

---

## Task 1.3: `db/models.py` — SQLAlchemy 모델 `[M]`
- **Dependencies**: 1.1
- **Commit**: `[phase1-skeleton] Step 1.3: SQLAlchemy 모델 8개 테이블`

### Checklist
- [ ] `db/models.py` 생성 — 8개 모델 클래스
  - [ ] `AssetMaster` (asset_id PK, name, category, source_priority JSON, is_active)
  - [ ] `PriceDaily` (composite PK: asset_id+date+source, OHLCV, ingested_at)
  - [ ] `FactorDaily` (composite PK: asset_id+date+factor_name+version, value)
  - [ ] `SignalDaily` (auto PK, asset_id FK, date, strategy_id, signal, score, action, meta_json)
  - [ ] `BacktestRun` (UUID PK, strategy_id, config_json, started_at, ended_at, status)
  - [ ] `BacktestEquityCurve` (composite PK: run_id+date, equity, drawdown)
  - [ ] `BacktestTradeLog` (auto PK, run_id FK, asset_id FK, entry/exit_date, side, pnl, cost)
  - [ ] `JobRun` (UUID PK, job_name, started_at, ended_at, status, error_message)
- [ ] `Base = declarative_base()` 또는 `DeclarativeBase` 설정
- [ ] FK 관계 정의 (asset_master ← price_daily, factor_daily 등)
- [ ] 인덱스 정의
  - [ ] price_daily: (asset_id, date DESC), (date)
  - [ ] factor_daily: (asset_id, date DESC)
  - [ ] signal_daily: (asset_id, date, strategy_id)
- [ ] `db/session.py` 생성
  - [ ] engine 생성 (DATABASE_URL 빈 값이면 None)
  - [ ] SessionLocal 팩토리
  - [ ] get_session 헬퍼
- [ ] DB 연결 없이 모델 import 성공 확인

---

## Task 1.4: Alembic 초기화 + 초기 마이그레이션 `[M]`
- **Dependencies**: 1.2, 1.3
- **Blocker**: `DATABASE_URL` 설정 필수
- **Commit**: `[phase1-skeleton] Step 1.4: Alembic 초기화 + initial migration`

### Checklist
- [ ] `DATABASE_URL` 설정 확인
- [ ] `alembic init db/alembic`
- [ ] `alembic.ini` 수정
  - [ ] script_location = db/alembic
  - [ ] sqlalchemy.url 제거 (env.py에서 동적)
- [ ] `db/alembic/env.py` 수정
  - [ ] `from db.models import Base` import
  - [ ] `from config.settings import settings` import
  - [ ] target_metadata = Base.metadata
  - [ ] run_migrations_online에서 settings.database_url 사용
- [ ] `alembic revision --autogenerate -m "initial: 8 tables"` 성공
- [ ] 생성된 revision 파일 검토 (8개 테이블 포함 확인)
- [ ] `alembic upgrade head` 성공
- [ ] DB에 8개 테이블 + alembic_version 존재 확인
- [ ] `alembic downgrade -1` + `alembic upgrade head` 왕복 성공

---

## Task 1.5: `asset_master` 시드 스크립트 `[S]`
- **Dependencies**: 1.4
- **Commit**: `[phase1-skeleton] Step 1.5: asset_master 시드 스크립트`

### Checklist
- [ ] `scripts/seed_assets.py` 생성
  - [ ] 7개 자산 데이터 정의
  - [ ] idempotent 실행 (존재 시 skip 또는 update)
  - [ ] `encoding='utf-8'` 명시 (한글 이름)
  - [ ] 실행 결과 출력 (inserted/skipped 카운트)
- [ ] 스크립트 실행: `python scripts/seed_assets.py`
- [ ] asset_master 테이블 7개 행 확인
- [ ] 재실행 시 에러 없음 + 중복 미발생

---

## Task 1.6: `collector/fdr_client.py` — FDR 래퍼 `[M]`
- **Dependencies**: 1.1
- **Commit**: `[phase1-skeleton] Step 1.6: FDR 래퍼 (fdr_client.py)`

### Checklist
- [ ] `collector/fdr_client.py` 생성
  - [ ] SYMBOL_MAP 정의 (7개 자산)
    - [ ] KS200, 005930, 000660, SOXL, BTC, GC=F, SI=F
    - [ ] BTC: fdr_symbol="BTC/KRW", fallback="BTC/USD"
  - [ ] `fetch_ohlcv(asset_id, start, end)` 함수
    - [ ] SYMBOL_MAP에서 FDR 심볼 조회
    - [ ] `fdr.DataReader(symbol, start, end)` 호출
    - [ ] 기본 재시도 (max_retries=3, 지수 백오프)
    - [ ] BTC: BTC/KRW 실패 시 BTC/USD fallback
    - [ ] 빈 결과 시 ValueError raise
    - [ ] DataFrame 표준화
  - [ ] `_standardize_df(df, asset_id)` 내부 함수
    - [ ] 컬럼명 소문자 변환
    - [ ] Date 인덱스 → date 컬럼
    - [ ] asset_id, source="fdr" 추가
    - [ ] volume NaN → 0, int 변환
    - [ ] ingested_at = UTC now
  - [ ] `get_all_asset_ids()` 헬퍼
  - [ ] `get_symbol_info(asset_id)` 헬퍼
- [ ] FDR timeout 설정 반영 (settings.fdr_timeout)
- [ ] 로깅: fetch 시작/완료/실패 로그

---

## Task 1.7: `collector/validators.py` — 정합성 검증 `[M]`
- **Dependencies**: 1.1
- **Commit**: `[phase1-skeleton] Step 1.7: OHLCV 정합성 검증 (validators.py)`

### Checklist
- [ ] `collector/validators.py` 생성
  - [ ] `ValidationResult` dataclass 정의
    - [ ] is_valid: bool
    - [ ] errors: list[str]
    - [ ] warnings: list[str]
    - [ ] row_count: int
    - [ ] error_row_count: int
  - [ ] `validate_ohlcv(df)` 함수
    - [ ] 빈 DataFrame 검사
    - [ ] 필수 컬럼 존재 검사 (asset_id, date, open, high, low, close, volume)
    - [ ] 고가/저가 역전 검사 (high < low)
    - [ ] 음수 가격 검사 (open/high/low/close < 0)
    - [ ] 중복 키 검사 (asset_id + date)
    - [ ] 음수 거래량 검사 (volume < 0)
    - [ ] volume=0 경고 (WARNING, 저장 허용)
  - [ ] 반환: ValidationResult
- [ ] 순수 함수 (DB 의존 없음)
- [ ] 에러 메시지 포맷: `"{check_name}:{affected_rows}rows"`

---

## Task 1.8: `collector/ingest.py` — 수집 오케스트레이션 `[L]`
- **Dependencies**: 1.3, 1.6, 1.7
- **Commit**: `[phase1-skeleton] Step 1.8: 수집 오케스트레이션 (ingest.py)`

### Checklist
- [ ] `collector/ingest.py` 생성
  - [ ] `IngestResult` dataclass 정의
    - [ ] asset_id: str
    - [ ] status: str ("success" | "validation_failed" | "fetch_failed")
    - [ ] row_count: int
    - [ ] errors: list[str]
    - [ ] elapsed_ms: float
  - [ ] `ingest_asset(asset_id, start, end, session)` 함수
    - [ ] fetch_ohlcv 호출
    - [ ] validate_ohlcv 호출
    - [ ] 검증 통과 시 DB bulk insert
    - [ ] 검증 실패 시 저장 차단 + 결과 반환
    - [ ] fetch 실패 시 에러 처리 + 결과 반환
    - [ ] 경과 시간 측정
  - [ ] `ingest_all(start, end, session)` 함수
    - [ ] 활성 자산 목록 조회 (asset_master.is_active=True)
    - [ ] 각 자산 ingest_asset 실행
    - [ ] 한 자산 실패 시 다른 자산 계속 진행
    - [ ] 전체 결과 집계 반환
  - [ ] `_bulk_insert(session, df)` 내부 함수
    - [ ] DataFrame → dict 리스트 변환
    - [ ] session.bulk_insert_mappings 또는 session.execute(insert)
    - [ ] commit
- [ ] 자산 단위 독립 실행 보장
- [ ] 로깅: 자산별 시작/완료/에러

---

## Task 1.9: 단위 테스트 `[M]`
- **Dependencies**: 1.6, 1.7, 1.8
- **Commit**: `[phase1-skeleton] Step 1.9: 단위 테스트`

### Checklist
- [ ] `tests/conftest.py` — 공통 fixture
  - [ ] `sample_ohlcv_df` — 정상 OHLCV DataFrame
  - [ ] `invalid_ohlcv_df_inversion` — 고가/저가 역전
  - [ ] `invalid_ohlcv_df_negative` — 음수 가격
  - [ ] `empty_ohlcv_df` — 빈 DataFrame
  - [ ] `mock_session` — DB mock (SQLite in-memory 또는 MagicMock)
- [ ] `tests/unit/test_fdr_client.py`
  - [ ] test_symbol_map_completeness — 7개 자산 존재
  - [ ] test_symbol_map_fdr_symbol — FDR 심볼 형식 검증
  - [ ] test_fetch_ohlcv_columns — 반환 컬럼 검증 (mock FDR)
  - [ ] test_fetch_ohlcv_standardization — 소문자, asset_id, source 추가 검증
  - [ ] test_fetch_ohlcv_btc_fallback — BTC/KRW → BTC/USD fallback
  - [ ] test_fetch_ohlcv_empty_raises — 빈 결과 에러
  - [ ] test_fetch_ohlcv_retry — 재시도 로직 (실패 후 성공)
- [ ] `tests/unit/test_validators.py`
  - [ ] test_valid_data_passes — 정상 데이터 is_valid=True
  - [ ] test_high_low_inversion — 고가 < 저가 탐지
  - [ ] test_negative_price — 음수 가격 탐지
  - [ ] test_duplicate_key — 중복 키 탐지
  - [ ] test_empty_dataframe — 빈 DataFrame 탐지
  - [ ] test_missing_columns — 필수 컬럼 누락 탐지
  - [ ] test_zero_volume_warning — volume=0 경고
  - [ ] test_negative_volume — 음수 거래량 탐지
- [ ] `tests/unit/test_ingest.py`
  - [ ] test_ingest_asset_success — 정상 수집
  - [ ] test_ingest_asset_validation_failure — 검증 실패 시 미저장
  - [ ] test_ingest_asset_fetch_failure — FDR 실패 처리
  - [ ] test_ingest_all_partial_failure — 부분 실패 허용
- [ ] `python -m pytest tests/unit/ -v` 전체 통과
- [ ] `ruff check .` 통과

---

## 실행 순서 (권장)

```
[DB 불필요 그룹]
1.1 (pyproject.toml)
 ↓
1.2 + 1.3 + 1.6 + 1.7 (병렬)
 ↓
1.8 (ingest — 1.3, 1.6, 1.7 의존)
 ↓
1.9 (tests — 1.6, 1.7, 1.8 의존)

[DB 필수 그룹 — DATABASE_URL 설정 후]
1.4 (Alembic — 1.2, 1.3 의존)
 ↓
1.5 (seed — 1.4 의존)
```

## Progress Tracker

| Task | Size | Status | Commit |
|------|------|--------|--------|
| 1.1 pyproject.toml | S | [ ] Pending | |
| 1.2 .env + settings | S | [ ] Pending | |
| 1.3 DB models | M | [ ] Pending | |
| 1.4 Alembic | M | [ ] Blocked (DB) | |
| 1.5 seed | S | [ ] Blocked (1.4) | |
| 1.6 FDR client | M | [ ] Pending | |
| 1.7 validators | M | [ ] Pending | |
| 1.8 ingest | L | [ ] Pending | |
| 1.9 tests | M | [ ] Pending | |

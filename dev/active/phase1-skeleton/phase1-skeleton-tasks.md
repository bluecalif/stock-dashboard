# Phase 1 Tasks
> Last Updated: 2026-02-10
> Status: In Progress (DB 불필요 그룹 완료)

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
- [x] `pyproject.toml` 생성 (PEP 621)
  - [x] project metadata (name, version, requires-python)
  - [x] dependencies (core 11개)
  - [x] optional-dependencies.dev (4개)
  - [x] [tool.ruff] 설정
  - [x] [tool.pytest.ini_options] 설정
- [x] 패키지 `__init__.py` 생성
  - [x] `collector/__init__.py`
  - [x] `research_engine/__init__.py`
  - [x] `api/__init__.py`
  - [x] `db/__init__.py`
  - [x] `config/__init__.py`
  - [x] `tests/__init__.py`
  - [x] `tests/unit/__init__.py`
- [x] `pip install -e ".[dev]"` 성공
- [x] `ruff check .` 통과
- [x] `python -c "import collector; import db; import config"` 성공

---

## Task 1.2: `.env.example` + 환경 설정 `[S]`
- **Dependencies**: 1.1
- **Commit**: `[phase1-skeleton] Step 1.2: .env.example + Pydantic Settings`

### Checklist
- [x] `.env.example` 생성
  - [x] DATABASE_URL
  - [x] FDR_TIMEOUT
  - [x] LOG_LEVEL
  - [x] ALERT_WEBHOOK_URL
  - [x] PYTHONUTF8
- [x] `config/settings.py` 생성
  - [x] Settings 클래스 (BaseSettings 상속)
  - [x] 모든 필드 기본값 설정 (DATABASE_URL="" 포함)
  - [x] model_config env_file 설정
  - [x] settings 싱글턴 인스턴스
- [x] `.gitignore`에 `.env` 이미 포함 확인
- [x] `from config.settings import settings` import 성공
- [x] DATABASE_URL 빈 값에서도 import 에러 없음

---

## Task 1.3: `db/models.py` — SQLAlchemy 모델 `[M]`
- **Dependencies**: 1.1
- **Commit**: `[phase1-skeleton] Step 1.3: SQLAlchemy 모델 8개 테이블`

### Checklist
- [x] `db/models.py` 생성 — 8개 모델 클래스
  - [x] `AssetMaster` (asset_id PK, name, category, source_priority JSON, is_active)
  - [x] `PriceDaily` (composite PK: asset_id+date+source, OHLCV, ingested_at)
  - [x] `FactorDaily` (composite PK: asset_id+date+factor_name+version, value)
  - [x] `SignalDaily` (auto PK, asset_id, date, strategy_id, signal, score, action, meta_json)
  - [x] `BacktestRun` (UUID PK, strategy_id, config_json, started_at, ended_at, status)
  - [x] `BacktestEquityCurve` (composite PK: run_id+date, equity, drawdown)
  - [x] `BacktestTradeLog` (auto PK, run_id, asset_id, entry/exit_date, side, pnl, cost)
  - [x] `JobRun` (UUID PK, job_name, started_at, ended_at, status, error_message)
- [x] `DeclarativeBase` 설정 (SQLAlchemy 2.x)
- [x] 인덱스 정의
  - [x] price_daily: (asset_id, date DESC), (date)
  - [x] factor_daily: (asset_id, date DESC)
  - [x] signal_daily: (asset_id, date, strategy_id)
- [x] `db/session.py` 생성
  - [x] engine 생성 (DATABASE_URL 빈 값이면 None)
  - [x] SessionLocal 팩토리
- [x] DB 연결 없이 모델 import 성공 확인

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
- [x] `collector/fdr_client.py` 생성
  - [x] SYMBOL_MAP 정의 (7개 자산)
    - [x] KS200, 005930, 000660, SOXL, BTC, GC=F, SI=F
    - [x] BTC: fdr_symbol="BTC/KRW", fallback="BTC/USD"
  - [x] `fetch_ohlcv(asset_id, start, end)` 함수
    - [x] SYMBOL_MAP에서 FDR 심볼 조회
    - [x] `fdr.DataReader(symbol, start, end)` 호출
    - [x] 기본 재시도 (max_retries=3, 지수 백오프)
    - [x] BTC: BTC/KRW 실패 시 BTC/USD fallback
    - [x] 빈 결과 시 ValueError raise
    - [x] DataFrame 표준화
  - [x] `_standardize(df, asset_id)` 내부 함수
    - [x] 컬럼명 소문자 변환
    - [x] Date 인덱스 → date 컬럼
    - [x] asset_id, source="fdr" 추가
    - [x] volume NaN → 0, int 변환
    - [x] ingested_at = UTC now
- [x] 로깅: fetch 시작/완료/실패 로그

---

## Task 1.7: `collector/validators.py` — 정합성 검증 `[M]`
- **Dependencies**: 1.1
- **Commit**: `[phase1-skeleton] Step 1.7: OHLCV 정합성 검증 (validators.py)`

### Checklist
- [x] `collector/validators.py` 생성
  - [x] `ValidationResult` dataclass 정의
    - [x] is_valid: bool
    - [x] errors: list[str]
    - [x] warnings: list[str]
    - [x] row_count: int
    - [x] error_row_count: int
  - [x] `validate_ohlcv(df)` 함수
    - [x] 빈 DataFrame 검사
    - [x] 필수 컬럼 존재 검사 (asset_id, date, open, high, low, close, volume)
    - [x] 고가/저가 역전 검사 (high < low)
    - [x] 음수 가격 검사 (open/high/low/close < 0)
    - [x] 중복 키 검사 (asset_id + date)
    - [x] 음수 거래량 검사 (volume < 0)
    - [x] volume=0 경고 (WARNING, 저장 허용)
  - [x] 반환: ValidationResult
- [x] 순수 함수 (DB 의존 없음)
- [x] 에러 메시지 포맷: `"{check_name}:{affected_rows}rows"`

---

## Task 1.8: `collector/ingest.py` — 수집 오케스트레이션 `[L]`
- **Dependencies**: 1.3, 1.6, 1.7
- **Commit**: `[phase1-skeleton] Step 1.8: 수집 오케스트레이션 (ingest.py)`

### Checklist
- [x] `collector/ingest.py` 생성
  - [x] `IngestResult` dataclass 정의
    - [x] asset_id: str
    - [x] status: str ("success" | "validation_failed" | "fetch_failed")
    - [x] row_count: int
    - [x] errors: list[str]
    - [x] elapsed_ms: float
  - [x] `ingest_asset(asset_id, start, end, session)` 함수
    - [x] fetch_ohlcv 호출
    - [x] validate_ohlcv 호출
    - [x] 검증 통과 시 DB bulk insert
    - [x] 검증 실패 시 저장 차단 + 결과 반환
    - [x] fetch 실패 시 에러 처리 + 결과 반환
    - [x] 경과 시간 측정
  - [x] `ingest_all(start, end, session)` 함수
    - [x] 활성 자산 목록 조회 (asset_master.is_active=True)
    - [x] 각 자산 ingest_asset 실행
    - [x] 한 자산 실패 시 다른 자산 계속 진행
    - [x] 전체 결과 집계 반환
  - [x] `_bulk_insert(session, df)` 내부 함수
    - [x] DataFrame → PriceDaily 모델 변환 + session.add
    - [x] flush + commit
- [x] 자산 단위 독립 실행 보장
- [x] 로깅: 자산별 시작/완료/에러

---

## Task 1.9: 단위 테스트 `[M]`
- **Dependencies**: 1.6, 1.7, 1.8
- **Commit**: `[phase1-skeleton] Step 1.9: 단위 테스트`

### Checklist
- [x] `tests/conftest.py` — 공통 fixture
  - [x] `sample_ohlcv_df` — 정상 OHLCV DataFrame
  - [x] `invalid_ohlcv_high_low` — 고가/저가 역전
  - [x] `invalid_ohlcv_negative` — 음수 가격
  - [x] `mock_fdr_dataframe` — FDR 원본 형식 DataFrame
- [x] `tests/unit/test_fdr_client.py` (11개 테스트)
  - [x] test_symbol_map_completeness — 7개 자산 존재
  - [x] test_symbol_map_fdr_symbol — FDR 심볼 형식 검증
  - [x] test_btc_has_fallback — BTC fallback 존재
  - [x] test_columns — 표준화 컬럼 검증
  - [x] test_asset_id_added — asset_id 컬럼 추가
  - [x] test_source_is_fdr — source="fdr" 확인
  - [x] test_volume_int — volume 정수형 확인
  - [x] test_fetch_ohlcv_columns — 반환 컬럼 검증 (mock FDR)
  - [x] test_fetch_ohlcv_unknown_asset — 미등록 자산 에러
  - [x] test_fetch_ohlcv_empty_raises — 빈 결과 에러
  - [x] test_fetch_ohlcv_btc_fallback — BTC/KRW → BTC/USD fallback
- [x] `tests/unit/test_validators.py` (9개 테스트)
  - [x] test_valid_data_passes — 정상 데이터 is_valid=True
  - [x] test_high_low_inversion — 고가 < 저가 탐지
  - [x] test_negative_price — 음수 가격 탐지
  - [x] test_duplicate_key — 중복 키 탐지
  - [x] test_empty_dataframe — 빈 DataFrame 탐지
  - [x] test_none_dataframe — None 입력 처리
  - [x] test_missing_columns — 필수 컬럼 누락 탐지
  - [x] test_zero_volume_warning — volume=0 경고
  - [x] test_negative_volume — 음수 거래량 탐지
- [x] `tests/unit/test_ingest.py` (5개 테스트)
  - [x] test_ingest_asset_success — 정상 수집
  - [x] test_ingest_asset_validation_failure — 검증 실패 시 미저장
  - [x] test_ingest_asset_fetch_failure — FDR 실패 처리
  - [x] test_ingest_all_partial_failure — 부분 실패 허용
  - [x] test_ingest_all_returns_all_assets — 7개 자산 전체 시도
- [x] `python -m pytest tests/unit/ -v` 전체 통과 (25 passed)
- [x] `ruff check .` 통과

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
| 1.1 pyproject.toml | S | [x] Done | `ebfd75c` (이전 세션) |
| 1.2 .env + settings | S | [x] Done | 본 커밋 포함 |
| 1.3 DB models | M | [x] Done | 본 커밋 포함 |
| 1.4 Alembic | M | [ ] Blocked (DB) | |
| 1.5 seed | S | [ ] Blocked (1.4) | |
| 1.6 FDR client | M | [x] Done | 본 커밋 포함 |
| 1.7 validators | M | [x] Done | 본 커밋 포함 |
| 1.8 ingest | L | [x] Done | 본 커밋 포함 |
| 1.9 tests | M | [x] Done | 25 passed |

# Phase 1 Context
> Last Updated: 2026-02-10
> Status: In Progress (Steps 1.1~1.9 완료, 1.4/1.5 DB 대기)

## 핵심 파일

### 참조 문서 (기존)
| 파일 | 용도 | 참조 태스크 |
|------|------|-----------|
| `docs/masterplan-v0.md` | 전체 설계 명세 (스키마, API, 마일스톤) | 전체 |
| `docs/session-compact.md` | 현재 진행 상태 | 전체 |
| `docs/data-accessibility-report.md` | FDR 접근성 검증 결과 | 1.6 |
| `docs/guide_financereader.md` | FDR 사용법 + 7종목 심볼 | 1.6 |
| `CLAUDE.md` | 프로젝트 규칙, 기술 스택 | 전체 |
| `.claude/skills/backend-dev/SKILL.md` | 백엔드 패턴 가이드 | 1.3, 1.6, 1.7, 1.8 |

### 생성 파일 (Phase 1)
| 파일 | 용도 | 태스크 |
|------|------|-------|
| `pyproject.toml` | Python 프로젝트 메타 + 의존성 + 도구 | 1.1 |
| `.env.example` | 환경변수 템플릿 | 1.2 |
| `config/settings.py` | Pydantic Settings | 1.2 |
| `db/models.py` | SQLAlchemy 모델 8개 테이블 | 1.3 |
| `db/session.py` | DB 엔진 + 세션 팩토리 | 1.3 |
| `alembic.ini` | Alembic 설정 | 1.4 |
| `db/alembic/env.py` | Alembic 환경 설정 | 1.4 |
| `scripts/seed_assets.py` | asset_master 시드 | 1.5 |
| `collector/fdr_client.py` | FDR 래퍼 | 1.6 |
| `collector/validators.py` | OHLCV 정합성 검증 | 1.7 |
| `collector/ingest.py` | 수집 오케스트레이션 | 1.8 |
| `tests/unit/test_fdr_client.py` | FDR 래퍼 테스트 | 1.9 |
| `tests/unit/test_validators.py` | 정합성 검증 테스트 | 1.9 |
| `tests/unit/test_ingest.py` | 수집 오케스트레이션 테스트 | 1.9 |
| `tests/conftest.py` | 공통 test fixture | 1.9 |

## 주요 결정사항 (Phase 1)

| 결정 | 선택 | 근거 |
|------|------|------|
| Python 패키징 | `pyproject.toml` (PEP 621) | 표준, pip editable install 지원 |
| 설정 관리 | Pydantic Settings | 타입 안전, .env 자동 로드, 검증 |
| ORM | SQLAlchemy 2.x (Mapped Column) | FastAPI 생태계 표준, Alembic 호환 |
| DB 세션 | 동기 방식 (sync) | collector는 배치 작업, async 불필요 |
| 마이그레이션 | Alembic autogenerate | 모델 기반 자동 생성 |
| FDR 래퍼 | 동기 함수 + 기본 재시도 | FDR은 sync 라이브러리, Phase 2에서 강화 |
| 테스트 DB | SQLite in-memory / mock | 외부 DB 의존 없는 유닛 테스트 |
| bulk insert | Phase 1 단순 INSERT | UPSERT는 Phase 2 (Task 2.2) |
| BTC asset_id | `"BTC"` (FDR 심볼은 `BTC/KRW`) | asset_id에 `/` 포함 시 URL 문제 |

## 자산 매핑 (7개)

| asset_id | name | category | FDR symbol | fallback |
|----------|------|----------|------------|----------|
| KS200 | KOSPI200 | index | KS200 | - |
| 005930 | 삼성전자 | stock | 005930 | hantoo (v0.9+) |
| 000660 | SK하이닉스 | stock | 000660 | hantoo (v0.9+) |
| SOXL | SOXL ETF | etf | SOXL | - |
| BTC | Bitcoin | crypto | BTC/KRW | BTC/USD |
| GC=F | Gold Futures | commodity | GC=F | - |
| SI=F | Silver Futures | commodity | SI=F | - |

## DB 스키마 요약

### 복합 Primary Key
| 테이블 | PK |
|--------|-----|
| asset_master | (asset_id) |
| price_daily | (asset_id, date, source) |
| factor_daily | (asset_id, date, factor_name, version) |
| backtest_equity_curve | (run_id, date) |

### Foreign Key 관계
```
asset_master.asset_id ←── price_daily.asset_id
asset_master.asset_id ←── factor_daily.asset_id
asset_master.asset_id ←── signal_daily.asset_id
asset_master.asset_id ←── backtest_trade_log.asset_id
backtest_run.run_id   ←── backtest_equity_curve.run_id
backtest_run.run_id   ←── backtest_trade_log.run_id
```

### 인덱스
| 테이블 | 인덱스 |
|--------|--------|
| price_daily | (asset_id, date DESC), (date) |
| factor_daily | (asset_id, date DESC) |
| signal_daily | (asset_id, date, strategy_id) |

## FDR DataFrame 표준화 규칙

```
FDR 반환:                      →  표준화 후:
─────────────────────────         ─────────────────────────────────────
Date(index) Open High Low Close Volume   asset_id date open high low close volume source ingested_at
2026-01-02  100  105  98  103  50000     KS200    2026-01-02 100 105 98 103 50000 fdr    2026-02-10T...
```

변환 규칙:
1. 컬럼명 소문자 변환: `Open→open`, `High→high`, `Low→low`, `Close→close`, `Volume→volume`
2. 인덱스 → `date` 컬럼: `df.index.name = None; df.reset_index(); df.rename(columns={"Date": "date"})`
3. `asset_id` 컬럼 추가
4. `source = "fdr"` 컬럼 추가
5. `volume` NaN → 0, int 변환
6. `ingested_at` = `datetime.now(timezone.utc)`

## 정합성 검증 규칙

| 검증 | 조건 | 레벨 | 처리 |
|------|------|------|------|
| 고가/저가 역전 | `high < low` | ERROR | 저장 차단 |
| 음수 가격 | `open/high/low/close < 0` | ERROR | 저장 차단 |
| 중복 키 | `(asset_id, date)` 중복 | ERROR | 저장 차단 |
| 필수 컬럼 누락 | 7개 중 누락 | ERROR | 저장 차단 |
| 빈 DataFrame | `len(df) == 0` | ERROR | 저장 차단 |
| 음수 거래량 | `volume < 0` | ERROR | 저장 차단 |
| 거래량 0 | `volume == 0` | WARNING | 로깅만, 저장 허용 |

## 인코딩 컨벤션

| Context | Rule |
|---------|------|
| CSV/File read | `encoding='utf-8-sig'` (BOM 처리) |
| File write | `encoding='utf-8'` 명시 |
| Python stdout | `PYTHONUTF8=1` 환경변수 |
| HTTP JSON | `.json()` 자동 UTF-8 |
| DB 저장 | PostgreSQL UTF-8 기본 |

## 의존성 버전 참조

### Python (pyproject.toml)
- **Core**: `financedatareader`, `sqlalchemy[asyncio]>=2.0`, `psycopg2-binary`, `fastapi>=0.100`, `uvicorn[standard]`, `pydantic>=2.0`, `pydantic-settings`, `alembic`, `pandas>=2.0`, `numpy`, `python-dotenv`
- **Dev**: `pytest>=7.0`, `pytest-asyncio`, `httpx`, `ruff`

### 시스템 요구사항
- Python 3.11+
- PostgreSQL 15+ (Railway)
- Git

## Phase 2 연계 포인트

Phase 1 완료 후 Phase 2에서 강화할 영역:
| Phase 1 | Phase 2 강화 |
|---------|-------------|
| 기본 재시도 (3회) | 지수 백오프 재시도 고도화 (Task 2.1) |
| 단순 INSERT | idempotent UPSERT (Task 2.2) |
| 자산별 독립 실행 | 부분 실패 허용 + job_run 기록 (Task 2.3) |
| 기본 검증 6항목 | 정합성 검증 강화 (Task 2.4) |
| 단기 데이터 테스트 | 3년 백필 실행 + 검증 (Task 2.5) |

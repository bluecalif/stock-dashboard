# Session Compact

> Generated: 2026-02-10
> Source: Conversation compaction via /compact-and-go

## Goal
Phase 1 구현 시작: Task 1.1~1.9 (프로젝트 골격 + DB + Collector)

## Completed
- [x] 미커밋 변경사항 커밋 → `ebfd75c` [phase1-skeleton] Phase 1 dev-docs 생성 + DATABASE_URL 의존성 재배치
- [x] **backend/frontend 폴더 분리 결정** — 루트에서 `backend/` + `frontend/` 구조로 전환
- [x] **Task 1.1: pyproject.toml + 패키지 골격** 완료
  - `backend/pyproject.toml` 생성 (PEP 621, build-backend=setuptools.build_meta)
  - 패키지 `__init__.py` 7개 생성 (collector, research_engine, api, db, config, tests, tests/unit)
  - `backend/.venv` 생성 + `pip install -e ".[dev]"` 성공
  - `ruff check .` 통과, 패키지 import 검증 통과
  - `.gitignore` 수정 (dashboard/dist/ → frontend/dist/)
  - `CLAUDE.md` 업데이트 (monorepo 구조, commands, frontend 명칭)

## Current State
**Phase 1 구현 중. Task 1.1 완료, Task 1.2부터 진행 대기.**

### Git
- Repo: `https://github.com/bluecalif/stock-dashboard.git`
- Branch: `master`
- Last commit: `ebfd75c` [phase1-skeleton] Phase 1 dev-docs 생성 + DATABASE_URL 의존성 재배치
- Uncommitted (Task 1.1 결과물 — 아직 미커밋):
  - `backend/pyproject.toml` (신규)
  - `backend/collector/__init__.py` (신규)
  - `backend/research_engine/__init__.py` (신규)
  - `backend/api/__init__.py` (신규)
  - `backend/db/__init__.py` (신규)
  - `backend/config/__init__.py` (신규)
  - `backend/tests/__init__.py` (신규)
  - `backend/tests/unit/__init__.py` (신규)
  - `frontend/` (빈 디렉토리 — git에 안 잡힘)
  - `.gitignore` (수정)
  - `CLAUDE.md` (수정)
- Remote: 2 commits ahead of origin/master

### 프로젝트 구조 (변경됨)
```
stock-dashboard/
├── CLAUDE.md, AGENTS.md, docs/, dev/   ← 프로젝트 레벨
├── backend/                            ← Python 백엔드
│   ├── pyproject.toml
│   ├── .venv/                          ← 가상환경 (gitignored)
│   ├── collector/__init__.py
│   ├── research_engine/__init__.py
│   ├── api/__init__.py
│   ├── db/__init__.py
│   ├── config/__init__.py
│   ├── tests/__init__.py
│   └── tests/unit/__init__.py
└── frontend/                           ← React/Vite (비어있음, Phase 4)
```

### Phase 1 의존성 그래프 (업데이트)
```
[완료]
✅ 1.1 (pyproject.toml)

[즉시 시작 가능 — 1.1 완료됨]
→ 1.2 (.env + settings)
→ 1.3 (DB models)
→ 1.6 (FDR client)
→ 1.7 (validators)

[의존성 대기]
1.8 (ingest — 1.3, 1.6, 1.7 완료 후)
1.9 (tests — 1.6, 1.7, 1.8 완료 후)

[DB 필수 — DATABASE_URL 설정 후]
1.4 (Alembic — 1.2, 1.3) → 1.5 (seed)
```

### pyproject.toml 패키지명 주의
- PyPI 패키지명: `finance-datareader` (하이픈 포함, `financedatareader` 아님)
- import명: `import FinanceDataReader`

## Remaining / TODO
- [ ] Task 1.2: `.env.example` + `config/settings.py` (Pydantic Settings)
- [ ] Task 1.3: `db/models.py` (8개 테이블 SQLAlchemy ORM) + `db/session.py`
- [ ] Task 1.6: `collector/fdr_client.py` (SYMBOL_MAP, fetch_ohlcv, 재시도, BTC fallback)
- [ ] Task 1.7: `collector/validators.py` (ValidationResult, validate_ohlcv)
- [ ] Task 1.8: `collector/ingest.py` (IngestResult, ingest_asset, ingest_all)
- [ ] Task 1.9: `tests/` (conftest, test_fdr_client, test_validators, test_ingest)
- [ ] Task 1.1 결과 + 1.2~1.7 결과 커밋
- [ ] Task 1.4/1.5: DATABASE_URL 설정 후

## Key Decisions
- **backend/frontend 폴더 분리 (2026-02-10)**: 루트 monorepo에서 `backend/` + `frontend/` 2-폴더 구조로 전환. 모든 Python 코드는 `backend/` 하위에 위치
- **pyproject.toml**: PEP 621, `setuptools.build_meta` 백엔드 사용 (`.backends._legacy` 아님)
- **finance-datareader**: PyPI 패키지명 `finance-datareader` (하이픈), import는 `FinanceDataReader`
- **Task 1.1 결과 미커밋 상태**: 1.2~1.7 완료 후 함께 커밋 예정

## Context
다음 세션에서는 답변에 한국어를 사용하세요.
- **작업 디렉토리**: `backend/` 내에서 Python 작업 수행
- **venv 활성화**: `backend/.venv/Scripts/activate` (Windows)
- **pip 실행**: `backend/.venv/Scripts/pip` 또는 활성화 후 `pip`
- **dev-docs 위치**:
  - 프로젝트 전체: `dev/active/project-overall/` (plan, context, tasks)
  - Phase 1 상세: `dev/active/phase1-skeleton/` (plan, context, tasks) — **파일 경로가 `backend/` 기준으로 아직 미업데이트**
- **Phase 1 plan 파일**: `dev/active/phase1-skeleton/phase1-skeleton-plan.md` — Step별 상세 구현 명세 포함
- **Phase 1 context 파일**: `dev/active/phase1-skeleton/phase1-skeleton-context.md` — DB 스키마, FDR 표준화 규칙, 검증 규칙 참조
- Git remote: `https://github.com/bluecalif/stock-dashboard.git` (master)
- DB 연결은 `DATABASE_URL` 환경변수 설정 후 재검증 필요 (Task 1.4 전)

## Next Action
1. Task 1.2 구현: `backend/.env.example` + `backend/config/settings.py`
2. Task 1.3 구현: `backend/db/models.py` + `backend/db/session.py`
3. Task 1.6 구현: `backend/collector/fdr_client.py`
4. Task 1.7 구현: `backend/collector/validators.py`
5. 1.2~1.7 완료 후 → Task 1.8 (ingest.py) → Task 1.9 (tests)
6. 전체 커밋

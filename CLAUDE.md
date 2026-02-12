# CLAUDE.md

> **Rule: This file must stay under 100 lines.** Move details to skills or `dev/` docs.

## Project Overview

Stock Dashboard — 7개 자산(KOSPI200, 삼성전자, SK하이닉스, SOXL, BTC, Gold, Silver)의 일봉 데이터 수집/저장/분석/시각화 MVP.
Docs: `docs/masterplan-v0.md` (설계), `docs/session-compact.md` (현재 상태).

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, PostgreSQL (Railway)
- **Data**: FinanceDataReader (FDR) — 전 자산 1순위. Hantoo fallback은 v0.9+에서 추가
- **Dashboard**: React, Recharts, Vite, TypeScript
- **Migration**: Alembic
- **Repo**: Monorepo — `backend/` (collector, research_engine, api, db, config) + `frontend/` (React)

## Common Commands

```bash
# Backend (run from /c/Projects-2026/stock-dashboard/backend)
# IMPORTANT: Windows backslash paths (C:\...) fail in Git Bash. Always use /c/... format.
cd /c/Projects-2026/stock-dashboard/backend
pip install -e ".[dev]"             # Install deps (first time)
python -m pytest                    # Run all tests
ruff check .                        # Lint
uvicorn api.main:app --reload       # Dev server
# /step-update after each step | /dev-docs to generate planning docs
```

## Architecture

```
scheduler → collector (FDR REST) → PostgreSQL → research_engine → API (FastAPI) → dashboard
```

Pydantic schemas for all I/O. FastAPI DI for services.

### Data System

**7 Assets**: KS200, 005930, 000660, SOXL, BTC/KRW, GC=F, SI=F
**Source**: FDR primary for all. Hantoo REST fallback for 005930/000660 at v0.9+.
**DB tables**: `asset_master`, `price_daily`, `factor_daily`, `signal_daily`, `backtest_run`, `backtest_equity_curve`, `backtest_trade_log`, `job_run`

### Core Modules

- **collector**: FDR 기반 일봉 수집, 정합성 검증, UPSERT
- **research_engine**: 팩터 생성, 전략 신호(모멘텀/추세/평균회귀), 백테스트
- **api**: FastAPI 조회 API (`/v1/prices`, `/v1/factors`, `/v1/signals`, `/v1/backtests`)
- **frontend**: React 시각화 (가격/수익률/상관/전략 성과)

## Encoding (Windows + Korean)

| Context | Rule |
|---------|------|
| CSV/File read | `encoding='utf-8-sig'` (BOM) |
| File write | `encoding='utf-8'` explicit |
| Python stdout | `PYTHONUTF8=1` env var |
| HTTP JSON | Automatic UTF-8 via `.json()` |

**Never rely on system default encoding.** Always specify explicitly.

## Skills System

Skills in `.claude/skills/` — see each `SKILL.md` for details:
`backend-dev`, `frontend-dev`

## Workflow Conventions

- **Dev docs**: `dev/active/[task]/` with `-plan.md`, `-context.md`, `-tasks.md`
- **Commits**: `[task-name] Step X.Y: description`
- **Branches**: `feature/[task-name]`
- **Convention checks**: OHLCV schema rules (data code), Router-Service-Repo separation (API code)

## Key Design Decisions

- Kiwoom OpenAPI dropped (2026-02-10): 32-bit Python, DLL lock issues
- FDR is sole data source for weeks 1-4
- Hantoo REST API integration deferred to week 5 (pre-deployment)

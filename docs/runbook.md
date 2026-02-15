# Stock Dashboard Runbook

> 운영 매뉴얼 - 배포, 모니터링, 장애 대응

## 1. Architecture

```
[Windows PC]                    [Cloud]
 ├── Task Scheduler             ├── Railway PostgreSQL (DB)
 │   └── daily_collect.bat      ├── Railway App (FastAPI API)
 │       ├── collect.py         │   └── /v1/* endpoints
 │       ├── healthcheck.py     └── Vercel (React SPA)
 │       └── run_research.py        └── → Railway API
 └── Local dev environment
```

## 2. Daily Pipeline

**Schedule**: 매일 18:00 KST (Windows Task Scheduler)
**Script**: `backend/scripts/daily_collect.bat`
**Pipeline**: collect (T-7~T) → healthcheck → research → log rotation

### Logs
- 경로: `logs/collect_YYYYMMDD.log`
- 자동 삭제: 30일 이상 된 로그

### 수동 실행
```bash
cd backend
.venv/Scripts/python scripts/collect.py --start 2026-02-01 --end 2026-02-15
.venv/Scripts/python scripts/healthcheck.py
.venv/Scripts/python scripts/run_research.py --start 2026-02-01 --end 2026-02-15
```

## 3. Deployment

### 3.1 Backend (Railway)

**Service**: Railway App (same project as PostgreSQL)
**Root directory**: `backend/`
**Start command**: `uvicorn api.main:app --host 0.0.0.0 --port $PORT`

**Environment Variables** (Railway dashboard):
| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | Railway PostgreSQL internal URL (auto-linked) |
| `CORS_ORIGINS` | Vercel frontend URL (e.g. `https://your-app.vercel.app`) |
| `LOG_LEVEL` | `INFO` (production) |
| `PYTHONUTF8` | `1` |

**Deploy 절차**:
1. `git push origin master`
2. Railway auto-deploy 트리거됨
3. `/health` endpoint로 헬스체크 확인
4. Railway dashboard에서 로그 확인

### 3.2 Frontend (Vercel)

**Framework**: Vite + React
**Build command**: `cd frontend && npm install && npm run build`
**Output**: `frontend/dist`

**Environment Variables** (Vercel dashboard):
| Variable | Description |
|----------|-------------|
| `VITE_API_BASE_URL` | Railway API URL (e.g. `https://your-api.railway.app`) |

**Deploy 절차**:
1. `git push origin master`
2. Vercel auto-deploy 트리거됨
3. Preview URL에서 확인 후 Production promote

### 3.3 CI/CD (GitHub Actions)

**Trigger**: push/PR to master
**Jobs**: pytest + ruff lint
**Config**: `.github/workflows/ci.yml`

## 4. Pre-deployment Check

배포 전 환경 검증:
```bash
cd backend
.venv/Scripts/python scripts/preflight.py
```

검증 항목:
- DATABASE_URL 설정
- DB 연결
- 8개 테이블 존재
- 7개 시드 자산 존재
- 최근 7일 내 가격 데이터

## 5. Troubleshooting

### DB 연결 실패
1. Railway dashboard에서 PostgreSQL 서비스 상태 확인
2. `DATABASE_URL` 환경변수 확인
3. `preflight.py` 실행하여 진단

### 데이터 수집 실패
1. `logs/collect_YYYYMMDD.log` 확인
2. FDR 서버 상태 확인 (네트워크/타임아웃)
3. 수동 재실행: `python scripts/collect.py --start ... --end ...`

### API 응답 없음
1. Railway dashboard에서 서비스 상태/로그 확인
2. `/health` endpoint 호출
3. Railway에서 서비스 재시작

### Frontend 빈 화면
1. 브라우저 개발자 도구 Console 확인
2. `VITE_API_BASE_URL` 환경변수 확인
3. API CORS 설정 확인 (`CORS_ORIGINS`)

## 6. Monitoring

| Item | Method | Frequency |
|------|--------|-----------|
| Data freshness | `healthcheck.py` (자동) | Daily 18:00 |
| API health | `/health` endpoint | On deploy |
| Test suite | GitHub Actions CI | On push/PR |
| Logs | `logs/` directory | As needed |

## 7. Key Assets (7)

| ID | Name | Category |
|----|------|----------|
| KS200 | KOSPI200 | index |
| 005930 | Samsung Electronics | stock |
| 000660 | SK Hynix | stock |
| SOXL | SOXL ETF | etf |
| BTC | Bitcoin | crypto |
| GC=F | Gold Futures | commodity |
| SI=F | Silver Futures | commodity |

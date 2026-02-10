# Project Overall Context
> Last Updated: 2026-02-10
> Status: Planning

## 핵심 파일

| 파일 | 용도 |
|------|------|
| `docs/masterplan-v0.md` | 프로젝트 설계 명세서 (아키텍처, DB 스키마, API, 마일스톤) |
| `docs/session-compact.md` | 현재 진행 상태 |
| `docs/data-accessibility-plan.md` | 데이터 접근성 검증 계획 |
| `docs/data-accessibility-report.md` | 데이터 접근성 검증 결과 (Conditional Go) |
| `CLAUDE.md` | 프로젝트 규칙, 기술 스택, 컨벤션 |
| `.claude/skills/backend-dev/SKILL.md` | 백엔드 개발 가이드 |
| `.claude/skills/frontend-dev/SKILL.md` | 프론트엔드 개발 가이드 |

## 주요 결정사항

| 일자 | 결정 | 근거 |
|------|------|------|
| 2026-02-10 | Kiwoom OpenAPI 폐기 | 32비트 Python 요구, DLL 잠금 이슈 |
| 2026-02-10 | FDR 단일 소스 (Week 1-4) | 전 자산 검증 통과, 통합 간편 |
| 2026-02-10 | Hantoo fallback 이연 (v0.9+) | 배포 직전 국내주식 이중화 |
| 2026-02-10 | Dashboard: React + Recharts + Vite + TS | 시각화 라이브러리 풍부, 타입 안전성 |
| 2026-02-10 | DB Migration: Alembic | SQLAlchemy 네이티브 통합 |
| 2026-02-10 | 알림: Discord Webhook | 무료, 설정 간편 |

## 데이터 접근성 검증 요약

- **Gate**: Conditional Go
- **FDR 7개 자산**: 전체 PASS (smoke, backfill, reliability, freshness)
- **DB 연결**: FAIL (`DATABASE_URL` 미설정) — Task 1.4(Alembic) 전까지 비차단
- **p95 응답시간**: 최대 1173ms (SI=F reliability)
- **실패율**: 0% (재시도 포함)
- **백필 결측률**: 최대 0.4% (GC=F, SI=F — 허용 범위)

## 자산 목록

| asset_id | 이름 | 카테고리 | FDR 심볼 |
|----------|------|----------|----------|
| KS200 | KOSPI200 | index | KS200 |
| 005930 | 삼성전자 | stock | 005930 |
| 000660 | SK하이닉스 | stock | 000660 |
| SOXL | SOXL ETF | etf | SOXL |
| BTC | Bitcoin | crypto | BTC/KRW |
| GC=F | Gold | commodity | GC=F |
| SI=F | Silver | commodity | SI=F |

## DB 테이블 목록

1. `asset_master` — 자산 마스터
2. `price_daily` — 일봉 PK: (asset_id, date, source)
3. `factor_daily` — 팩터 PK: (asset_id, date, factor_name, version)
4. `signal_daily` — 전략 신호
5. `backtest_run` — 백테스트 실행
6. `backtest_equity_curve` — 에쿼티 커브
7. `backtest_trade_log` — 트레이드 로그
8. `job_run` — 작업 실행 이력

## API 엔드포인트 (v1)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/v1/assets` | 자산 목록 |
| GET | `/v1/prices/daily` | 일봉 조회 |
| GET | `/v1/factors` | 팩터 조회 |
| GET | `/v1/signals` | 전략 신호 조회 |
| POST | `/v1/backtests/run` | 백테스트 실행 |
| GET | `/v1/backtests/{run_id}` | 백테스트 결과 |
| GET | `/v1/backtests/{run_id}/equity` | 에쿼티 커브 |
| GET | `/v1/backtests/{run_id}/trades` | 트레이드 로그 |
| GET | `/v1/health` | 헬스 체크 |

## 컨벤션 체크리스트

### 데이터 관련
- [ ] OHLCV 표준 스키마 준수 (asset_id, date, open, high, low, close, volume, source, ingested_at)
- [ ] FDR primary source 사용 (모든 자산)
- [ ] price_daily PK: (asset_id, date, source)

### API 관련
- [ ] Router → Service → Repository 레이어 분리
- [ ] Pydantic 스키마 정의
- [ ] 의존성 주입 패턴

### 수집 관련
- [ ] idempotent UPSERT
- [ ] 지수 백오프 재시도
- [ ] 정합성 검증 (고가/저가 역전, 음수 가격, 중복)

### 인코딩 관련
- [ ] CSV/File read: `encoding='utf-8-sig'`
- [ ] File write: `encoding='utf-8'` explicit
- [ ] `PYTHONUTF8=1` 환경변수

### 배포/운영 관련
- [ ] 환경변수 하드코딩 금지 (`.env` + Railway env vars)
- [ ] `.env` 파일 gitignore 확인
- [ ] CORS 화이트리스트 설정
- [ ] DB TLS 연결 강제
- [ ] GitHub Secrets로 시크릿 관리
- [ ] CI 파이프라인 필수 통과 (lint + test + build)
- [ ] 프로덕션 빌드 최적화 (코드 스플리팅, 에셋 해시)
- [ ] 프로세스 매니저로 API 서버 등록
- [ ] 배치 실패 시 Discord 알림 동작 확인
- [ ] DB 백업 + 복구 절차 검증
- [ ] Alembic downgrade 롤백 테스트

## 배포 인프라 결정 사항 (TBD)

| 항목 | 후보 | 상태 |
|------|------|------|
| 프론트엔드 호스팅 | Vercel / Netlify / Nginx (Windows) | 미결정 |
| 백엔드 프로세스 매니저 | NSSM / Windows Service | 미결정 |
| CI/CD | GitHub Actions | 확정 |
| DB 호스팅 | Railway PostgreSQL | 확정 |
| 알림 채널 | Discord Webhook | 확정 |

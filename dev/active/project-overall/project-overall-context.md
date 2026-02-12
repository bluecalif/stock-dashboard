# Project Overall Context
> Last Updated: 2026-02-12
> Status: In Progress (Phase 3 완료, Phase 4 Planning)

## 핵심 파일

| 파일 | 용도 |
|------|------|
| `docs/masterplan-v0.md` | 프로젝트 설계 명세서 (아키텍처, DB 스키마, API 12개, 프론트엔드 6페이지, Phase 1~6) |
| `docs/session-compact.md` | 현재 진행 상태 |
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
| 2026-02-12 | 상관행렬: API on-the-fly 계산 | 별도 DB 테이블 불필요, 7자산 데이터 소규모 |
| 2026-02-12 | Phase 구조 리비전 | 기존 Phase 4(백테스트+API+대시보드) → Phase 4(API), Phase 5(Frontend) 분리 |
| 2026-02-12 | API 12개 엔드포인트 | 기존 9개 + dashboard/summary, correlation, backtests list 추가 |
| 2026-02-12 | 프론트엔드 6개 페이지 | 기존 4개(가격/수익률/상관/전략) → 6개(홈/가격/상관/팩터/시그널/전략) 확대 |

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

## DB 테이블 목록 (8개, 모두 생성 완료)

1. `asset_master` — 자산 마스터 (7개 자산 시드 완료)
2. `price_daily` — 일봉 PK: (asset_id, date, source) — 5,559 rows
3. `factor_daily` — 팩터 PK: (asset_id, date, factor_name, version)
4. `signal_daily` — 전략 신호 (id PK, ix: asset_id+date+strategy_id)
5. `backtest_run` — 백테스트 실행 (run_id UUID PK)
6. `backtest_equity_curve` — 에쿼티 커브 (run_id+date PK)
7. `backtest_trade_log` — 트레이드 로그 (id PK)
8. `job_run` — 작업 실행 이력 (job_id UUID PK)

## API 엔드포인트 (v1) — 12개

### 조회 API (5개)
| Method | Path | 설명 |
|--------|------|------|
| GET | `/v1/health` | 헬스체크 (DB 연결 상태) |
| GET | `/v1/assets` | 자산 목록 (asset_master) |
| GET | `/v1/prices/daily?asset_id=&from=&to=` | 가격 조회 (pagination) |
| GET | `/v1/factors?asset_id=&factor_name=&from=&to=` | 팩터 조회 |
| GET | `/v1/signals?asset_id=&strategy_id=&from=&to=` | 시그널 조회 |

### 백테스트 API (4개 + 1 POST)
| Method | Path | 설명 |
|--------|------|------|
| POST | `/v1/backtests/run` | 온디맨드 백테스트 실행 |
| GET | `/v1/backtests` | 백테스트 실행 목록 |
| GET | `/v1/backtests/{run_id}` | 백테스트 요약 (metrics 포함) |
| GET | `/v1/backtests/{run_id}/equity` | 에쿼티 커브 |
| GET | `/v1/backtests/{run_id}/trades` | 거래 이력 |

### 집계/분석 API (2개)
| Method | Path | 설명 |
|--------|------|------|
| GET | `/v1/dashboard/summary` | 대시보드 요약 (최신가격/시그널/성과) |
| GET | `/v1/correlation?asset_ids=&from=&to=&window=` | 자산 간 상관행렬 (on-the-fly) |

## 프론트엔드 페이지 (6개)

| # | 페이지 | 주요 API 소비 | 차트 종류 |
|---|--------|-------------|----------|
| 1 | 대시보드 홈 | `/dashboard/summary` | 요약 카드 + 미니 라인 |
| 2 | 가격/수익률 | `/prices/daily` | 라인/캔들 + 정규화 비교 |
| 3 | 상관 히트맵 | `/correlation` | 히트맵 (Recharts) |
| 4 | 팩터 현황 | `/factors` | RSI/MACD 서브차트 |
| 5 | 시그널 타임라인 | `/signals` + `/prices/daily` | 가격 + 매매 마커 |
| 6 | 전략 성과 | `/backtests/*` | 에쿼티 커브 + 메트릭스 |

## 컨벤션 체크리스트

### 데이터 관련
- [x] OHLCV 표준 스키마 준수 (asset_id, date, open, high, low, close, volume, source, ingested_at)
- [x] FDR primary source 사용 (모든 자산)
- [x] price_daily PK: (asset_id, date, source)
- [x] idempotent UPSERT (collector + factor_store)
- [x] 지수 백오프 재시도 (fdr_client)
- [x] 정합성 검증 (고가/저가 역전, 음수 가격, 중복)

### API 관련
- [ ] Router → Service → Repository 레이어 분리
- [ ] Pydantic 스키마 정의
- [ ] 의존성 주입 패턴
- [ ] CORS 설정
- [ ] Pagination (limit/offset)

### 인코딩 관련
- [x] CSV/File read: `encoding='utf-8-sig'`
- [x] File write: `encoding='utf-8'` explicit
- [x] `PYTHONUTF8=1` 환경변수

### 배포/운영 관련
- [x] 환경변수 하드코딩 금지 (`.env` + Pydantic Settings)
- [x] `.env` 파일 gitignore 확인
- [ ] CORS 화이트리스트 설정
- [ ] DB TLS 연결 강제
- [ ] GitHub Secrets로 시크릿 관리
- [ ] CI 파이프라인 (lint + test + build)
- [ ] 프로덕션 빌드 최적화
- [ ] 배치 실패 시 Discord 알림 동작 확인
- [ ] DB 백업 + 복구 절차 검증

## 배포 인프라 결정 사항

| 항목 | 후보 | 상태 |
|------|------|------|
| 프론트엔드 호스팅 | Vercel / Netlify / Nginx (Windows) | 미결정 |
| 백엔드 프로세스 매니저 | NSSM / Windows Service | 미결정 |
| CI/CD | GitHub Actions | 확정 |
| DB 호스팅 | Railway PostgreSQL | 확정 |
| 알림 채널 | Discord Webhook | 확정 |

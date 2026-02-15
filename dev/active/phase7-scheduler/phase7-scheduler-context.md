# Phase 7: Scheduled Collection — Context
> Last Updated: 2026-02-15
> Status: Planning

## 1. 핵심 파일

### 이 Phase에서 읽어야 할 기존 코드
| 파일 | 용도 |
|------|------|
| `.github/workflows/ci.yml` | 기존 CI/CD 워크플로우 (참고용 — Python/pip 설정 패턴) |
| `backend/scripts/collect.py` | 수집 CLI (--start, --end 인자) |
| `backend/scripts/healthcheck.py` | 데이터 신선도 검증 + Discord 알림 |
| `backend/scripts/run_research.py` | 분석 파이프라인 CLI (--start, --end 인자) |
| `backend/config/settings.py` | 환경변수 목록 (DATABASE_URL, ALERT_WEBHOOK_URL) |
| `backend/collector/alerting.py` | Discord webhook 전송 로직 |

### 이 Phase에서 생성/수정할 파일
| 파일 | 작업 |
|------|------|
| `.github/workflows/daily-collect.yml` | **신규** — cron scheduled workflow |
| `docs/runbook.md` | **수정** — 스케줄 수집 섹션 추가 |

## 2. 데이터 인터페이스

### 입력 (어디서 읽는가)
- **FDR API** → `collect.py` → `price_daily` 테이블 UPSERT
- **Railway PostgreSQL** → `healthcheck.py` 신선도 조회
- **Railway PostgreSQL** → `run_research.py` 팩터/시그널/백테스트 계산

### 출력 (어디에 쓰는가)
- **Railway PostgreSQL** — price_daily, factor_daily, signal_daily, backtest_*, job_run
- **Discord Webhook** — 헬스체크 실패 시 알림
- **GitHub Actions Logs** — 실행 이력/디버깅

## 3. 주요 결정사항

| 결정 | 근거 |
|------|------|
| GitHub Actions cron (Railway cron X) | 무료, 기존 CI/CD 인프라 활용, 별도 서비스 불필요 |
| UTC 09:00 (KST 18:00) | 한국 장 마감 (15:30) 후 충분한 여유, FDR 데이터 반영 대기 |
| workflow_dispatch 추가 | 수동 실행/디버깅/백필 용도 |
| 기존 스크립트 변경 없음 | collect.py, healthcheck.py, run_research.py 그대로 재활용 |
| Railway Public Networking 필요 | GitHub Actions → Railway DB 직접 접속 (내부 URL 사용 불가) |
| continue-on-error for healthcheck | 헬스체크 실패해도 research 파이프라인은 실행 (부분 데이터로도 분석 가능) |

## 4. 컨벤션 체크리스트

### 데이터 관련
- [x] FDR primary source 유지
- [x] idempotent UPSERT (기존 collect.py)
- [x] T-7 ~ T 롤링 윈도우 (기존 daily_collect.bat과 동일)

### 인코딩 관련
- [x] `PYTHONUTF8=1` 환경변수 설정

### 배포/운영 관련
- [x] GitHub Secrets로 시크릿 관리 (DATABASE_URL, WEBHOOK_URL)
- [x] 환경변수 하드코딩 금지
- [x] 기존 ci.yml과 분리된 독립 워크플로우

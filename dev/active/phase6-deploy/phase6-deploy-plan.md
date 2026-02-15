# Phase 6: Deploy & Ops
> Last Updated: 2026-02-15
> Status: Complete

## 1. Summary (개요)

**목적**: Phase 1~5 완료 후 통합 검증 + CI/CD + 실제 배포 + 운영 안정화. 배치 통합, 테스트 검증, GitHub Actions CI/CD 파이프라인, Railway(백엔드) + Vercel(프론트엔드) 배포, 운영 문서 작성.

**범위**: 기존 코드의 통합 검증, CI/CD 파이프라인 구축, 프로덕션 배포, 운영 도구 보강.

**예상 결과물**:
- `daily_collect.bat` 통합 배치 (collect → healthcheck → research + 로그 로테이션)
- `preflight.py` pre-deployment 체크 스크립트
- `.github/workflows/ci.yml` GitHub Actions CI (test + lint)
- `.github/workflows/deploy.yml` GitHub Actions CD (auto-deploy)
- Railway App 배포 (FastAPI 백엔드)
- Vercel 배포 (React 프론트엔드)
- `docs/runbook.md` 운영 문서
- 전체 테스트 통과 확인

## 2. Current State (현재 상태)

- **Phase 1~5**: 64/64 tasks 완료
- **배치 스크립트**: `daily_collect.bat` (collect + healthcheck), `register_scheduler.bat` 존재
- **리서치 스크립트**: `run_research.py` 배치에 통합 완료 (Step 6.1)
- **로깅**: JSON 구조화 로그 (`config/logging.py`), Discord 알림 코드 (`collector/alerting.py`) 존재
- **헬스체크**: `healthcheck.py` 데이터 신선도 체크 존재
- **테스트**: 405 passed, 7 skipped
- **CI/CD**: 없음 (GitHub Actions 미설정)
- **배포**: 없음 (로컬 개발 환경만)
- **인프라**: Railway PostgreSQL (DB만), GitHub 리포 (`bluecalif/stock-dashboard`)

## 3. Target State (목표 상태)

| 영역 | 목표 | 현재 |
|------|------|------|
| 배치 통합 | collect → healthcheck → research 순차 실행 | collect + healthcheck만 |
| 로그 관리 | 30일 로테이션 자동 삭제 | 로테이션 없음 |
| Pre-deployment | 환경/DB/데이터 사전 검증 스크립트 | 없음 |
| 테스트 | 전체 통과 확인 + 실패 수정 | 405 passed (미확인) |
| CI | GitHub Actions — push/PR 시 test + lint 자동 실행 | 없음 |
| 백엔드 배포 | Railway App — FastAPI + uvicorn | 로컬만 |
| 프론트엔드 배포 | Vercel — React SPA 정적 배포 | 로컬만 |
| CD | main push 시 자동 배포 | 없음 |
| 운영 문서 | Runbook (일일 운영, 장애 대응, 배포 가이드) | 없음 |

## 4. Implementation Stages

### Stage A: 배치 통합 (Step 6.1, 6.4)
- `daily_collect.bat`에 `run_research.py` 호출 추가
- 30일 이상 로그 파일 자동 삭제

### Stage B: 테스트 검증 (Step 6.2)
- `python -m pytest` 전체 실행
- 실패 테스트 수정

### Stage C: 운영 도구 (Step 6.3)
- `preflight.py` pre-deployment 체크 스크립트 생성

### Stage D: CI/CD 파이프라인 (Step 6.7)
- `.github/workflows/ci.yml` — push/PR 시 pytest + ruff 자동 실행
- Python 3.12, PostgreSQL service container
- 캐싱 (pip cache)

### Stage E: 프로덕션 배포 (Step 6.8, 6.9)
- **백엔드**: Railway App 배포
  - `Procfile` 또는 `railway.toml` 설정
  - 환경변수 설정 (DATABASE_URL, 기타)
  - CORS에 프론트엔드 프로덕션 URL 추가
- **프론트엔드**: Vercel 배포
  - `vite.config.ts`에 API base URL 환경변수 처리
  - Vercel 프로젝트 설정 (build command, output directory)

### Stage F: 문서화 (Step 6.5, 6.6)
- `docs/runbook.md` 운영 문서 (배포 절차 포함)
- dev-docs 갱신 + 커밋

### Stage G: 배포 안정화 (Step 6.10~6.13)
- **근본 이슈 해결**: 헬스체크 503 체인, Alembic 자동화, CMD exec form
- **문서 확장**: cli-deployment.md에 트러블슈팅/체크리스트/운영 명령어 추가
- **배포 검증**: D-4 수정 push → Railway 성공 확인 + 환경변수 설정

## 5. Task Breakdown

| # | Task | Size | Stage | Dependencies |
|---|------|------|-------|-------------|
| 6.1 | 리서치 파이프라인 배치 스케줄링 | S | A | - |
| 6.2 | 테스트 전체 실행 & 검증 | M | B | - |
| 6.3 | Pre-deployment 체크 스크립트 | M | C | - |
| 6.4 | 로그 로테이션 | S | A | 6.1 |
| 6.7 | GitHub Actions CI 파이프라인 | M | D | 6.2 |
| 6.8 | 백엔드 Railway 배포 | M | E | 6.2, 6.7 |
| 6.9 | 프론트엔드 Vercel 배포 | M | E | 6.8 |
| 6.5 | 운영 문서 (Runbook) | M | F | 6.1, 6.3, 6.8, 6.9 |
| 6.6 | dev-docs 갱신 & 커밋 | S | F | 6.1~6.9 |

## 6. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| 테스트 실패 발견 | 수정 시간 소요 | 실패 테스트 우선 분석, 환경 의존적 skip 허용 |
| run_research.py 배치 연동 시 경로 문제 | 배치 실행 실패 | 기존 collect.py 패턴 동일 적용 |
| Discord webhook 미설정 | 알림 기능 미검증 | 코드 레벨 검증만, 실발송 제외 |
| Railway 무료 티어 제약 | 슬립/재시작 이슈 | Hobby 플랜 또는 starter 플랜 활용 |
| Vercel CORS 이슈 | API 호출 실패 | CORS origin에 Vercel 도메인 추가 |
| GitHub Actions 시크릿 관리 | CI 실패 | DATABASE_URL 등 GitHub Secrets 설정 |

## 7. Dependencies

### 내부
- `scripts/run_research.py` — 리서치 파이프라인 CLI (Phase 3)
- `scripts/healthcheck.py` — 데이터 신선도 체크 (Phase 3)
- `scripts/collect.py` — 수집 CLI (Phase 2)
- `api/main.py` — FastAPI 앱 엔트리포인트 (Phase 4)
- `db/session.py` — DB 세션 (Phase 1)

### 외부
- Railway PostgreSQL (DATABASE_URL) — 기존 사용 중
- Railway App 서비스 — 백엔드 호스팅 (신규)
- Vercel — 프론트엔드 호스팅 (신규)
- GitHub Actions — CI/CD (신규)

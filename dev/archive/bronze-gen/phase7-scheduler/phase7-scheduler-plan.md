# Phase 7: Scheduled Collection (GitHub Actions Cron)
> Last Updated: 2026-02-15
> Status: Planning

## 1. Summary (개요)

**목적**: 일일 데이터 수집 파이프라인을 GitHub Actions cron으로 자동화하여 Windows PC 의존성 제거.

**범위**: GitHub Actions scheduled workflow 1개 생성 (collect → healthcheck → research)

**예상 결과물**:
- `.github/workflows/daily-collect.yml` — cron + 수동 실행 가능한 워크플로우
- 매일 KST 18:00 자동 수집/분석, Railway DB에 직접 적재

## 2. Current State (현재 상태)

- Phase 0~6 전체 완료 (77/77 tasks)
- 데이터 수집은 Windows Task Scheduler (`daily_collect.bat`) 기반 → PC 꺼지면 중단
- 기존 스크립트: `collect.py`, `healthcheck.py`, `run_research.py` — CLI 인터페이스 완비
- Railway DB 운영 중, FastAPI + Vercel 프론트엔드 배포 완료
- CI/CD: GitHub Actions (lint + test + deploy) 이미 운영 중 (`ci.yml`)

## 3. Target State (목표 상태)

| 영역 | 현재 | 목표 |
|------|------|------|
| 수집 스케줄 | Windows Task Scheduler (PC 의존) | GitHub Actions cron (클라우드, 24/7) |
| 수동 실행 | 로컬 CLI 직접 실행 | `workflow_dispatch` (GitHub UI에서 원클릭) |
| 실행 모니터링 | 로컬 로그 파일 | GitHub Actions 로그 + Discord 알림 |
| 기존 스크립트 | 유지 | 변경 없음 (로컬 수동 실행 가능) |

## 4. Implementation Stages

### Stage A: 사전 준비 (수동)
- Railway PostgreSQL Public Networking 활성화 확인
- GitHub Secrets 등록 (`RAILWAY_DATABASE_URL`, `ALERT_WEBHOOK_URL`)

### Stage B: Workflow 구현
- `.github/workflows/daily-collect.yml` 생성
- 트리거: `schedule` (cron `0 9 * * *` = UTC 09:00 = KST 18:00) + `workflow_dispatch`
- 파이프라인: checkout → Python 3.12 → pip install → collect → healthcheck → research

### Stage C: 검증 + 문서
- `workflow_dispatch` 수동 실행으로 E2E 검증
- 기존 `docs/runbook.md` 업데이트 (GitHub Actions 스케줄 관련)

## 5. Task Breakdown

| # | Task | Size | 의존성 | 설명 |
|---|------|------|--------|------|
| 7.1 | Railway Public Networking 확인 | S | — | Railway 대시보드에서 Postgres 외부 접속 활성화 |
| 7.2 | GitHub Secrets 등록 | S | 7.1 | `RAILWAY_DATABASE_URL`, `ALERT_WEBHOOK_URL` |
| 7.3 | `daily-collect.yml` 작성 | M | — | cron + dispatch + 3단계 파이프라인 |
| 7.4 | workflow_dispatch 수동 검증 | M | 7.2, 7.3 | GitHub UI에서 수동 실행 + 로그 확인 |
| 7.5 | Runbook 업데이트 | S | 7.4 | 스케줄 수집 관련 문서 추가 |
| 7.6 | dev-docs 갱신 | S | 7.5 | Phase 7 완료 처리 |

## 6. Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Railway Public Networking 비활성화 | DB 접속 불가 | 대시보드에서 TCP Proxy 활성화 |
| GitHub Actions cron 지연 (최대 15분) | 수집 시간 약간 변동 | 허용 범위 내, 장 마감 후이므로 무관 |
| FDR가 GitHub Actions IP를 차단 | 수집 실패 | FDR은 IP 제한 없음 (공개 API) |
| Railway 외부 URL 노출 | 보안 | GitHub Secrets로 관리, DB 비밀번호 포함 |

## 7. Dependencies

### 외부
- **Railway PostgreSQL**: Public Networking (TCP Proxy) 필요
- **GitHub Actions**: `schedule` + `workflow_dispatch` 트리거
- **FDR**: Ubuntu 환경에서 정상 동작 확인 필요 (CI 테스트에서 이미 검증됨)

### 기존 코드 (변경 없음)
- `backend/scripts/collect.py` — 수집 CLI
- `backend/scripts/healthcheck.py` — 데이터 신선도 검증
- `backend/scripts/run_research.py` — 분석 파이프라인
- `backend/collector/alerting.py` — Discord 알림

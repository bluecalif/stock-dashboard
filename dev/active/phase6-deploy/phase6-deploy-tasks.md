# Phase 6: Deploy & Ops — Tasks
> Last Updated: 2026-02-15
> Status: Complete

## Stage A: 배치 통합
- [x] 6.1 리서치 파이프라인 배치 스케줄링 `[S]`
  - `daily_collect.bat`에 `run_research.py` 호출 추가
  - collect → healthcheck → research 순서
  - 로그 파일에 research 결과도 기록
- [x] 6.4 로그 로테이션 `[S]`
  - `daily_collect.bat`에 30일 이상 로그 파일 자동 삭제 추가

## Stage B: 테스트 검증
- [x] 6.2 테스트 전체 실행 & 검증 `[M]`
  - `python -m pytest` 전체 실행
  - 실패 테스트 수정: test_partial_failure mock 시그니처 수정
  - 결과: 405 passed, 7 skipped, 0 failed

## Stage C: 운영 도구
- [x] 6.3 Pre-deployment 체크 스크립트 `[M]`
  - `backend/scripts/preflight.py` 생성
  - DATABASE_URL → DB 연결 → 8개 테이블 → 7개 시드 → 최근 데이터
  - 18 checks all PASS

## Stage D: CI/CD 파이프라인
- [x] 6.7 GitHub Actions CI 파이프라인 `[M]`
  - `.github/workflows/ci.yml` 생성
  - Trigger: push/PR to master
  - Jobs: pytest + ruff, PostgreSQL 16 service container, Python 3.12

## Stage E: 프로덕션 배포
- [x] 6.8 백엔드 Railway 배포 `[M]`
  - `Procfile`, `railway.toml`, `nixpacks.toml` 생성
  - `CORS_ORIGINS` 환경변수로 프로덕션 도메인 지원
  - Railway dashboard에서 서비스 생성 + 환경변수 설정 필요
- [x] 6.9 프론트엔드 Vercel 배포 `[M]`
  - `vercel.json` SPA 라우팅 설정
  - `VITE_API_BASE_URL` 환경변수 이미 지원 (client.ts)
  - Vercel dashboard에서 프로젝트 연결 필요

## Stage F: 문서화
- [x] 6.5 운영 문서 (Runbook) `[M]`
  - `docs/runbook.md` 생성
  - 배포 절차, 트러블슈팅, 모니터링
- [x] 6.6 dev-docs 갱신 & 커밋 `[S]`
  - dev-docs 갱신 + session-compact 갱신

---

## Stage G: 배포 안정화 (근본 이슈 해결)
- [x] 6.10 헬스체크 개선 & 의존성 503 체인 `[M]`
  - `dependencies.py`: RuntimeError → HTTPException(503)
  - `health.py`: DB 실패 시 503 반환 + `/v1/ready` 진단 엔드포인트 분리
- [x] 6.11 Dockerfile & railway.toml 개선 `[S]`
  - Dockerfile: CMD exec form 전환, alembic 파일 COPY 추가
  - railway.toml: startCommand에 `alembic upgrade head &&` 추가
- [x] 6.12 cli-deployment.md 대폭 확장 `[L]`
  - 트러블슈팅 가이드 (D-1~D-4 패턴별)
  - 배포 전/후 체크리스트
  - Railway 서비스 구조 & Dockerfile vs nixpacks
  - 운영 명령어 모음
- [ ] 6.13 D-4 수정 커밋 & push → Railway 배포 확인 `[M]`
  - 환경변수 설정 안내 (DATABASE_URL, CORS_ORIGINS, VITE_API_BASE_URL)
  - CI 파이프라인 실행 → Railway 배포 성공 확인

---

## Summary
- **Tasks**: 12/13 완료 (92%)
- **Phase 6 In Progress** — Stage G 배포 안정화 진행 중

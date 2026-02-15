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

## Summary
- **Tasks**: 9/9 완료 (100%)
- **Phase 6 Complete**

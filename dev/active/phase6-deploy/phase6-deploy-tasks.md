# Phase 6: Deploy & Ops — Tasks
> Last Updated: 2026-02-15
> Status: In Progress

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
- [ ] 6.3 Pre-deployment 체크 스크립트 `[M]`
  - `backend/scripts/preflight.py` 생성
  - .env 필수 변수 검증 (DATABASE_URL)
  - DB 연결 테스트
  - 테이블 존재 확인 (8개)
  - asset_master 시드 확인 (7개 자산)
  - 최근 수집 데이터 존재 여부

## Stage D: CI/CD 파이프라인
- [ ] 6.7 GitHub Actions CI 파이프라인 `[M]`
  - `.github/workflows/ci.yml` 생성
  - Trigger: push to master, PR to master
  - Jobs: pytest + ruff lint
  - PostgreSQL service container (테스트용)
  - pip cache로 설치 속도 개선
  - Python 3.12 매트릭스

## Stage E: 프로덕션 배포
- [ ] 6.8 백엔드 Railway 배포 `[M]`
  - Railway App 서비스 생성 (기존 Railway 프로젝트에 추가)
  - `Procfile` 작성: `web: uvicorn api.main:app --host 0.0.0.0 --port $PORT`
  - `railway.toml` 설정 (빌드 커맨드, 시작 커맨드)
  - 환경변수 설정: DATABASE_URL (내부 연결), LOG_LEVEL, PYTHONUTF8
  - `requirements.txt` 생성 (Railway 호환)
  - CORS에 Vercel 프로덕션 도메인 추가
  - 배포 확인: `/v1/health` 엔드포인트 응답 테스트
- [ ] 6.9 프론트엔드 Vercel 배포 `[M]`
  - Vercel 프로젝트 연결 (GitHub 리포)
  - `VITE_API_BASE_URL` 환경변수 처리 (프론트엔드 코드)
  - Vercel 설정: root directory → `frontend/`, build command → `npm run build`, output → `dist`
  - `vercel.json` SPA 라우팅 리다이렉트 설정
  - 배포 확인: 대시보드 로드 + API 연결 테스트

## Stage F: 문서화
- [ ] 6.5 운영 문서 (Runbook) `[M]`
  - `docs/runbook.md` 생성
  - 일일 운영 흐름, 수동 실행, 장애 대응
  - 배포 절차 (Railway, Vercel)
  - Discord webhook 설정, Task Scheduler 관리, 로그 확인
  - 환경변수 목록 + 설명
- [ ] 6.6 dev-docs 갱신 & 커밋 `[S]`
  - dev-docs 갱신
  - 전체 변경사항 커밋
  - session-compact.md 갱신

---

## Summary
- **Tasks**: 9개 (S: 3, M: 6)
- **Status**: 3/9 완료 (33%)

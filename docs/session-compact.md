# Session Compact

> Generated: 2026-03-03
> Source: Step Update (hotfix — Daily Collect 5일 연속 실패 수정)

## Goal
Daily Collect hotfix — KS200 LOGOUT + 부분 성공 exit code + Discord 403 수정

## Completed (이번 세션)
- [x] **Hotfix**: Daily Collect 5일 연속 실패 (2/27~3/3) 원인 분석 및 수정 (`9624dbf`)
  - KS200 LOGOUT: FDR Naver 경로 차단 → `^KS200` (Yahoo Finance) fallback 추가
  - collect.py exit code: 1개라도 실패 → exit 1 → 부분 성공(6/7) 시 exit 0으로 변경
  - Discord 403: Cloudflare가 Python urllib User-Agent 차단 → `User-Agent: StockDashboard/1.0` 추가
  - SYMBOL_MAP: `"fallback"` → `"fallbacks"` 다중 fallback 체인 지원

## Current State

### Git 상태
- 최신 커밋: `9624dbf` (push 대기)
- 브랜치: `master`

### GitHub Actions
- **CI** (`ci.yml`): ✅ test → deploy-railway → deploy-vercel
- **Daily Collect** (`daily-collect.yml`): ❌ 5일 연속 실패 (2/27~3/3) → hotfix 적용 (`9624dbf`)
  - 원인: KS200 LOGOUT (1/7 실패) + exit 1 → 전체 실패 처리

### 인프라 상태
- **Railway**: backend + Postgres 운영 중
  - Public Networking: `mainline.proxy.rlwy.net:34025`
  - 공개 URL: `https://backend-production-e5bc.up.railway.app`
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`
- **GitHub Secrets**: `RAILWAY_DATABASE_URL`, `ALERT_WEBHOOK_URL` 등록 완료
- **Discord**: webhook 알림 설정 완료

## Remaining / TODO
- Phase 0~7 전체 완료 (83/83 tasks, 100%)
- 향후 고려사항:
  - [ ] Hantoo REST API fallback (v0.9+)
  - [ ] 대시보드 기능 확장 (알림 이력, 수집 상태 표시 등)

## Key Decisions
- **GitHub Actions cron 선택**: Railway cron 대신 무료 + 기존 CI 인프라 활용
- **Public Networking 필수**: GitHub Actions → Railway DB 직접 접속 (internal URL 사용 불가)
- **RAILWAY_DATABASE_URL**: internal URL이 아닌 public TCP proxy URL 사용 필수
- **continue-on-error for healthcheck**: 헬스체크 실패해도 research 파이프라인 실행
- **KS200 fallback `^KS200`**: FDR Naver 경로(KS200, KS11) LOGOUT 지속 → Yahoo 경로(`^KS200`)가 실제 KOSPI200 지수 데이터 반환
- **부분 성공 exit 0**: 전체 실패(0/7)만 exit 1, 부분 성공은 exit 0 → research pipeline 보장
- **Discord User-Agent 필수**: Cloudflare가 `Python-urllib` UA 차단 (error 1010)

## Context
- 다음 세션에서는 답변에 한국어를 사용하세요.
- **Railway**: 프로젝트 `stock-dashboard`, 서비스 `backend` + `Postgres`
  - 프로젝트 ID: `50fe3dfd-fc3c-495a-b1dd-e10c4cd68aac`
  - 서비스 ID: `0f64966e-c557-483e-a79e-7a385cf4ba6c`
  - 공개 URL: `https://backend-production-e5bc.up.railway.app`
- **Vercel**: projectId `prj_JHiNy6kA0O1AwGv0z7XRoEQKT069`, orgId `team_OzRhH4vDDonkLhxYA9lsAOFS`
  - 프로덕션 URL: `https://stock-dashboard-alpha-lilac.vercel.app`
- **gh CLI**: `bluecalif` 계정, remote: `https://github.com/bluecalif/stock-dashboard.git`
- **배포 아키텍처**:
  ```
  [GitHub Actions]
   ├── CI (ci.yml): test → deploy-railway + deploy-vercel
   └── Daily Collect (daily-collect.yml): collect → healthcheck → research
  ```

## Project Status

| Phase | 상태 | Tasks |
|-------|------|-------|
| 0~5 | ✅ 완료 | 64/64 |
| 6 | ✅ 완료 | 13/13 |
| 7 | ✅ 완료 | 6/6 |
| **Total** | **✅ 완료** | **83/83 (100%)** |

## Next Action
- hotfix push 후 Daily Collect 정상 동작 확인 (다음 cron 또는 workflow_dispatch)
- MVP 전체 완료. 사용자 지시에 따라 다음 작업 결정.
- 후보: Hantoo API 연동, 대시보드 기능 확장, 모니터링 강화 등

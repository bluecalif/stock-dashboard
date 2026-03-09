# Session Compact

> Generated: 2026-03-03 20:30
> Source: Conversation compaction via /compact-and-go

## Goal
Daily Collect GitHub Actions 5일 연속 실패 (2/27~3/3) 원인 분석 및 hotfix

## Completed (이번 세션)
- [x] **실패 원인 분석**: 5일치 로그 전수 조사 — 동일 패턴 확인
- [x] **KS200 LOGOUT 수정**: FDR Naver 경로(KS200, KS11) 차단 → `^KS200` (Yahoo Finance) fallback 추가 (`9624dbf`)
  - `SYMBOL_MAP`: `"fallback"` → `"fallbacks"` 다중 fallback 체인 지원
  - 069500 (KODEX 200 ETF)은 지수가 아니므로 제외, `^KS200`이 실제 KOSPI200 지수
- [x] **collect.py exit code 수정**: 부분 성공(6/7) 시 exit 0 → research pipeline 정상 실행 (`9624dbf`)
- [x] **Discord 403 수정**: Cloudflare error 1010 (User-Agent 차단) → `User-Agent: StockDashboard/1.0` 추가 (`9624dbf`)
- [x] **run_research.py 수정**: `--missing-threshold` CLI 파라미터 추가 + 부분 성공 exit 0 (`21b7023`)
  - 7일 범위에서 주말 결측 → 16.7% > 10% threshold → daily-collect.yml에서 `--missing-threshold 0.20` 전달
- [x] **workflow_dispatch E2E 검증 성공**: 전 단계 통과 (40초)

## Current State

### Git 상태
- 최신 커밋: `21b7023` (pushed to origin/master)
- 브랜치: `master`

### GitHub Actions
- **CI** (`ci.yml`): ✅ test → deploy-railway → deploy-vercel
- **Daily Collect** (`daily-collect.yml`): ✅ hotfix 적용 후 workflow_dispatch 검증 성공 (run #22620326208)

### Changed Files
- `backend/collector/fdr_client.py` — KS200 fallback `^KS200`, 다중 fallbacks 체인
- `backend/collector/alerting.py` — User-Agent 헤더 추가
- `backend/scripts/collect.py` — 부분 성공 exit 0
- `backend/scripts/run_research.py` — `--missing-threshold` 파라미터, 부분 성공 exit 0
- `backend/tests/unit/test_fdr_client.py` — fallbacks 테스트 업데이트
- `.github/workflows/daily-collect.yml` — `--missing-threshold 0.20` 전달

### 인프라 상태
- **Railway**: backend + Postgres 운영 중
  - Public Networking: `mainline.proxy.rlwy.net:34025`
  - 공개 URL: `https://backend-production-e5bc.up.railway.app`
- **Vercel**: `https://stock-dashboard-alpha-lilac.vercel.app`
- **GitHub Secrets**: `RAILWAY_DATABASE_URL`, `ALERT_WEBHOOK_URL` 등록 완료
- **Discord**: webhook 알림 정상 작동 확인 (User-Agent 수정 후)

## Remaining / TODO
- Phase 0~7 전체 완료 (83/83 tasks, 100%) + hotfix 완료
- 향후 고려사항:
  - [ ] Hantoo REST API fallback (v0.9+)
  - [ ] 대시보드 기능 확장 (알림 이력, 수집 상태 표시 등)
  - [ ] FDR KS200/KS11 Naver 경로 복구 모니터링 (현재 Yahoo ^KS200 fallback 사용 중)

## Key Decisions
- **KS200 fallback `^KS200`**: FDR Naver 경로(KS200, KS11) LOGOUT 지속 → Yahoo 경로(`^KS200`)가 실제 KOSPI200 지수 데이터 반환. 069500은 ETF이므로 부적합.
- **부분 성공 exit 0 정책**: collect.py, run_research.py 모두 적용. 전체 실패(0/N)만 exit 1.
- **Discord User-Agent 필수**: Cloudflare가 `Python-urllib/3.12` UA를 차단 (error 1010). `StockDashboard/1.0`으로 해결.
- **missing-threshold 분리**: 기본 10%, daily cron에서는 20% (7일 범위 주말 결측 허용)

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
- MVP 전체 완료 + hotfix 완료. 사용자 지시에 따라 다음 작업 결정.
- 후보: Hantoo API 연동, 대시보드 기능 확장, 모니터링 강화 등

# Phase A: Auth — Tasks
> Last Updated: 2026-03-12
> Status: ✅ Complete (16/16)

## Stage A: Backend 기반 (Step A.1~A.4)

- [x] A.1 DB 모델: User, UserSession + Alembic migration `[M]` → `49f9928`
- [x] A.2 Settings: jwt_secret_key, jwt_algorithm, access/refresh TTL `[S]` → `6bbc6bb`
- [x] A.3 Pydantic 스키마: auth.py `[S]` → `2c3e9a4`
- [x] A.4 Repository: user_repo.py, session_repo.py `[M]` → `3d85590`

## Stage B: Backend Auth 로직 (Step A.5~A.7)

- [x] A.5 Service: auth_service.py `[L]` → `0ea34b7`
  - bcrypt 직접 사용 (passlib 제거 — bcrypt 5.x 호환)
- [x] A.6+A.7 Router + Dependencies `[M]` → `66fc0e1`

## Stage C: Backend 통합 + 테스트 (Step A.8~A.10)

- [x] A.8 main.py 라우터 등록 + pyproject.toml 의존성 `[S]` → `985c093`
- [x] A.9+A.10 Auth 테스트 16개 + Regression 426 passed `[M]` → `4e1419f`

## Stage D: Frontend Auth (Step A.11~A.15)

- [x] A.11 Zustand authStore + auth API + types `[M]` → `fcdeed3`
  - `src/store/authStore.ts`, `src/api/auth.ts`, `src/types/auth.ts`
  - zustand 설치, localStorage 토큰 영속화
- [x] A.12 LoginPage + SignupPage `[M]` → `fcdeed3`
  - `src/pages/LoginPage.tsx`, `src/pages/SignupPage.tsx`
- [x] A.13 ProtectedRoute + client.ts interceptor `[M]` → `fcdeed3`
  - `src/components/auth/ProtectedRoute.tsx`
  - `src/api/client.ts` — Bearer 토큰 + 401 refresh + 대기열 처리
- [x] A.14 Sidebar 사용자 정보 + 로그아웃 `[S]` → `fcdeed3`
- [x] A.15 App.tsx 라우팅 업데이트 `[S]` → `fcdeed3`

## Stage E: E2E 검증 + 문서 (Step A.16~A.17)

- [x] A.16 E2E 검증 `[M]` — 프로덕션 확인 완료
  - Railway JWT_SECRET_KEY 설정 완료 (대시보드)
  - 회원가입 → 로그인 → 대시보드 → 로그아웃 플로우 정상
- [x] A.17 dev-docs 갱신 `[S]` — 이 파일

---

## Summary
- **Total**: 16 tasks (S: 6, M: 9, L: 1)
- **Progress**: 16/16 (100%) ✅

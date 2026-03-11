# Phase A: Auth — Tasks
> Last Updated: 2026-03-11
> Status: Planning (0/16)

## Stage A: Backend 기반 (Step A.1~A.4)

- [ ] A.1 DB 모델: User, UserSession + Alembic migration `[M]`
  - `db/models.py`에 User, UserSession 모델 추가
  - `alembic revision --autogenerate -m "Add auth tables"`
  - Railway DB에 마이그레이션 적용

- [ ] A.2 Settings: jwt_secret_key, jwt_algorithm, access/refresh TTL `[S]`
  - `config/settings.py` 확장
  - `.env.example` 업데이트

- [ ] A.3 Pydantic 스키마: auth.py `[S]` — blocked by A.1
  - SignupRequest, LoginRequest, RefreshRequest
  - TokenResponse, UserResponse

- [ ] A.4 Repository: user_repo.py, session_repo.py `[M]` — blocked by A.1
  - user_repo: create_user, get_by_email, get_by_id
  - session_repo: create_session, get_by_token_hash, delete_session, delete_expired

## Stage B: Backend Auth 로직 (Step A.5~A.7)

- [ ] A.5 Service: auth_service.py `[L]` — blocked by A.2, A.4
  - hash_password, verify_password (passlib bcrypt)
  - create_access_token, create_refresh_token (python-jose)
  - signup, login, refresh 비즈니스 로직
  - refresh token rotation

- [ ] A.6 Router: auth.py `[M]` — blocked by A.3, A.5
  - POST /v1/auth/signup → 201 UserResponse
  - POST /v1/auth/login → TokenResponse
  - POST /v1/auth/refresh → TokenResponse
  - GET /v1/auth/me → UserResponse

- [ ] A.7 Dependencies: get_current_user, get_current_user_optional `[M]` — blocked by A.5
  - OAuth2PasswordBearer scheme
  - get_current_user: JWT decode → User (401 on failure)
  - get_current_user_optional: None on no token (기존 API 하위 호환)

## Stage C: Backend 통합 + 테스트 (Step A.8~A.10)

- [ ] A.8 main.py 라우터 등록 + pyproject.toml 의존성 `[S]` — blocked by A.6
  - `app.include_router(auth.router)`
  - CORS allow_headers에 Authorization 확인
  - python-jose, passlib, python-multipart 추가

- [ ] A.9 단위 테스트: auth service + auth router `[M]` — blocked by A.6, A.7
  - test_auth_service.py: signup/login/refresh/token 검증
  - test_auth_router.py: httpx TestClient 엔드포인트 테스트

- [ ] A.10 Regression: 기존 tests 통과 확인 `[S]` — blocked by A.8
  - `python -m pytest` 전체 실행
  - `ruff check .` lint 통과

## Stage D: Frontend Auth (Step A.11~A.15)

- [ ] A.11 Zustand authStore + auth API + types `[M]` — blocked by A.6
  - `src/store/authStore.ts` — user, tokens, login/logout/refresh actions
  - `src/api/auth.ts` — signup, login, refresh, getMe API 함수
  - `src/types/auth.ts` — User, TokenResponse, SignupRequest, LoginRequest 타입
  - `package.json` — zustand 추가

- [ ] A.12 LoginPage + SignupPage `[M]` — blocked by A.11
  - `src/pages/LoginPage.tsx` — 이메일/비밀번호 폼 + 에러 표시
  - `src/pages/SignupPage.tsx` — 이메일/비밀번호/닉네임 폼

- [ ] A.13 ProtectedRoute + client.ts interceptor `[M]` — blocked by A.11
  - `src/components/auth/ProtectedRoute.tsx` — 미인증 시 /login 리다이렉트
  - `src/api/client.ts` — request interceptor (Bearer), response interceptor (401 → refresh)

- [ ] A.14 Sidebar 사용자 정보 + 로그아웃 `[S]` — blocked by A.11
  - `src/components/layout/Sidebar.tsx` — 하단에 user 표시 + 로그아웃 버튼

- [ ] A.15 App.tsx 라우팅 업데이트 `[S]` — blocked by A.12, A.13
  - /login, /signup 라우트 추가
  - 기존 라우트를 ProtectedRoute로 감싸기 (optional — MVP 호환 고려)

## Stage E: E2E 검증 + 문서 (Step A.16~A.17)

- [ ] A.16 E2E 검증 `[M]` — blocked by A.10, A.15
  - signup → login → access token 확인
  - refresh → 새 토큰 발급
  - /me → 사용자 정보 반환
  - 기존 API (prices, factors 등) → auth 없이도 접근 가능 확인
  - 로그인 UI → 대시보드 진입 → 사이드바 사용자 표시

- [ ] A.17 dev-docs 갱신 + 커밋 `[S]` — blocked by A.16
  - Phase A tasks 업데이트 (commit hash 기록)
  - project-overall 동기화
  - session-compact 갱신

---

## Summary
- **Total**: 16 tasks (S: 6, M: 9, L: 1)
- **Progress**: 0/16 (0%)
- **파일 집계**: 신규 14 / 수정 6 / Migration 1

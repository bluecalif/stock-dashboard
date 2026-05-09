# Phase A: Auth + 사용자 컨텍스트
> Last Updated: 2026-03-11
> Status: Planning

## 1. Summary (개요)

**목적**: JWT 인증 시스템 구축 + 사용자별 데이터 격리 기반 마련. Post-MVP 전체의 기초 인프라.

**범위**:
- Backend: users/user_sessions 테이블, Auth API (signup/login/refresh/me), JWT 토큰 관리
- Frontend: Zustand auth store, 로그인/회원가입 UI, ProtectedRoute, Bearer interceptor
- 기존 공개 API: auth 없이 하위 호환 유지 (optional auth)

**예상 결과물**:
- 회원가입 → 로그인 → access token(30분) + refresh token(7일) 발급
- 인증된 요청에 사용자 컨텍스트 주입 (`get_current_user` DI)
- 미인증 사용자도 기존 12개 API 접근 가능 (optional auth)
- 프론트엔드 로그인 UI + 401 자동 리프레시

## 2. Current State (현재 상태)

- MVP Phase 0~7 완료 (83/83 tasks)
- FastAPI 12 endpoints, 409 tests, ruff clean
- React SPA 6 pages (인증 없음, 전체 공개)
- Railway (backend+DB) + Vercel (frontend) 운영 중
- Router-Service-Repository 3계층 아키텍처 확립
- `Depends(get_db)` DI 패턴 활용 중

## 3. Target State (목표 상태)

| 영역 | Before | After |
|------|--------|-------|
| 인증 | 없음 | JWT (access 30min + refresh 7d) |
| DB | 8 테이블 | 10 테이블 (+users, user_sessions) |
| API | 12 endpoints (공개) | 16 endpoints (12 공개 + 4 auth) |
| DI | get_db | get_db + get_current_user + get_current_user_optional |
| Frontend 상태 | useState/useEffect | + Zustand authStore |
| Frontend 라우팅 | 6 routes (공개) | 8 routes (6 + login + signup) |
| Frontend API | Authorization 없음 | Bearer 자동 첨부 + 401 refresh |

## 4. Implementation Stages

### Stage A: Backend 기반 (Step A.1~A.4)
- DB 모델 (User, UserSession) + Alembic 마이그레이션
- Settings 확장 (jwt_secret_key, jwt_algorithm, TTL)
- Auth 스키마 (SignupRequest, LoginRequest, TokenResponse, UserResponse)
- Auth Repository (user_repo, session_repo)

### Stage B: Backend Auth 로직 (Step A.5~A.7)
- Auth Service (password hash, JWT 생성/검증, signup/login/refresh 로직)
- Auth Router (POST signup/login/refresh, GET me)
- Dependencies 확장 (get_current_user, get_current_user_optional)

### Stage C: Backend 통합 + 테스트 (Step A.8~A.10)
- main.py 라우터 등록 + CORS 확인
- 단위 테스트 (auth service, auth router)
- 기존 테스트 통과 확인 (regression)

### Stage D: Frontend Auth (Step A.11~A.15)
- Zustand authStore + auth API 클라이언트
- LoginPage + SignupPage
- ProtectedRoute + client.ts interceptor (Bearer, 401 refresh)
- Sidebar 사용자 정보 + 로그아웃
- App.tsx 라우팅 업데이트

### Stage E: E2E 검증 + 문서 (Step A.16~A.17)
- E2E 검증: signup → login → refresh → /me → 기존 API 접근
- dev-docs 갱신

## 5. Task Breakdown

| Step | Task | Size | Depends | Stage |
|------|------|------|---------|-------|
| A.1 | DB 모델: User, UserSession + Alembic migration | M | - | A |
| A.2 | Settings: jwt_secret_key, jwt_algorithm, access/refresh TTL | S | - | A |
| A.3 | Pydantic 스키마: auth.py (Signup/Login/Token/User) | S | A.1 | A |
| A.4 | Repository: user_repo.py, session_repo.py | M | A.1 | A |
| A.5 | Service: auth_service.py (password hash, JWT, signup/login/refresh) | L | A.2, A.4 | B |
| A.6 | Router: auth.py (POST signup/login/refresh, GET me) | M | A.3, A.5 | B |
| A.7 | Dependencies: get_current_user, get_current_user_optional | M | A.5 | B |
| A.8 | main.py 라우터 등록 + pyproject.toml 의존성 추가 | S | A.6 | C |
| A.9 | 단위 테스트: auth service + auth router | M | A.6, A.7 | C |
| A.10 | Regression: 기존 409 tests 통과 확인 | S | A.8 | C |
| A.11 | Frontend: Zustand authStore + auth API client + types | M | A.6 | D |
| A.12 | Frontend: LoginPage + SignupPage | M | A.11 | D |
| A.13 | Frontend: ProtectedRoute + client.ts interceptor | M | A.11 | D |
| A.14 | Frontend: Sidebar 사용자 정보 + 로그아웃 | S | A.11 | D |
| A.15 | Frontend: App.tsx 라우팅 업데이트 | S | A.12, A.13 | D |
| A.16 | E2E 검증: signup → login → refresh → me → API | M | A.10, A.15 | E |
| A.17 | dev-docs 갱신 + 커밋 | S | A.16 | E |

**Size 분포**: S: 6, M: 9, L: 1, XL: 0 — **총 16 tasks** (추정 파일: 신규 14 / 수정 6 / Migration 1)

## 6. Risks & Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| JWT secret 유출 | 전체 인증 무효화 | 저 | GitHub Secrets + .env gitignore |
| Refresh token 탈취 | 세션 하이재킹 | 중 | DB 저장 + 만료 검증 + 단일 사용 |
| 기존 API 호환성 깨짐 | MVP 기능 중단 | 중 | get_current_user_optional로 하위 호환 |
| bcrypt 해싱 성능 | 로그인 지연 | 저 | 기본 rounds(12)로 충분, 사용자 소수 |
| Alembic migration 충돌 | 배포 실패 | 저 | 단일 개발자, linear migration |
| CORS + Bearer 헤더 | 프론트엔드 요청 거부 | 중 | CORS allow_headers에 Authorization 추가 |

## 7. Dependencies

### 내부 (기존 모듈)
- `db/models.py` — Base 클래스 상속, 기존 테이블과 동일 패턴
- `db/session.py` — SessionLocal 공유
- `api/dependencies.py` — get_db 패턴 확장
- `api/main.py` — 라우터 등록
- `config/settings.py` — Settings 확장

### 외부 (신규 라이브러리)
- `python-jose[cryptography]` >= 3.3.0 — JWT 생성/검증
- `passlib[bcrypt]` >= 1.7.4 — 패스워드 해싱
- `python-multipart` — OAuth2PasswordRequestForm (선택)
- `zustand` (frontend) — auth state 관리

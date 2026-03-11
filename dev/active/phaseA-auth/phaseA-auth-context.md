# Phase A: Auth — Context
> Last Updated: 2026-03-11
> Status: Planning

## 1. 핵심 파일 — 이 Phase에서 읽어야 할 기존 코드

### Backend (수정 대상)
| 파일 | 용도 | 수정 내용 |
|------|------|----------|
| `backend/db/models.py` | DB 모델 (8 테이블) | User, UserSession 모델 추가 |
| `backend/config/settings.py` | Settings 싱글톤 | JWT 설정 필드 추가 |
| `backend/api/dependencies.py` | DI (get_db) | get_current_user, get_current_user_optional 추가 |
| `backend/api/main.py` | 앱 엔트리포인트 | auth 라우터 등록 |
| `backend/pyproject.toml` | 의존성 | python-jose, passlib, python-multipart |

### Backend (참조 — 패턴 학습)
| 파일 | 참조 이유 |
|------|----------|
| `backend/api/routers/assets.py` | 간단한 라우터 패턴 |
| `backend/api/routers/backtests.py` | POST + 서비스 호출 패턴 |
| `backend/api/schemas/backtest.py` | 요청/응답 분리 패턴 |
| `backend/api/repositories/asset_repo.py` | 함수형 Repository 패턴 |
| `backend/api/repositories/backtest_repo.py` | CRUD Repository 패턴 |
| `backend/api/services/backtest_service.py` | 오케스트레이션 서비스 패턴 |
| `backend/db/alembic/env.py` | Alembic 마이그레이션 설정 |

### Frontend (수정 대상)
| 파일 | 수정 내용 |
|------|----------|
| `frontend/src/api/client.ts` | Bearer interceptor + 401 refresh |
| `frontend/src/App.tsx` | /login, /signup 라우트 추가 |
| `frontend/src/components/layout/Sidebar.tsx` | 사용자 정보 + 로그아웃 |
| `frontend/package.json` | zustand 추가 |

### Frontend (신규)
| 파일 | 용도 |
|------|------|
| `frontend/src/store/authStore.ts` | Zustand: user, tokens, login/logout/refresh |
| `frontend/src/pages/LoginPage.tsx` | 로그인 폼 |
| `frontend/src/pages/SignupPage.tsx` | 회원가입 폼 |
| `frontend/src/components/auth/ProtectedRoute.tsx` | 인증 확인 래퍼 |
| `frontend/src/api/auth.ts` | Auth API 함수 |
| `frontend/src/types/auth.ts` | Auth 타입 정의 |

## 2. 데이터 인터페이스

### 입력 (어디서 읽는가)
| 소스 | 데이터 | 용도 |
|------|--------|------|
| POST body | email, password | 로그인/회원가입 요청 |
| Authorization 헤더 | Bearer {access_token} | 인증 확인 |
| Cookie/Body | refresh_token | 토큰 갱신 |
| DB `users` | user_id, email, hashed_password | 로그인 검증 |
| DB `user_sessions` | refresh_token_hash, expires_at | 리프레시 검증 |

### 출력 (어디에 쓰는가)
| 대상 | 데이터 | 용도 |
|------|--------|------|
| DB `users` | 신규 사용자 레코드 | 회원가입 |
| DB `user_sessions` | 리프레시 토큰 세션 | 로그인/갱신 |
| HTTP Response | access_token, refresh_token, user info | 클라이언트 전달 |
| FastAPI Request State | current_user (User 객체) | 후속 엔드포인트에서 사용자 참조 |

### DB 스키마 (신규 2 테이블)

```sql
-- users
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    nickname    VARCHAR(100),
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP WITH TIME ZONE DEFAULT now(),
    updated_at  TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX ix_users_email ON users(email);

-- user_sessions (refresh token 관리)
CREATE TABLE user_sessions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id             UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash  VARCHAR(255) NOT NULL,
    expires_at          TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT now()
);
CREATE INDEX ix_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX ix_user_sessions_expires ON user_sessions(expires_at);
```

### API 엔드포인트 (신규 4개)

| Method | Path | Auth | 설명 |
|--------|------|------|------|
| POST | `/v1/auth/signup` | None | 회원가입 → UserResponse |
| POST | `/v1/auth/login` | None | 로그인 → TokenResponse (access + refresh) |
| POST | `/v1/auth/refresh` | None (refresh token in body) | 토큰 갱신 → TokenResponse |
| GET | `/v1/auth/me` | Required | 내 정보 → UserResponse |

### 토큰 플로우

```
[Signup] → users INSERT → 201 UserResponse

[Login] → email/password 검증 → access_token(30min) + refresh_token(7d) 발급
       → user_sessions INSERT (refresh_token_hash)

[Refresh] → refresh_token 검증 (hash match + expires_at)
          → 새 access_token + 새 refresh_token 발급
          → 기존 session DELETE, 새 session INSERT (rotation)

[Request] → Authorization: Bearer {access_token}
          → get_current_user DI → JWT decode → User 객체 주입

[Existing API] → get_current_user_optional DI → 토큰 없으면 None (하위 호환)
```

## 3. 주요 결정사항

| 결정 | 선택 | 대안 | 근거 |
|------|------|------|------|
| 인증 방식 | JWT (self-hosted) | OAuth2 (Google/GitHub), Session-based | 외부 의존 없음, 자체 제어 가능 |
| JWT 라이브러리 | python-jose[cryptography] | PyJWT | JOSE 표준, JWK 지원 |
| 패스워드 해싱 | passlib[bcrypt] | argon2 | 검증된 기본값, 라이브러리 성숙도 |
| Refresh token 저장 | DB (user_sessions) | Redis, Cookie-only | DB 기반 revocation 가능 |
| Refresh rotation | 매 갱신 시 새 token 발급 | 고정 token | 탈취 감지 가능 |
| Frontend 상태 | Zustand authStore | Context API, Redux | 가볍고 충분, Post-MVP 전체 공유 |
| 기존 API 호환 | optional auth (None 허용) | 전체 필수화 | MVP 기능 보존, 점진적 전환 |
| access token TTL | 30분 | 15분, 1시간 | 보안/UX 균형 |
| refresh token TTL | 7일 | 30일 | 개인 프로젝트 수준 적절 |

## 4. 컨벤션 체크리스트

### 기존 컨벤션 (Phase A에서도 준수)
- [x] Router → Service → Repository 3계층 구조
- [x] Pydantic v2 스키마 (`ConfigDict(from_attributes=True)`)
- [x] Repository: 함수형 모듈 (클래스 없음)
- [x] DI: `Depends(get_db)` 패턴 확장
- [x] `Mapped[]` + `mapped_column()` (SQLAlchemy 2.0)
- [x] 인코딩: utf-8 explicit
- [x] 환경변수 하드코딩 금지 (.env + Settings)

### Phase A 신규 컨벤션
- [ ] JWT secret: Settings.jwt_secret_key (환경변수)
- [ ] password 평문 로깅 금지
- [ ] refresh token DB 저장 시 hash only (평문 저장 금지)
- [ ] get_current_user: 401 Unauthorized (토큰 없음/만료/무효)
- [ ] get_current_user_optional: 토큰 없으면 None 반환 (기존 API용)
- [ ] CORS: `allow_headers`에 `Authorization` 포함 확인
- [ ] signup 이메일 중복: 409 Conflict
- [ ] login 실패: 401 Unauthorized (email/password 구분 안 함 — 보안)

### 파일 명명 규칙
| 유형 | 위치 | 파일명 |
|------|------|--------|
| 모델 | `db/models.py` | 기존 파일에 추가 |
| 스키마 | `api/schemas/auth.py` | 신규 |
| Repository | `api/repositories/user_repo.py` | 신규 |
| Repository | `api/repositories/session_repo.py` | 신규 |
| Service | `api/services/auth_service.py` | 신규 |
| Router | `api/routers/auth.py` | 신규 |
| Migration | `db/alembic/versions/xxx_add_auth_tables.py` | 자동 생성 |

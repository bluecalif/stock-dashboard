"""
## 용도
JWT Access Token + Refresh Token Rotation 인증 플로우.
회원가입, 로그인, 토큰 갱신, 회원 탈퇴. 복붙 후 시크릿/TTL 수정 필요.

## 언제 쓰는가
외부 인증 서비스(Auth0, Supabase Auth) 없이 JWT 인증을 자체 구현할 때.
Refresh Token Rotation으로 토큰 탈취 시 피해를 최소화해야 할 때.

## 전제조건
- PostgreSQL (또는 Refresh Token 해시를 저장할 RDB)
- User, UserSession 테이블 (cascade-fk-models.py 참조)

## 의존성
- python-jose[cryptography]: JWT 인코딩/디코딩
- bcrypt: 비밀번호 해싱
- settings: jwt_secret_key, jwt_algorithm, access_token_expire_minutes, refresh_token_expire_days

## 통합 포인트
- Service 계층 (auth_service.py)에 배치
- Router에서 signup/login/refresh/withdraw 엔드포인트로 노출
- fastapi-dependency-injection.py의 get_current_user에서 decode_access_token 호출

## 주의사항
- Refresh Token은 평문이 아닌 SHA256 해시만 DB에 저장할 것
- Rotation 시 이전 세션은 반드시 삭제 (재사용 공격 방지)
- jwt_secret_key는 환경변수로 관리, 코드에 하드코딩 금지

## 출처
stock-dashboard/backend/api/services/auth_service.py
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

import bcrypt
from jose import JWTError, jwt


# --- Password ---

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# --- Token ---

def _hash_token(token: str) -> str:
    """Refresh token은 SHA256 해시만 DB에 저장."""
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(user_id: UUID, secret_key: str, algorithm: str, expire_minutes: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=expire_minutes)
    payload = {"sub": str(user_id), "exp": expire, "type": "access"}
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def decode_access_token(token: str, secret_key: str, algorithm: str) -> UUID:
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        user_id_str = payload.get("sub")
        token_type = payload.get("type")
        if user_id_str is None or token_type != "access":
            raise ValueError("Invalid token")
        return UUID(user_id_str)
    except JWTError:
        raise ValueError("Invalid or expired token")


def _create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


# --- Service ---
# signup, login, refresh, withdraw 함수는
# user_repo.create_user, user_repo.get_by_email, session_repo.create_session 등을 조합.
# Refresh Token Rotation: 갱신 시 이전 세션 삭제 → 신규 생성.
# Withdraw: 비밀번호 재확인 후 user 삭제 (CASCADE FK로 관련 데이터 자동 정리).

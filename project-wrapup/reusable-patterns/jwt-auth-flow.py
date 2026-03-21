"""
## 용도
JWT Access Token + Refresh Token Rotation 인증 플로우.
회원가입, 로그인, 토큰 갱신, 회원 탈퇴.

## 사용법
1. settings에 jwt_secret_key, jwt_algorithm, access_token_expire_minutes, refresh_token_expire_days 설정
2. user_repo, session_repo 구현 (아래 인터페이스 참조)
3. 각 함수를 FastAPI 라우터에서 호출

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

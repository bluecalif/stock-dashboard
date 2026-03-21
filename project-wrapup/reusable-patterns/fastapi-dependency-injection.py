"""
## 용도
FastAPI 의존성 주입 — DB 세션 관리, JWT 인증, 선택적 인증.

## 사용법
1. get_db: 모든 DB 접근 엔드포인트에 Depends(get_db)
2. get_current_user: 인증 필수 엔드포인트에 Depends(get_current_user)
3. get_current_user_optional: 인증 선택 엔드포인트에 사용

## 출처
stock-dashboard/backend/api/dependencies.py
"""

from typing import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

# --- OAuth2 Scheme ---
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)


# --- DB Session (Generator 패턴) ---
def get_db() -> Generator[Session, None, None]:
    # SessionLocal이 None이면 503 반환 (DB 미설정 시)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 인증 필수 ---
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    user_id = decode_access_token(token)  # JWTError → 401
    user = user_repo.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or deactivated")
    return user


# --- 인증 선택 (토큰 없으면 None) ---
def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
):
    if not token:
        return None
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None

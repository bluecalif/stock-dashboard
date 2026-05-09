"""
## 용도
FastAPI 의존성 주입 — DB 세션 관리, JWT 인증(필수/선택).
Generator 패턴으로 세션 라이프사이클 자동 관리.

## 언제 쓰는가
FastAPI 프로젝트에서 DB 세션과 인증을 DI로 관리할 때.
일부 엔드포인트는 인증 필수, 일부는 선택(비로그인 허용)일 때.

## 전제조건
- FastAPI 앱 + SQLAlchemy SessionLocal 설정 완료
- JWT 토큰 발급/검증 함수 (jwt-auth-flow.py 참조)

## 의존성
- fastapi: Depends, HTTPException, OAuth2PasswordBearer
- sqlalchemy.orm: Session

## 통합 포인트
- dependencies.py에 배치
- 모든 Router에서 Depends(get_db), Depends(get_current_user) 사용
- 주의: 백그라운드 태스크에 get_db 세션 전달 금지 (T-003)

## 주의사항
- get_db 세션은 요청 스코프. 백그라운드 태스크에는 자체 SessionLocal() 생성 필수
- auto_error=False로 설정한 optional 스킴에서는 토큰 없으면 None 반환
- 헬스체크 엔드포인트는 get_db DI 없이 직접 DB 접근 권장

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

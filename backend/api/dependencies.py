"""FastAPI dependency injection — DB session, auth."""

from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db.models import User
from db.session import SessionLocal

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=True)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Yield a SQLAlchemy session and ensure it is closed after use."""
    if SessionLocal is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database not configured (DATABASE_URL missing)",
        )
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Decode JWT and return the User. Raises 401 on failure."""
    from api.services.auth_service import decode_access_token

    user_id = decode_access_token(token)
    from api.repositories import user_repo

    user = user_repo.get_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated",
        )
    return user


def get_current_user_optional(
    token: str | None = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
) -> User | None:
    """Return User if token present and valid, else None (기존 API 하위 호환)."""
    if not token:
        return None
    try:
        return get_current_user(token=token, db=db)
    except HTTPException:
        return None

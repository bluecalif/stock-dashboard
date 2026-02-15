"""FastAPI dependency injection — DB session management."""

from collections.abc import Generator

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from db.session import SessionLocal


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

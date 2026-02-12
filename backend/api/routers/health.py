"""Health check endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_db

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Check API and database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {"status": "ok", "db": db_status}

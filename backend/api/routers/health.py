"""Health check endpoints."""

from fastapi import APIRouter, Depends, Response
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.dependencies import get_db

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health")
def health_check(response: Response, db: Session = Depends(get_db)):
    """Railway healthcheck. Returns 503 when DB is unreachable."""
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        response.status_code = 503
        return {"status": "error", "db": "disconnected"}


@router.get("/ready")
def readiness_check(db: Session = Depends(get_db)):
    """Diagnostic endpoint. Always returns 200 with DB status detail."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    return {"status": "ok", "db": db_status}

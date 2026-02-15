"""Health check endpoints."""

from fastapi import APIRouter, Response
from sqlalchemy import text

from config.settings import settings
from db.session import SessionLocal

router = APIRouter(prefix="/v1", tags=["health"])


@router.get("/health")
def health_check():
    """Railway healthcheck. Always 200 (liveness). Reports DB status in body."""
    db_status = "not_configured"
    if SessionLocal is not None:
        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            db_status = "connected"
        except Exception:
            db_status = "disconnected"
        finally:
            db.close()
    return {"status": "ok", "db": db_status}


@router.get("/debug/cors")
def debug_cors():
    """Temporary: show CORS config for debugging. Remove after verification."""
    return {
        "cors_origins_env": settings.cors_origins,
        "cors_origins_parsed": [o.strip() for o in settings.cors_origins.split(",") if o.strip()] if settings.cors_origins else [],
    }


@router.get("/ready")
def readiness_check():
    """Readiness probe. Returns 503 when DB is unreachable."""
    if SessionLocal is None:
        return Response(
            content='{"status":"error","db":"not_configured"}',
            status_code=503,
            media_type="application/json",
        )
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception:
        return Response(
            content='{"status":"error","db":"disconnected"}',
            status_code=503,
            media_type="application/json",
        )
    finally:
        db.close()

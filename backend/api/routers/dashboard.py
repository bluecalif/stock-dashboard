"""Dashboard endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.dashboard import DashboardSummaryResponse
from api.services.dashboard_service import get_dashboard_summary

router = APIRouter(prefix="/v1", tags=["dashboard"])


@router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def dashboard_summary(
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    """Return dashboard summary: per-asset latest info + recent backtests."""
    return get_dashboard_summary(db)

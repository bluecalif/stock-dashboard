"""Asset endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.repositories import asset_repo
from api.schemas.asset import AssetResponse

router = APIRouter(prefix="/v1", tags=["assets"])


@router.get("/assets", response_model=list[AssetResponse])
def list_assets(
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    db: Session = Depends(get_db),
) -> list[AssetResponse]:
    """Return all assets, optionally filtered by is_active."""
    rows = asset_repo.get_all(db, is_active=is_active)
    return [AssetResponse.model_validate(r) for r in rows]

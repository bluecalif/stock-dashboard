"""Asset master repository."""

from __future__ import annotations

from sqlalchemy.orm import Session

from db.models import AssetMaster


def get_all(db: Session, *, is_active: bool | None = None) -> list[AssetMaster]:
    """Return all assets, optionally filtered by is_active."""
    query = db.query(AssetMaster)
    if is_active is not None:
        query = query.filter(AssetMaster.is_active == is_active)
    return query.order_by(AssetMaster.asset_id).all()

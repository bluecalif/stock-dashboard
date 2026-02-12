"""Price daily repository."""

from __future__ import annotations

import datetime

from sqlalchemy.orm import Session

from db.models import PriceDaily


def _apply_date_filter(query, start_date: datetime.date | None, end_date: datetime.date | None):
    if start_date:
        query = query.filter(PriceDaily.date >= start_date)
    if end_date:
        query = query.filter(PriceDaily.date <= end_date)
    return query


def get_prices(
    db: Session,
    asset_id: str,
    *,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[PriceDaily]:
    """Return price records for an asset with date filter and pagination."""
    query = db.query(PriceDaily).filter(PriceDaily.asset_id == asset_id)
    query = _apply_date_filter(query, start_date, end_date)
    return query.order_by(PriceDaily.date.desc()).offset(offset).limit(limit).all()


def get_latest_price(db: Session, asset_id: str) -> PriceDaily | None:
    """Return the most recent price record for an asset."""
    return (
        db.query(PriceDaily)
        .filter(PriceDaily.asset_id == asset_id)
        .order_by(PriceDaily.date.desc())
        .first()
    )

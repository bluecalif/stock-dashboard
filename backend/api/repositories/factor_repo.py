"""Factor daily repository."""

from __future__ import annotations

import datetime

from sqlalchemy.orm import Session

from db.models import FactorDaily


def get_factors(
    db: Session,
    *,
    asset_id: str | None = None,
    factor_name: str | None = None,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[FactorDaily]:
    """Return factor records with optional filters and pagination."""
    query = db.query(FactorDaily)
    if asset_id is not None:
        query = query.filter(FactorDaily.asset_id == asset_id)
    if factor_name is not None:
        query = query.filter(FactorDaily.factor_name == factor_name)
    if start_date:
        query = query.filter(FactorDaily.date >= start_date)
    if end_date:
        query = query.filter(FactorDaily.date <= end_date)
    return query.order_by(FactorDaily.date.desc()).offset(offset).limit(limit).all()

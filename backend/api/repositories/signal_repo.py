"""Signal daily repository."""

from __future__ import annotations

import datetime

from sqlalchemy.orm import Session

from db.models import SignalDaily


def get_signals(
    db: Session,
    *,
    asset_id: str | None = None,
    strategy_id: str | None = None,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[SignalDaily]:
    """Return signal records with optional filters and pagination."""
    query = db.query(SignalDaily)
    if asset_id is not None:
        query = query.filter(SignalDaily.asset_id == asset_id)
    if strategy_id is not None:
        query = query.filter(SignalDaily.strategy_id == strategy_id)
    if start_date:
        query = query.filter(SignalDaily.date >= start_date)
    if end_date:
        query = query.filter(SignalDaily.date <= end_date)
    return query.order_by(SignalDaily.date.desc()).offset(offset).limit(limit).all()


def get_latest_signal(
    db: Session, asset_id: str, *, strategy_id: str | None = None
) -> SignalDaily | None:
    """Return the most recent signal for an asset, optionally filtered by strategy."""
    query = (
        db.query(SignalDaily)
        .filter(SignalDaily.asset_id == asset_id)
    )
    if strategy_id is not None:
        query = query.filter(SignalDaily.strategy_id == strategy_id)
    return query.order_by(SignalDaily.date.desc()).first()

"""Backtest repository (runs, equity curves, trade logs)."""

from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from db.models import BacktestEquityCurve, BacktestRun, BacktestTradeLog


def get_runs(
    db: Session,
    *,
    strategy_id: str | None = None,
    asset_id: str | None = None,
    limit: int = 500,
    offset: int = 0,
) -> list[BacktestRun]:
    """Return backtest runs with optional filters and pagination."""
    query = db.query(BacktestRun)
    if strategy_id is not None:
        query = query.filter(BacktestRun.strategy_id == strategy_id)
    if asset_id is not None:
        query = query.filter(BacktestRun.asset_id == asset_id)
    return query.order_by(BacktestRun.started_at.desc()).offset(offset).limit(limit).all()


def get_run_by_id(db: Session, run_id: uuid.UUID) -> BacktestRun | None:
    """Return a single backtest run by ID."""
    return db.query(BacktestRun).filter(BacktestRun.run_id == run_id).first()


def get_equity_curve(db: Session, run_id: uuid.UUID) -> list[BacktestEquityCurve]:
    """Return equity curve records for a backtest run."""
    return (
        db.query(BacktestEquityCurve)
        .filter(BacktestEquityCurve.run_id == run_id)
        .order_by(BacktestEquityCurve.date.asc())
        .all()
    )


def get_trades(db: Session, run_id: uuid.UUID) -> list[BacktestTradeLog]:
    """Return trade log records for a backtest run."""
    return (
        db.query(BacktestTradeLog)
        .filter(BacktestTradeLog.run_id == run_id)
        .order_by(BacktestTradeLog.entry_date.asc())
        .all()
    )


def create_run(db: Session, run: BacktestRun) -> BacktestRun:
    """Insert a new backtest run and return it."""
    db.add(run)
    db.flush()
    return run


def bulk_insert_equity(db: Session, records: list[BacktestEquityCurve]) -> None:
    """Bulk insert equity curve records."""
    db.add_all(records)
    db.flush()


def bulk_insert_trades(db: Session, records: list[BacktestTradeLog]) -> None:
    """Bulk insert trade log records."""
    db.add_all(records)
    db.flush()

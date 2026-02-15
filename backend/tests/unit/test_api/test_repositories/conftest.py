"""Shared fixtures for repository tests — SQLite in-memory DB."""

import datetime
import uuid

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from db.models import (
    AssetMaster,
    BacktestEquityCurve,
    BacktestRun,
    BacktestTradeLog,
    Base,
    FactorDaily,
    PriceDaily,
    SignalDaily,
)


@pytest.fixture()
def db():
    """Yield a SQLAlchemy session backed by SQLite in-memory."""
    engine = create_engine("sqlite:///:memory:")

    # SQLite doesn't have native UUID — store as string via text affinity (works automatically).
    # Render PostgreSQL UUID columns as TEXT for SQLite.
    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


# ── Seed helpers ──

@pytest.fixture()
def seed_assets(db):
    """Insert 3 assets (2 active, 1 inactive)."""
    assets = [
        AssetMaster(
            asset_id="KS200", name="KOSPI200", category="index",
            source_priority=["fdr"], is_active=True,
        ),
        AssetMaster(
            asset_id="005930", name="삼성전자", category="stock",
            source_priority=["fdr"], is_active=True,
        ),
        AssetMaster(
            asset_id="INACTIVE", name="Inactive", category="test",
            source_priority=["fdr"], is_active=False,
        ),
    ]
    db.add_all(assets)
    db.commit()
    return assets


@pytest.fixture()
def seed_prices(db, seed_assets):
    """Insert 5 price rows for KS200."""
    base = datetime.date(2026, 1, 5)
    rows = []
    for i in range(5):
        rows.append(PriceDaily(
            asset_id="KS200",
            date=base + datetime.timedelta(days=i),
            source="fdr",
            open=100.0 + i,
            high=105.0 + i,
            low=98.0 + i,
            close=103.0 + i,
            volume=50000 + i * 1000,
        ))
    db.add_all(rows)
    db.commit()
    return rows


@pytest.fixture()
def seed_factors(db, seed_assets):
    """Insert 4 factor rows."""
    base = datetime.date(2026, 1, 5)
    rows = []
    for i in range(4):
        rows.append(FactorDaily(
            asset_id="KS200",
            date=base + datetime.timedelta(days=i),
            factor_name="momentum_20d",
            version="v1",
            value=0.5 + i * 0.1,
        ))
    db.add_all(rows)
    db.commit()
    return rows


@pytest.fixture()
def seed_signals(db, seed_assets):
    """Insert 4 signal rows (2 strategies)."""
    base = datetime.date(2026, 1, 5)
    d1 = base + datetime.timedelta(days=1)
    rows = [
        SignalDaily(asset_id="KS200", date=base, strategy_id="mom_20", signal=1, score=0.8),
        SignalDaily(asset_id="KS200", date=d1, strategy_id="mom_20", signal=-1, score=0.3),
        SignalDaily(asset_id="KS200", date=base, strategy_id="trend_60", signal=1, score=0.9),
        SignalDaily(asset_id="KS200", date=d1, strategy_id="trend_60", signal=0, score=0.5),
    ]
    db.add_all(rows)
    db.commit()
    return rows


@pytest.fixture()
def seed_backtest(db, seed_assets):
    """Insert a backtest run with equity curve and trades."""
    run_id = uuid.uuid4()
    run = BacktestRun(
        run_id=run_id,
        strategy_id="mom_20",
        asset_id="KS200",
        config_json={"window": 20},
        metrics_json={"sharpe": 1.5},
        started_at=datetime.datetime(2026, 1, 10, 9, 0, tzinfo=datetime.timezone.utc),
        ended_at=datetime.datetime(2026, 1, 10, 9, 5, tzinfo=datetime.timezone.utc),
        status="completed",
    )
    db.add(run)

    base = datetime.date(2026, 1, 5)
    equity = [
        BacktestEquityCurve(
            run_id=run_id, date=base + datetime.timedelta(days=i),
            equity=10000 + i * 100, drawdown=0.0,
        )
        for i in range(3)
    ]
    db.add_all(equity)

    trades = [
        BacktestTradeLog(
            run_id=run_id, asset_id="KS200",
            entry_date=base, entry_price=100.0,
            exit_date=base + datetime.timedelta(days=2), exit_price=105.0,
            side="long", shares=10, pnl=50.0, cost=1.0,
        ),
    ]
    db.add_all(trades)
    db.commit()
    return run

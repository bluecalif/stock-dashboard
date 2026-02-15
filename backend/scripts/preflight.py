"""Pre-deployment preflight check — validates environment, DB, seeds, and data."""

import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure backend/ is on sys.path when running as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, inspect, func, select, text
from sqlalchemy.orm import Session

from config.settings import settings
from db.models import (
    AssetMaster,
    BacktestEquityCurve,
    BacktestRun,
    BacktestTradeLog,
    FactorDaily,
    JobRun,
    PriceDaily,
    SignalDaily,
)

# 7 expected seed assets
EXPECTED_ASSETS = {"KS200", "005930", "000660", "SOXL", "BTC", "GC=F", "SI=F"}

EXPECTED_TABLES = [
    "asset_master",
    "price_daily",
    "factor_daily",
    "signal_daily",
    "backtest_run",
    "backtest_equity_curve",
    "backtest_trade_log",
    "job_run",
]


class PreflightResult:
    """Accumulates check results."""

    def __init__(self):
        self.checks: list[dict] = []

    def add(self, name: str, ok: bool, detail: str = ""):
        status = "PASS" if ok else "FAIL"
        self.checks.append({"name": name, "status": status, "detail": detail})

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c["status"] == "PASS")

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if c["status"] == "FAIL")

    @property
    def all_passed(self) -> bool:
        return self.failed == 0

    def print_report(self):
        print(f"\nPreflight Check ({date.today().isoformat()})")
        print("=" * 60)
        for c in self.checks:
            marker = "PASS" if c["status"] == "PASS" else "FAIL"
            detail = f"  - {c['detail']}" if c["detail"] else ""
            print(f"  [{marker}] {c['name']}{detail}")
        print("=" * 60)
        print(f"  {self.passed} passed, {self.failed} failed")


def check_env(result: PreflightResult):
    """Check DATABASE_URL is set."""
    url = settings.database_url
    has_url = bool(url)
    masked = f"{url[:20]}...{url[-10:]}" if len(url) > 35 else "(empty)"
    result.add("DATABASE_URL configured", has_url, masked if has_url else "Not set")


def check_db_connection(result: PreflightResult) -> object | None:
    """Try to connect to DB. Returns engine on success."""
    if not settings.database_url:
        result.add("DB connection", False, "No DATABASE_URL")
        return None
    try:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result.add("DB connection", True, "Connected")
        return engine
    except Exception as e:
        result.add("DB connection", False, str(e)[:100])
        return None


def check_tables(engine, result: PreflightResult):
    """Check all 8 required tables exist."""
    inspector = inspect(engine)
    existing = set(inspector.get_table_names())
    for table in EXPECTED_TABLES:
        found = table in existing
        result.add(f"Table: {table}", found, "exists" if found else "MISSING")


def check_seeds(engine, result: PreflightResult):
    """Check 7 seed assets exist in asset_master."""
    with Session(engine) as session:
        rows = session.execute(select(AssetMaster.asset_id)).scalars().all()
        existing = set(rows)

    for asset_id in sorted(EXPECTED_ASSETS):
        found = asset_id in existing
        result.add(f"Seed: {asset_id}", found, "found" if found else "MISSING")


def check_recent_data(engine, result: PreflightResult):
    """Check price_daily has data within last 7 days for at least 1 asset."""
    cutoff = date.today() - timedelta(days=7)
    with Session(engine) as session:
        count = session.execute(
            select(func.count())
            .select_from(PriceDaily)
            .where(PriceDaily.date >= cutoff)
        ).scalar()
        has_data = count > 0
        result.add(
            "Recent price data (7 days)",
            has_data,
            f"{count} rows since {cutoff.isoformat()}" if has_data else "No recent data",
        )


def main():
    result = PreflightResult()

    # 1. Environment
    check_env(result)

    # 2. DB Connection
    engine = check_db_connection(result)

    if engine is None:
        result.print_report()
        sys.exit(1)

    # 3. Tables
    check_tables(engine, result)

    # 4. Seeds
    check_seeds(engine, result)

    # 5. Recent data
    check_recent_data(engine, result)

    result.print_report()
    sys.exit(0 if result.all_passed else 1)


if __name__ == "__main__":
    main()

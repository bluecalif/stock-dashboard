"""Data freshness check — verifies each asset has recent price data."""

import sys
from datetime import date, timedelta
from pathlib import Path

# Ensure backend/ is on sys.path when running as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import func, select

from collector.alerting import send_discord_alert
from config.logging import setup_logging
from config.settings import settings
from db.models import AssetMaster, PriceDaily
from db.session import SessionLocal

# Categories that trade every calendar day (no weekends off)
DAILY_CATEGORIES = {"crypto"}


def previous_business_day(ref: date) -> date:
    """Return the most recent business day on or before ref - 1 day."""
    d = ref - timedelta(days=1)
    # Monday=0 ... Sunday=6
    while d.weekday() >= 5:  # Saturday or Sunday
        d -= timedelta(days=1)
    return d


def expected_latest_date(category: str, today: date | None = None) -> date:
    """Return the expected latest data date for an asset category.

    - crypto: yesterday (trades every day)
    - others: previous business day
    """
    today = today or date.today()
    if category in DAILY_CATEGORIES:
        return today - timedelta(days=1)
    return previous_business_day(today)


def check_freshness(session, today: date | None = None) -> list[dict]:
    """Check data freshness for all active assets.

    Returns a list of dicts with keys:
        asset_id, name, category, expected_date, actual_date, status
    """
    today = today or date.today()

    # Subquery: max date per asset
    max_date_sq = (
        select(
            PriceDaily.asset_id,
            func.max(PriceDaily.date).label("max_date"),
        )
        .group_by(PriceDaily.asset_id)
        .subquery()
    )

    # Join with asset_master for active assets
    stmt = (
        select(
            AssetMaster.asset_id,
            AssetMaster.name,
            AssetMaster.category,
            max_date_sq.c.max_date,
        )
        .outerjoin(max_date_sq, AssetMaster.asset_id == max_date_sq.c.asset_id)
        .where(AssetMaster.is_active.is_(True))
        .order_by(AssetMaster.asset_id)
    )

    rows = session.execute(stmt).all()
    results = []

    for asset_id, name, category, actual_date in rows:
        expected = expected_latest_date(category, today)
        if actual_date is None:
            status = "NO_DATA"
        elif actual_date >= expected:
            status = "OK"
        else:
            status = "STALE"

        results.append({
            "asset_id": asset_id,
            "name": name,
            "category": category,
            "expected_date": expected.isoformat(),
            "actual_date": actual_date.isoformat() if actual_date else None,
            "status": status,
        })

    return results


def format_healthcheck_message(results: list[dict]) -> str:
    """Format stale/missing assets into a Discord alert message."""
    problems = [r for r in results if r["status"] != "OK"]
    lines = [
        f"**[Stock Dashboard] 데이터 신선도 경고** ({len(problems)}건)",
        "",
    ]
    for r in problems:
        actual = r["actual_date"] or "없음"
        lines.append(
            f"- {r['asset_id']} ({r['name']}): "
            f"최신 {actual}, 기대 {r['expected_date']} → **{r['status']}**"
        )
    return "\n".join(lines)


def main():
    setup_logging(settings.log_level)

    if SessionLocal is None:
        print("ERROR: DATABASE_URL not configured.", file=sys.stderr)
        sys.exit(1)

    session = SessionLocal()
    try:
        results = check_freshness(session)
    finally:
        session.close()

    # Print summary
    ok = [r for r in results if r["status"] == "OK"]
    problems = [r for r in results if r["status"] != "OK"]

    print(f"\nData Freshness Check ({date.today().isoformat()})")
    print("=" * 55)

    for r in results:
        marker = "OK" if r["status"] == "OK" else r["status"]
        actual = r["actual_date"] or "N/A"
        print(f"  {r['asset_id']:>8s}  {actual}  (expected {r['expected_date']})  [{marker}]")

    print("=" * 55)
    print(f"  {len(ok)} OK, {len(problems)} problem(s)")

    # Discord alert if any problems
    if problems:
        msg = format_healthcheck_message(results)
        send_discord_alert(settings.alert_webhook_url, msg)
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()

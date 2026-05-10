"""Silver Phase 1 backfill 스크립트 (P1-4).

신규 8자산 10년 일봉 + USD/KRW 10년 fx_daily 적재.
"""

import logging
import sys
from datetime import date, timedelta

sys.path.insert(0, ".")

from collector.fx_collector import run as fx_run
from collector.ingest import ingest_asset
from db.session import SessionLocal

logging.basicConfig(level=logging.INFO, stream=sys.stdout, encoding="utf-8")
logger = logging.getLogger(__name__)

END = date.today().isoformat()
START = (date.today() - timedelta(days=365 * 10 + 3)).isoformat()

SILVER_ASSETS = ["QQQ", "SPY", "SCHD", "JEPI", "TLT", "NVDA", "GOOGL", "TSLA"]


def run_backfill():
    results = {}

    print(f"\n{'='*50}")
    print(f"Silver Phase 1 Backfill: {START} ~ {END}")
    print(f"{'='*50}\n")

    # 1. 8자산 일봉 backfill
    with SessionLocal() as session:
        for asset in SILVER_ASSETS:
            print(f"▶ {asset} backfill...")
            r = ingest_asset(asset, START, END, session=session)
            session.commit()
            results[asset] = {"status": r.status, "rows": r.row_count, "errors": r.errors}
            print(f"  → {r.status}: {r.row_count} rows")

    # 2. USD/KRW 10년 fx_daily backfill
    print("\n▶ USD/KRW fx_daily backfill...")
    fx_result = fx_run(START, END)
    results["USD/KRW"] = fx_result
    print(f"  → {fx_result['status']}: {fx_result['rows']} rows")

    # 3. 결과 요약
    print(f"\n{'='*50}")
    print("결과 요약")
    print(f"{'='*50}")
    for k, v in results.items():
        status = v.get("status", "?")
        rows = v.get("rows", 0)
        icon = "✅" if status == "success" else "❌"
        print(f"  {icon} {k:10s}: {rows:5d} rows  [{status}]")

    return results


if __name__ == "__main__":
    run_backfill()

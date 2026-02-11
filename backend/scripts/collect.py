"""CLI script for OHLCV data collection via FDR."""

import argparse
import sys
import time
from pathlib import Path

# Ensure backend/ is on sys.path when running as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from collector.ingest import ingest_all, ingest_asset
from config.logging import setup_logging
from config.settings import settings
from db.session import SessionLocal


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Collect OHLCV data for registered assets")
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--assets",
        default=None,
        help="Comma-separated asset IDs (e.g. KS200,005930). Default: all active assets",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    setup_logging(settings.log_level)

    if SessionLocal is None:
        print("ERROR: DATABASE_URL not configured. Set it in .env or environment.", file=sys.stderr)
        sys.exit(1)

    session = SessionLocal()
    t0 = time.perf_counter()

    try:
        if args.assets:
            asset_ids = [a.strip() for a in args.assets.split(",")]
            results = []
            for asset_id in asset_ids:
                result = ingest_asset(asset_id, args.start, args.end, session)
                results.append(result)
        else:
            results = ingest_all(args.start, args.end, session)
    finally:
        session.close()

    elapsed = time.perf_counter() - t0

    # Summary
    success = [r for r in results if r.status == "success"]
    failed = [r for r in results if r.status != "success"]
    total_rows = sum(r.row_count for r in success)

    print(f"\n{'='*50}")
    print(f"Collection complete: {len(success)}/{len(results)} assets succeeded")
    print(f"Total rows: {total_rows:,}")
    print(f"Elapsed: {elapsed:.1f}s")

    if failed:
        print(f"\nFailed ({len(failed)}):")
        for r in failed:
            print(f"  - {r.asset_id}: {r.status} - {r.errors}")

    if success:
        print(f"\nSucceeded ({len(success)}):")
        for r in success:
            print(f"  - {r.asset_id}: {r.row_count} rows ({r.elapsed_ms:.0f}ms)")

    print(f"{'='*50}")

    # Exit code: 0 if all succeeded, 1 if any failed
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()

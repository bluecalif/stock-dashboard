"""CLI script for research pipeline: factors → signals → backtest → metrics → DB store."""

import argparse
import sys
import time
from pathlib import Path

# Ensure backend/ is on sys.path when running as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.logging import setup_logging
from db.session import SessionLocal
from research_engine.backtest import BacktestConfig, run_backtest
from research_engine.backtest_store import store_backtest_result
from research_engine.factor_store import store_factors_for_asset
from research_engine.factors import compute_all_factors
from research_engine.metrics import compute_metrics, metrics_to_dict
from research_engine.preprocessing import preprocess
from research_engine.signal_store import store_signals_for_asset
from research_engine.strategies import STRATEGY_REGISTRY


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run research pipeline: factors → signals → backtest → metrics → DB"
    )
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    parser.add_argument(
        "--assets",
        default=None,
        help="Comma-separated asset IDs (e.g. KS200,005930). Default: all active assets",
    )
    parser.add_argument(
        "--strategy",
        default=None,
        help=(
            f"Comma-separated strategy names. "
            f"Available: {','.join(STRATEGY_REGISTRY.keys())}. Default: all"
        ),
    )
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=10_000_000,
        help="Initial cash for backtest (default: 10,000,000)",
    )
    parser.add_argument(
        "--skip-backtest",
        action="store_true",
        help="Skip backtest (only compute factors and signals)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log level (default: INFO)",
    )
    return parser.parse_args(argv)


def _resolve_asset_ids(session, assets_arg: str | None) -> list[str]:
    """Resolve asset IDs from CLI arg or query active assets from DB."""
    if assets_arg:
        return [a.strip() for a in assets_arg.split(",")]

    from db.models import AssetMaster

    try:
        assets = session.query(AssetMaster).filter(AssetMaster.is_active.is_(True)).all()
        return [a.asset_id for a in assets]
    except Exception:
        from collector.fdr_client import SYMBOL_MAP

        return list(SYMBOL_MAP.keys())


def _resolve_strategy_names(strategy_arg: str | None) -> list[str]:
    """Resolve strategy names from CLI arg or use all registered."""
    if strategy_arg:
        names = [s.strip() for s in strategy_arg.split(",")]
        for name in names:
            if name not in STRATEGY_REGISTRY:
                print(
                    f"ERROR: Unknown strategy '{name}'. "
                    f"Available: {list(STRATEGY_REGISTRY.keys())}",
                    file=sys.stderr,
                )
                sys.exit(1)
        return names
    return list(STRATEGY_REGISTRY.keys())


def run_pipeline(session, asset_ids, strategy_names, start, end, config, skip_backtest=False):
    """Run the full research pipeline and return summary dict."""
    summary = {
        "assets": {},
        "total_factor_rows": 0,
        "total_signal_rows": 0,
        "total_backtest_runs": 0,
        "errors": [],
    }

    for asset_id in asset_ids:
        asset_summary = {"factors": None, "signals": {}, "backtests": {}}

        # Step 1: Preprocess + Factors → DB
        print(f"\n--- {asset_id}: Computing factors ---")
        factor_result = store_factors_for_asset(
            session, asset_id, start, end, missing_threshold=0.10,
        )
        asset_summary["factors"] = factor_result.status
        if factor_result.status != "success":
            summary["errors"].append(f"{asset_id}/factors: {factor_result.errors}")
            summary["assets"][asset_id] = asset_summary
            continue
        summary["total_factor_rows"] += factor_result.row_count
        print(f"  Factors: {factor_result.row_count} rows ({factor_result.elapsed_ms:.0f}ms)")

        # Need preprocessed df and factors df for signals + backtest
        df_preprocessed = preprocess(session, asset_id, start, end, missing_threshold=0.10)
        df_factors = compute_all_factors(df_preprocessed)
        # Include close price for strategies that need it (e.g. mean_reversion)
        df_factors["close"] = df_preprocessed["close"]

        # Step 2: Signals → DB (per strategy)
        for strat_name in strategy_names:
            print(f"  --- {asset_id}/{strat_name}: Generating signals ---")
            sig_result = store_signals_for_asset(session, asset_id, strat_name, df_factors)
            asset_summary["signals"][strat_name] = sig_result.status
            if sig_result.status != "success":
                summary["errors"].append(
                    f"{asset_id}/{strat_name}/signals: {sig_result.errors}"
                )
                continue
            summary["total_signal_rows"] += sig_result.row_count
            print(
                f"    Signals: {sig_result.row_count} rows "
                f"(entry={sig_result.n_entry}, exit={sig_result.n_exit}, "
                f"{sig_result.elapsed_ms:.0f}ms)"
            )

            # Step 3: Backtest → Metrics → DB
            if skip_backtest:
                continue

            print(f"    --- {asset_id}/{strat_name}: Running backtest ---")
            from db.models import SignalDaily

            sig_rows = (
                session.query(SignalDaily)
                .filter(
                    SignalDaily.asset_id == asset_id,
                    SignalDaily.strategy_id == sig_result.strategy_id,
                )
                .all()
            )
            import pandas as pd

            signals_df = pd.DataFrame(
                [{"date": r.date, "signal": r.signal} for r in sig_rows]
            )

            if signals_df.empty:
                print("    No signals to backtest")
                continue

            bt_result = run_backtest(
                prices=df_preprocessed,
                signals=signals_df,
                asset_id=asset_id,
                strategy_id=sig_result.strategy_id,
                config=config,
            )

            if bt_result.equity_curve.empty:
                print("    Empty equity curve, skipping")
                continue

            metrics = compute_metrics(bt_result)
            store_result = store_backtest_result(session, bt_result, metrics)
            asset_summary["backtests"][strat_name] = {
                "status": store_result.status,
                "metrics": metrics_to_dict(metrics),
            }

            if store_result.status != "success":
                summary["errors"].append(
                    f"{asset_id}/{strat_name}/backtest: {store_result.errors}"
                )
            else:
                summary["total_backtest_runs"] += 1
                print(
                    f"    Backtest: CAGR={metrics.cagr:.2%}, "
                    f"MDD={metrics.mdd:.2%}, Sharpe={metrics.sharpe:.2f}, "
                    f"trades={metrics.num_trades} ({store_result.elapsed_ms:.0f}ms)"
                )

        summary["assets"][asset_id] = asset_summary

    return summary


def main(argv=None):
    args = parse_args(argv)
    setup_logging(args.log_level)

    if SessionLocal is None:
        print("ERROR: DATABASE_URL not configured. Set it in .env or environment.", file=sys.stderr)
        sys.exit(1)

    session = SessionLocal()
    t0 = time.perf_counter()

    try:
        asset_ids = _resolve_asset_ids(session, args.assets)
        strategy_names = _resolve_strategy_names(args.strategy)
        config = BacktestConfig(initial_cash=args.initial_cash)

        print(f"Research pipeline: {len(asset_ids)} assets × {len(strategy_names)} strategies")
        print(f"  Assets: {asset_ids}")
        print(f"  Strategies: {strategy_names}")
        print(f"  Period: {args.start} ~ {args.end}")
        if args.skip_backtest:
            print("  Backtest: SKIPPED")

        summary = run_pipeline(
            session, asset_ids, strategy_names, args.start, args.end,
            config, args.skip_backtest,
        )
    finally:
        session.close()

    elapsed = time.perf_counter() - t0

    # Print summary
    print(f"\n{'='*60}")
    print(f"Research pipeline complete ({elapsed:.1f}s)")
    print(f"  Factor rows: {summary['total_factor_rows']:,}")
    print(f"  Signal rows: {summary['total_signal_rows']:,}")
    print(f"  Backtest runs: {summary['total_backtest_runs']}")

    if summary["errors"]:
        print(f"\n  Errors ({len(summary['errors'])}):")
        for err in summary["errors"]:
            print(f"    - {err}")

    # Per-asset summary
    for asset_id, info in summary["assets"].items():
        status_icon = "OK" if info["factors"] == "success" else "FAIL"
        print(f"\n  [{status_icon}] {asset_id}:")
        print(f"    Factors: {info['factors']}")
        for strat, sig_status in info["signals"].items():
            bt_info = info["backtests"].get(strat, {})
            bt_status = bt_info.get("status", "skipped")
            metrics = bt_info.get("metrics", {})
            cagr = metrics.get("cagr")
            cagr_str = f" CAGR={cagr:.2%}" if cagr is not None else ""
            print(f"    {strat}: signals={sig_status}, backtest={bt_status}{cagr_str}")

    print(f"{'='*60}")

    has_errors = bool(summary["errors"])
    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()

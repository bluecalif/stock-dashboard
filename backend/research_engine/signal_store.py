"""Signal DB storage: generate signals and store into signal_daily table."""

import logging
import time
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from db.models import SignalDaily
from research_engine.strategies import STRATEGY_REGISTRY, get_strategy
from research_engine.strategies.base import SignalResult

logger = logging.getLogger(__name__)


@dataclass
class SignalStoreResult:
    asset_id: str
    strategy_id: str
    status: str  # "success" | "compute_failed" | "store_failed"
    row_count: int = 0
    n_entry: int = 0
    n_exit: int = 0
    errors: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


def _signal_result_to_records(
    asset_id: str,
    strategy_id: str,
    signal_result: SignalResult,
) -> list[dict]:
    """Convert SignalResult to list of dicts for signal_daily INSERT."""
    records = []
    for _, row in signal_result.signals.iterrows():
        date_val = row["date"]
        date_key = date_val.date() if hasattr(date_val, "date") else date_val
        records.append({
            "asset_id": asset_id,
            "date": date_key,
            "strategy_id": strategy_id,
            "signal": int(row["signal"]),
            "score": float(row["score"]) if row.get("score") is not None else None,
            "action": row.get("action"),
            "meta_json": row.get("meta_json"),
        })
    return records


def _delete_and_insert_signals(
    session: Session,
    asset_id: str,
    strategy_id: str,
    records: list[dict],
    chunk_size: int = 2000,
) -> int:
    """Delete existing signals and insert new ones (idempotent).

    Since signal_daily has no unique constraint (only an index),
    we DELETE existing rows for (asset_id, strategy_id) then INSERT.
    """
    # Delete existing signals for this asset + strategy
    session.query(SignalDaily).filter(
        SignalDaily.asset_id == asset_id,
        SignalDaily.strategy_id == strategy_id,
    ).delete(synchronize_session=False)

    # Insert in chunks
    total = 0
    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        session.bulk_insert_mappings(SignalDaily, chunk)
        total += len(chunk)

    session.flush()
    return total


def store_signals_for_asset(
    session: Session,
    asset_id: str,
    strategy_name: str,
    factors_df,
    **strategy_kwargs,
) -> SignalStoreResult:
    """Generate and store signals for a single asset + strategy.

    Args:
        session: SQLAlchemy session.
        asset_id: Asset identifier.
        strategy_name: Strategy name (momentum, trend, mean_reversion).
        factors_df: DataFrame with factor columns (from compute_all_factors).
        **strategy_kwargs: Parameters passed to the strategy constructor.

    Returns:
        SignalStoreResult with status and counts.
    """
    t0 = time.perf_counter()
    strategy = get_strategy(strategy_name, **strategy_kwargs)
    strategy_id = strategy.strategy_id

    # 1. Compute signals
    try:
        signal_result = strategy.generate_signals(factors_df, asset_id)
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error("Signal compute failed for %s/%s: %s", asset_id, strategy_id, e)
        return SignalStoreResult(
            asset_id=asset_id,
            strategy_id=strategy_id,
            status="compute_failed",
            errors=[str(e)],
            elapsed_ms=elapsed,
        )

    if signal_result.signals.empty:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.warning("No signals generated for %s/%s", asset_id, strategy_id)
        return SignalStoreResult(
            asset_id=asset_id,
            strategy_id=strategy_id,
            status="success",
            row_count=0,
            elapsed_ms=elapsed,
        )

    # 2. Convert and store
    try:
        records = _signal_result_to_records(asset_id, strategy_id, signal_result)
        row_count = _delete_and_insert_signals(session, asset_id, strategy_id, records)
        session.commit()
    except Exception as e:
        session.rollback()
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error("Signal store failed for %s/%s: %s", asset_id, strategy_id, e)
        return SignalStoreResult(
            asset_id=asset_id,
            strategy_id=strategy_id,
            status="store_failed",
            errors=[f"db_error: {e}"],
            elapsed_ms=elapsed,
        )

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info(
        "Stored %d signals for %s/%s (entry=%d, exit=%d) in %.0fms",
        row_count, asset_id, strategy_id,
        signal_result.n_entry, signal_result.n_exit, elapsed,
    )
    return SignalStoreResult(
        asset_id=asset_id,
        strategy_id=strategy_id,
        status="success",
        row_count=row_count,
        n_entry=signal_result.n_entry,
        n_exit=signal_result.n_exit,
        elapsed_ms=elapsed,
    )


def store_signals_all(
    session: Session,
    factors_by_asset: dict,
    strategy_names: list[str] | None = None,
    **strategy_kwargs,
) -> list[SignalStoreResult]:
    """Generate and store signals for all assets × all strategies.

    Args:
        session: SQLAlchemy session.
        factors_by_asset: Dict mapping asset_id → factors DataFrame.
        strategy_names: List of strategy names. If None, uses all registered.
        **strategy_kwargs: Passed to each strategy constructor.

    Returns:
        List of SignalStoreResult for each asset × strategy combination.
    """
    if strategy_names is None:
        strategy_names = list(STRATEGY_REGISTRY.keys())

    results: list[SignalStoreResult] = []
    for asset_id, factors_df in factors_by_asset.items():
        for strategy_name in strategy_names:
            result = store_signals_for_asset(
                session, asset_id, strategy_name, factors_df, **strategy_kwargs
            )
            results.append(result)

    success = sum(1 for r in results if r.status == "success")
    total = len(results)
    total_rows = sum(r.row_count for r in results)
    logger.info(
        "Signal store complete: %d/%d succeeded, %d total rows",
        success, total, total_rows,
    )
    return results

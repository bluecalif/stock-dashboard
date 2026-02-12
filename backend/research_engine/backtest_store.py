"""Backtest result DB storage: save run metadata, equity curve, and trade log."""

import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from db.models import BacktestEquityCurve, BacktestRun, BacktestTradeLog
from research_engine.backtest import BacktestResult
from research_engine.metrics import PerformanceMetrics, metrics_to_dict

logger = logging.getLogger(__name__)


@dataclass
class BacktestStoreResult:
    strategy_id: str
    asset_id: str
    status: str  # "success" | "store_failed"
    run_id: uuid.UUID | None = None
    row_count_equity: int = 0
    row_count_trades: int = 0
    errors: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


def _config_to_dict(config) -> dict:
    """Convert BacktestConfig to JSON-serializable dict."""
    return {
        "initial_cash": config.initial_cash,
        "commission_pct": config.commission_pct,
        "slippage_pct": config.slippage_pct,
        "allow_short": config.allow_short,
    }


def _equity_curve_to_records(run_id: uuid.UUID, equity_df) -> list[dict]:
    """Convert equity_curve DataFrame to list of dicts for bulk insert."""
    records = []
    for _, row in equity_df.iterrows():
        date_val = row["date"]
        date_key = date_val.date() if hasattr(date_val, "date") else date_val
        records.append({
            "run_id": run_id,
            "date": date_key,
            "equity": float(row["equity"]),
            "drawdown": float(row["drawdown"]),
        })
    return records


def _trades_to_records(run_id: uuid.UUID, trades: list) -> list[dict]:
    """Convert list of TradeRecord to list of dicts for bulk insert."""
    records = []
    for t in trades:
        records.append({
            "run_id": run_id,
            "asset_id": t.asset_id,
            "entry_date": t.entry_date,
            "entry_price": t.entry_price,
            "exit_date": t.exit_date,
            "exit_price": t.exit_price,
            "side": t.side,
            "shares": t.shares,
            "pnl": t.pnl,
            "cost": t.cost,
        })
    return records


def store_backtest_result(
    session: Session,
    result: BacktestResult,
    metrics: PerformanceMetrics,
) -> BacktestStoreResult:
    """Store a backtest result (run + equity curve + trade log) into DB.

    Args:
        session: SQLAlchemy session.
        result: BacktestResult from run_backtest / run_backtest_multi.
        metrics: PerformanceMetrics from compute_metrics.

    Returns:
        BacktestStoreResult with status and counts.
    """
    t0 = time.perf_counter()
    run_id = uuid.uuid4()

    try:
        # 1. Create backtest_run record
        now = datetime.now(timezone.utc)
        run = BacktestRun(
            run_id=run_id,
            strategy_id=result.strategy_id,
            asset_id=result.asset_id,
            config_json=_config_to_dict(result.config),
            metrics_json=metrics_to_dict(metrics),
            started_at=now,
            status="running",
        )
        session.add(run)
        session.flush()

        # 2. Insert equity curve
        equity_records = _equity_curve_to_records(run_id, result.equity_curve)
        if equity_records:
            session.bulk_insert_mappings(BacktestEquityCurve, equity_records)

        # 3. Insert trade log
        trade_records = _trades_to_records(run_id, result.trades)
        if trade_records:
            session.bulk_insert_mappings(BacktestTradeLog, trade_records)

        # 4. Update status to success
        run.status = "success"
        run.ended_at = datetime.now(timezone.utc)
        session.commit()

    except Exception as e:
        session.rollback()
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error(
            "Backtest store failed for %s/%s: %s",
            result.strategy_id, result.asset_id, e,
        )
        return BacktestStoreResult(
            strategy_id=result.strategy_id,
            asset_id=result.asset_id,
            status="store_failed",
            errors=[f"db_error: {e}"],
            elapsed_ms=elapsed,
        )

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info(
        "Stored backtest run %s for %s/%s (equity=%d, trades=%d) in %.0fms",
        run_id, result.strategy_id, result.asset_id,
        len(equity_records), len(trade_records), elapsed,
    )
    return BacktestStoreResult(
        strategy_id=result.strategy_id,
        asset_id=result.asset_id,
        status="success",
        run_id=run_id,
        row_count_equity=len(equity_records),
        row_count_trades=len(trade_records),
        elapsed_ms=elapsed,
    )

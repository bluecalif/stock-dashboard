"""Factor storage: compute factors and UPSERT to factor_daily table."""

import logging
import time
from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db.models import AssetMaster, FactorDaily
from research_engine.factors import (
    ALL_FACTOR_NAMES,
    FACTOR_VERSION,
    compute_all_factors,
)
from research_engine.preprocessing import preprocess

logger = logging.getLogger(__name__)


@dataclass
class FactorStoreResult:
    asset_id: str
    status: str  # "success" | "preprocess_failed" | "compute_failed" | "store_failed"
    row_count: int = 0
    errors: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


def _upsert_factors(session: Session, records: list[dict], chunk_size: int = 1000) -> int:
    """Upsert factor records into factor_daily using ON CONFLICT DO UPDATE.

    Conflict key: (asset_id, date, factor_name, version).
    Updated column: value.

    Returns total row count processed.
    """
    total = 0
    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        stmt = insert(FactorDaily).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=["asset_id", "date", "factor_name", "version"],
            set_={"value": stmt.excluded.value},
        )
        session.execute(stmt)
        total += len(chunk)

    session.flush()
    return total


def _factors_to_records(
    asset_id: str,
    factor_df: pd.DataFrame,
    version: str = FACTOR_VERSION,
) -> list[dict]:
    """Convert wide factor DataFrame to long-format records for DB insert.

    Skips NaN values (factor_daily.value is NOT NULL).
    """
    records = []
    for date_val, row in factor_df.iterrows():
        dt = date_val.date() if hasattr(date_val, "date") else date_val
        for factor_name in ALL_FACTOR_NAMES:
            if factor_name in row and pd.notna(row[factor_name]):
                records.append(
                    {
                        "asset_id": asset_id,
                        "date": dt,
                        "factor_name": factor_name,
                        "version": version,
                        "value": float(row[factor_name]),
                    }
                )
    return records


def compute_and_store_factors(
    session: Session,
    asset_id: str,
    start: str | None = None,
    end: str | None = None,
) -> FactorStoreResult:
    """Single asset factor pipeline: preprocess → compute → store.

    Args:
        session: SQLAlchemy session
        asset_id: Internal asset identifier
        start: Start date string (optional)
        end: End date string (optional)

    Returns:
        FactorStoreResult with status and details
    """
    t0 = time.perf_counter()
    logger.info("Computing factors for %s", asset_id)

    # 1. Preprocess
    try:
        price_df = preprocess(session, asset_id, start, end)
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error("Preprocess failed for %s: %s", asset_id, e)
        return FactorStoreResult(
            asset_id=asset_id,
            status="preprocess_failed",
            errors=[str(e)],
            elapsed_ms=elapsed,
        )

    # 2. Compute factors
    try:
        factor_df = compute_all_factors(price_df)
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error("Factor compute failed for %s: %s", asset_id, e)
        return FactorStoreResult(
            asset_id=asset_id,
            status="compute_failed",
            errors=[str(e)],
            elapsed_ms=elapsed,
        )

    # 3. Convert to records and store
    try:
        records = _factors_to_records(asset_id, factor_df)
        if records:
            row_count = _upsert_factors(session, records)
        else:
            row_count = 0
        session.commit()
    except Exception as e:
        session.rollback()
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error("Factor store failed for %s: %s", asset_id, e)
        return FactorStoreResult(
            asset_id=asset_id,
            status="store_failed",
            errors=[str(e)],
            elapsed_ms=elapsed,
        )

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("Stored %d factor rows for %s in %.0fms", row_count, asset_id, elapsed)
    return FactorStoreResult(
        asset_id=asset_id,
        status="success",
        row_count=row_count,
        elapsed_ms=elapsed,
    )


def compute_and_store_all_factors(
    session: Session,
    start: str | None = None,
    end: str | None = None,
) -> list[FactorStoreResult]:
    """Compute and store factors for all active assets.

    Queries asset_master for active assets, falls back to SYMBOL_MAP.
    Processes each asset independently (partial failure allowed).
    """
    from collector.fdr_client import SYMBOL_MAP

    try:
        assets = (
            session.query(AssetMaster).filter(AssetMaster.is_active.is_(True)).all()
        )
        asset_ids = [a.asset_id for a in assets]
    except Exception:
        logger.warning("Could not query asset_master, falling back to SYMBOL_MAP")
        asset_ids = list(SYMBOL_MAP.keys())

    results: list[FactorStoreResult] = []
    for asset_id in asset_ids:
        result = compute_and_store_factors(session, asset_id, start, end)
        results.append(result)

    success = sum(1 for r in results if r.status == "success")
    total_rows = sum(r.row_count for r in results)
    logger.info(
        "Factor store complete: %d/%d assets succeeded, %d total rows",
        success,
        len(results),
        total_rows,
    )

    return results

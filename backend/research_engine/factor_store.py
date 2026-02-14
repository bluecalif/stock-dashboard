"""Factor DB storage: compute factors and UPSERT into factor_daily table."""

import logging
import time
from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db.models import FactorDaily
from research_engine.factors import FACTOR_VERSION, compute_all_factors
from research_engine.preprocessing import preprocess

logger = logging.getLogger(__name__)


@dataclass
class FactorStoreResult:
    asset_id: str
    status: str  # "success" | "preprocess_failed" | "compute_failed" | "store_failed"
    row_count: int = 0
    factor_count: int = 0
    errors: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


def _factors_to_records(
    asset_id: str,
    factors_df: pd.DataFrame,
    version: str = FACTOR_VERSION,
) -> list[dict]:
    """Convert wide factor DataFrame to long-format records for factor_daily.

    Skips NaN values (early rows with insufficient lookback).
    """
    records = []
    for date_val, row in factors_df.iterrows():
        date_key = date_val.date() if hasattr(date_val, "date") else date_val
        for factor_name in factors_df.columns:
            value = row[factor_name]
            if pd.isna(value):
                continue
            records.append({
                "asset_id": asset_id,
                "date": date_key,
                "factor_name": factor_name,
                "version": version,
                "value": float(value),
            })
    return records


def _upsert_factors(session: Session, records: list[dict], chunk_size: int = 2000) -> int:
    """UPSERT factor records into factor_daily using ON CONFLICT DO UPDATE.

    Conflict key: (asset_id, date, factor_name, version).
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


def store_factors_for_asset(
    session: Session,
    asset_id: str,
    start: str | None = None,
    end: str | None = None,
    version: str = FACTOR_VERSION,
    missing_threshold: float = 0.05,
) -> FactorStoreResult:
    """Compute and store factors for a single asset.

    Pipeline: preprocess → compute_all_factors → UPSERT factor_daily.
    """
    t0 = time.perf_counter()
    logger.info("Computing factors for %s", asset_id)

    # 1. Preprocess
    try:
        df = preprocess(session, asset_id, start, end, missing_threshold=missing_threshold)
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
        factors_df = compute_all_factors(df)
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error("Factor computation failed for %s: %s", asset_id, e)
        return FactorStoreResult(
            asset_id=asset_id,
            status="compute_failed",
            errors=[str(e)],
            elapsed_ms=elapsed,
        )

    # 3. Convert to long format and UPSERT
    try:
        records = _factors_to_records(asset_id, factors_df, version)
        row_count = _upsert_factors(session, records)
        session.commit()
    except Exception as e:
        session.rollback()
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error("Factor store failed for %s: %s", asset_id, e)
        return FactorStoreResult(
            asset_id=asset_id,
            status="store_failed",
            errors=[f"db_upsert_error: {e}"],
            elapsed_ms=elapsed,
        )

    elapsed = (time.perf_counter() - t0) * 1000
    factor_count = len(factors_df.columns)
    logger.info(
        "Stored %d factor rows for %s (%d factors) in %.0fms",
        row_count, asset_id, factor_count, elapsed,
    )
    return FactorStoreResult(
        asset_id=asset_id,
        status="success",
        row_count=row_count,
        factor_count=factor_count,
        elapsed_ms=elapsed,
    )


def store_factors_all(
    session: Session,
    asset_ids: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
    version: str = FACTOR_VERSION,
) -> list[FactorStoreResult]:
    """Compute and store factors for all (or specified) assets.

    If asset_ids is None, queries asset_master for active assets.
    """
    from collector.fdr_client import SYMBOL_MAP
    from db.models import AssetMaster

    if asset_ids is None:
        try:
            assets = session.query(AssetMaster).filter(AssetMaster.is_active.is_(True)).all()
            asset_ids = [a.asset_id for a in assets]
        except Exception:
            logger.warning("Could not query asset_master, falling back to SYMBOL_MAP")
            asset_ids = list(SYMBOL_MAP.keys())

    results: list[FactorStoreResult] = []
    for asset_id in asset_ids:
        result = store_factors_for_asset(session, asset_id, start, end, version)
        results.append(result)

    success = sum(1 for r in results if r.status == "success")
    total = len(results)
    total_rows = sum(r.row_count for r in results)
    logger.info(
        "Factor store complete: %d/%d assets succeeded, %d total rows",
        success, total, total_rows,
    )

    return results

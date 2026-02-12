"""Factor storage: compute factors for assets and UPSERT into factor_daily."""

import logging
import time
from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from db.models import FactorDaily
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
    status: str  # "success" | "error"
    row_count: int = 0
    factor_count: int = 0
    errors: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


def _factors_to_records(
    asset_id: str,
    df_factors: pd.DataFrame,
    version: str = FACTOR_VERSION,
) -> list[dict]:
    """Convert factor DataFrame to list of dicts for DB insertion.

    Each row × factor_name becomes one record:
      {asset_id, date, factor_name, version, value}

    NaN values are skipped.
    """
    records = []
    for date_idx, row in df_factors.iterrows():
        date_val = date_idx.date() if hasattr(date_idx, "date") else date_idx
        for factor_name in df_factors.columns:
            if factor_name not in ALL_FACTOR_NAMES:
                continue
            value = row[factor_name]
            if pd.isna(value):
                continue
            records.append(
                {
                    "asset_id": asset_id,
                    "date": date_val,
                    "factor_name": factor_name,
                    "version": version,
                    "value": float(value),
                }
            )
    return records


def upsert_factors(
    session: Session,
    records: list[dict],
    chunk_size: int = 1000,
) -> int:
    """UPSERT factor records into factor_daily using ON CONFLICT DO UPDATE.

    Conflict key: (asset_id, date, factor_name, version).
    Updated column: value.
    Processes in chunks of chunk_size rows.

    Returns total row count processed.
    """
    if not records:
        return 0

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
    """Full pipeline for one asset: preprocess → compute factors → UPSERT.

    Args:
        session: SQLAlchemy session
        asset_id: Asset identifier
        start: Start date string (optional)
        end: End date string (optional)
        version: Factor version tag (default "v1")
        missing_threshold: Missing data threshold for preprocessing

    Returns:
        FactorStoreResult with status and details
    """
    t0 = time.perf_counter()
    logger.info("Computing factors for %s", asset_id)

    try:
        # 1. Preprocess
        df = preprocess(session, asset_id, start, end, missing_threshold)

        # 2. Compute factors
        df_factors = compute_all_factors(df)

        # 3. Convert to records (skip NaN)
        records = _factors_to_records(asset_id, df_factors, version)

        # 4. UPSERT
        row_count = upsert_factors(session, records)
        session.commit()

        elapsed = (time.perf_counter() - t0) * 1000
        factor_count = df_factors.columns.isin(ALL_FACTOR_NAMES).sum()

        logger.info(
            "Stored factors for %s: %d records (%d factors) in %.0fms",
            asset_id,
            row_count,
            factor_count,
            elapsed,
        )

        return FactorStoreResult(
            asset_id=asset_id,
            status="success",
            row_count=row_count,
            factor_count=int(factor_count),
            elapsed_ms=elapsed,
        )

    except Exception as e:
        session.rollback()
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error("Factor computation failed for %s: %s", asset_id, e)
        return FactorStoreResult(
            asset_id=asset_id,
            status="error",
            errors=[str(e)],
            elapsed_ms=elapsed,
        )


def store_factors_all(
    session: Session,
    asset_ids: list[str] | None = None,
    start: str | None = None,
    end: str | None = None,
    version: str = FACTOR_VERSION,
    missing_threshold: float = 0.05,
) -> list[FactorStoreResult]:
    """Compute and store factors for multiple assets.

    If asset_ids is None, queries asset_master for active assets.

    Args:
        session: SQLAlchemy session
        asset_ids: List of asset identifiers (None = all active)
        start: Start date string
        end: End date string
        version: Factor version tag
        missing_threshold: Missing data threshold

    Returns:
        List of FactorStoreResult for each asset
    """
    if asset_ids is None:
        from collector.fdr_client import SYMBOL_MAP
        from db.models import AssetMaster

        try:
            assets = (
                session.query(AssetMaster)
                .filter(AssetMaster.is_active.is_(True))
                .all()
            )
            asset_ids = [a.asset_id for a in assets]
        except Exception:
            logger.warning(
                "Could not query asset_master, falling back to SYMBOL_MAP"
            )
            asset_ids = list(SYMBOL_MAP.keys())

    results: list[FactorStoreResult] = []
    for asset_id in asset_ids:
        result = store_factors_for_asset(
            session, asset_id, start, end, version, missing_threshold
        )
        results.append(result)

    success = sum(1 for r in results if r.status == "success")
    total = len(results)
    logger.info("Factor storage complete: %d/%d succeeded", success, total)

    return results

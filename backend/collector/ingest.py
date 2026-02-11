"""Ingest orchestration: fetch → validate → store pipeline."""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert

from collector.fdr_client import fetch_ohlcv
from collector.validators import validate_ohlcv
from db.models import AssetMaster, JobRun, PriceDaily

logger = logging.getLogger(__name__)


@dataclass
class IngestResult:
    asset_id: str
    status: str  # "success" | "validation_failed" | "fetch_failed"
    row_count: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


def _upsert(session, df, chunk_size: int = 1000) -> int:
    """Upsert DataFrame rows into price_daily using ON CONFLICT DO UPDATE.

    Conflict key: (asset_id, date, source).
    Updated columns: open, high, low, close, volume, ingested_at.
    Processes in chunks of chunk_size rows.

    Returns total row count processed.
    """
    records = df.to_dict(orient="records")
    total = 0
    update_cols = ["open", "high", "low", "close", "volume", "ingested_at"]

    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        stmt = insert(PriceDaily).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=["asset_id", "date", "source"],
            set_={col: stmt.excluded[col] for col in update_cols},
        )
        session.execute(stmt)
        total += len(chunk)

    session.flush()
    return total


def _create_job_run(session, job_name: str):
    """Create a job_run record with status='running'. Returns the JobRun."""
    job = JobRun(
        job_name=job_name,
        started_at=datetime.now(timezone.utc),
        status="running",
    )
    session.add(job)
    session.flush()
    return job


def _finish_job_run(session, job, results: list["IngestResult"]):
    """Update job_run with final status based on results."""
    failures = [r for r in results if r.status != "success"]
    successes = [r for r in results if r.status == "success"]

    if len(failures) == 0:
        job.status = "success"
    elif len(successes) == 0:
        job.status = "failure"
    else:
        job.status = "partial_failure"

    job.ended_at = datetime.now(timezone.utc)

    if failures:
        error_summary = [
            {"asset_id": r.asset_id, "status": r.status, "errors": r.errors}
            for r in failures
        ]
        job.error_message = json.dumps(error_summary, ensure_ascii=False)

    session.flush()


def ingest_asset(asset_id: str, start: str, end: str, session=None) -> IngestResult:
    """Single asset ingest pipeline: fetch → validate → store.

    Args:
        asset_id: Internal asset identifier
        start: Start date string
        end: End date string
        session: SQLAlchemy session (None = skip DB store)

    Returns:
        IngestResult with status and details
    """
    t0 = time.perf_counter()
    logger.info("Ingesting %s (%s ~ %s)", asset_id, start, end)

    # 1. Fetch
    try:
        df = fetch_ohlcv(asset_id, start, end)
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error("Fetch failed for %s: %s", asset_id, e)
        return IngestResult(
            asset_id=asset_id,
            status="fetch_failed",
            errors=[str(e)],
            elapsed_ms=elapsed,
        )

    # 2. Validate
    result = validate_ohlcv(df)
    if not result.is_valid:
        elapsed = (time.perf_counter() - t0) * 1000
        logger.error("Validation failed for %s: %s", asset_id, result.errors)
        return IngestResult(
            asset_id=asset_id,
            status="validation_failed",
            row_count=result.row_count,
            errors=result.errors,
            elapsed_ms=elapsed,
        )

    # 3. Store
    row_count = result.row_count
    if session is not None:
        try:
            row_count = _upsert(session, df)
            session.commit()
        except Exception as e:
            session.rollback()
            elapsed = (time.perf_counter() - t0) * 1000
            logger.error("DB insert failed for %s: %s", asset_id, e)
            return IngestResult(
                asset_id=asset_id,
                status="fetch_failed",
                errors=[f"db_insert_error: {e}"],
                elapsed_ms=elapsed,
            )

    elapsed = (time.perf_counter() - t0) * 1000
    logger.info("Ingested %s: %d rows in %.0fms", asset_id, row_count, elapsed)
    return IngestResult(
        asset_id=asset_id,
        status="success",
        row_count=row_count,
        elapsed_ms=elapsed,
    )


def ingest_all(start: str, end: str, session=None) -> list[IngestResult]:
    """Ingest all active assets.

    If session is provided, queries asset_master for active assets
    and records a job_run entry.
    Otherwise falls back to SYMBOL_MAP keys (no job_run).
    """
    from collector.fdr_client import SYMBOL_MAP

    if session is not None:
        try:
            assets = session.query(AssetMaster).filter(AssetMaster.is_active.is_(True)).all()
            asset_ids = [a.asset_id for a in assets]
        except Exception:
            logger.warning("Could not query asset_master, falling back to SYMBOL_MAP")
            asset_ids = list(SYMBOL_MAP.keys())
    else:
        asset_ids = list(SYMBOL_MAP.keys())

    # Create job_run record
    job = None
    if session is not None:
        job = _create_job_run(session, f"ingest_all({start}~{end})")

    results: list[IngestResult] = []
    for asset_id in asset_ids:
        result = ingest_asset(asset_id, start, end, session)
        results.append(result)

    # Finish job_run
    if session is not None and job is not None:
        _finish_job_run(session, job, results)
        session.commit()

    success = sum(1 for r in results if r.status == "success")
    total = len(results)
    logger.info("Ingest complete: %d/%d succeeded", success, total)

    return results

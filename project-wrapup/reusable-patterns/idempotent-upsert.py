"""
## 용도
PostgreSQL INSERT ... ON CONFLICT DO UPDATE (Idempotent UPSERT).
대용량 데이터를 chunk 단위로 분할 처리 + Job 추적.

## 사용법
1. PriceDaily 등 테이블에 복합 PK/유니크 인덱스 설정 (asset_id, date, source)
2. _upsert(session, df, chunk_size) 호출
3. ingest_asset() → fetch → validate → upsert 파이프라인

## 출처
stock-dashboard/backend/collector/ingest.py
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone

from sqlalchemy.dialects.postgresql import insert


@dataclass
class IngestResult:
    asset_id: str
    status: str  # "success" | "validation_failed" | "fetch_failed"
    row_count: int = 0
    errors: list[str] = field(default_factory=list)
    elapsed_ms: float = 0.0


def _upsert(session, table_class, df, conflict_keys, update_cols, chunk_size=1000) -> int:
    """Upsert DataFrame rows using ON CONFLICT DO UPDATE."""
    records = df.to_dict(orient="records")
    total = 0

    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        stmt = insert(table_class).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=conflict_keys,
            set_={col: stmt.excluded[col] for col in update_cols},
        )
        session.execute(stmt)
        total += len(chunk)

    session.flush()
    return total


def ingest_asset(asset_id, start, end, session, fetch_fn, validate_fn, table_class, conflict_keys, update_cols) -> IngestResult:
    """Single asset ingest pipeline: fetch -> validate -> upsert."""
    t0 = time.perf_counter()

    # 1. Fetch
    try:
        df = fetch_fn(asset_id, start, end)
    except Exception as e:
        elapsed = (time.perf_counter() - t0) * 1000
        return IngestResult(asset_id=asset_id, status="fetch_failed", errors=[str(e)], elapsed_ms=elapsed)

    # 2. Validate
    result = validate_fn(df)
    if not result.is_valid:
        elapsed = (time.perf_counter() - t0) * 1000
        return IngestResult(asset_id=asset_id, status="validation_failed",
            row_count=result.row_count, errors=result.errors, elapsed_ms=elapsed)

    # 3. Upsert
    try:
        row_count = _upsert(session, table_class, df, conflict_keys, update_cols)
        session.commit()
    except Exception as e:
        session.rollback()
        elapsed = (time.perf_counter() - t0) * 1000
        return IngestResult(asset_id=asset_id, status="fetch_failed",
            errors=[f"db_insert_error: {e}"], elapsed_ms=elapsed)

    elapsed = (time.perf_counter() - t0) * 1000
    return IngestResult(asset_id=asset_id, status="success", row_count=row_count, elapsed_ms=elapsed)


# --- Job Tracking ---
def _create_job_run(session, job_run_class, job_name):
    job = job_run_class(job_name=job_name, started_at=datetime.now(timezone.utc), status="running")
    session.add(job)
    session.flush()
    return job

def _finish_job_run(session, job, results):
    failures = [r for r in results if r.status != "success"]
    successes = [r for r in results if r.status == "success"]
    job.status = "success" if not failures else ("failure" if not successes else "partial_failure")
    job.ended_at = datetime.now(timezone.utc)
    if failures:
        job.error_message = json.dumps(
            [{"asset_id": r.asset_id, "status": r.status, "errors": r.errors} for r in failures],
            ensure_ascii=False,
        )
    session.flush()

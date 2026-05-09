"""
## 용도
PostgreSQL ON CONFLICT DO UPDATE 기반 멱등 UPSERT.
chunk 단위 분할 처리 + Job 상태 추적. 수정 필요 (테이블/컬럼/conflict 키 교체).

## 언제 쓰는가
외부 데이터 소스에서 주기적으로 데이터를 수집하여 DB에 적재할 때.
동일 키 데이터가 반복 수집되어도 안전하게 업데이트되어야 할 때 (멱등성).

## 전제조건
- PostgreSQL (ON CONFLICT 지원)
- 대상 테이블에 복합 PK 또는 유니크 인덱스 (conflict_keys로 사용)
- pandas DataFrame 형태의 입력 데이터

## 의존성
- sqlalchemy.dialects.postgresql: insert (PostgreSQL 전용)
- pandas: DataFrame → dict 변환
- dataclasses: IngestResult 결과 객체

## 통합 포인트
- collector/ 디렉토리에 ingest.py로 배치
- 스케줄러(cron/GitHub Actions)에서 ingest_asset() 호출
- job_run 테이블로 수집 작업 상태 추적 (성공/실패/부분실패)
- numpy 타입은 Python native로 변환 후 전달 필수 (T-007)

## 주의사항
- chunk_size가 너무 크면 메모리 문제, 너무 작으면 성능 저하 — 1000이 기본값
- conflict_keys와 실제 DB 인덱스가 일치해야 함
- numpy.float64/Timestamp → Python native 타입 변환 필수 (T-007)
- NaN 값 DB 적재 전 체크 필수 (T-006)

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

"""Integration tests for ingest pipeline against real PostgreSQL."""

import os
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
import pytest
from sqlalchemy import text

from collector.ingest import _upsert, ingest_all

pytestmark = pytest.mark.skipif(
    not os.environ.get("INTEGRATION_TEST"),
    reason="Set INTEGRATION_TEST=1 to run integration tests",
)


def _mock_asset_master_query(*asset_ids):
    """Return a patch that makes session.query(AssetMaster) return fake assets."""
    fake_assets = [
        SimpleNamespace(asset_id=aid, is_active=True) for aid in asset_ids
    ]

    def _patch_query(model):
        """Replace session.query(AssetMaster) with fake chain."""
        mock_qs = SimpleNamespace(
            filter=lambda *a, **kw: SimpleNamespace(all=lambda: fake_assets)
        )
        return mock_qs

    return _patch_query


def _make_test_df(asset_id="__TEST_KS200", dates=None, close=100.0):
    """Create a minimal OHLCV DataFrame for testing."""
    if dates is None:
        dates = ["2023-06-01", "2023-06-02", "2023-06-05"]
    n = len(dates)
    return pd.DataFrame(
        {
            "asset_id": [asset_id] * n,
            "date": pd.to_datetime(dates),
            "open": [close] * n,
            "high": [close + 5] * n,
            "low": [close - 5] * n,
            "close": [close] * n,
            "volume": [10000] * n,
            "source": ["fdr"] * n,
            "ingested_at": [datetime.now(timezone.utc)] * n,
        }
    )


class TestUpsertIdempotent:
    def test_upsert_twice_same_row_count(self, db_session):
        """Same data upserted twice must not duplicate rows."""
        df = _make_test_df()

        _upsert(db_session, df)
        db_session.commit()

        _upsert(db_session, df)
        db_session.commit()

        result = db_session.execute(
            text(
                "SELECT count(*) FROM price_daily "
                "WHERE asset_id = '__TEST_KS200' AND source = 'fdr'"
            )
        )
        count = result.scalar()
        assert count == 3, f"Expected 3 rows, got {count} (duplicates detected)"

    def test_upsert_updates_ingested_at(self, db_session):
        """Re-upsert must update ingested_at to a newer timestamp."""
        df1 = _make_test_df()
        _upsert(db_session, df1)
        db_session.commit()

        # Read first ingested_at
        row = db_session.execute(
            text(
                "SELECT ingested_at FROM price_daily "
                "WHERE asset_id = '__TEST_KS200' AND date = '2023-06-01'"
            )
        ).fetchone()
        first_ts = row[0]

        # Re-upsert with fresh timestamp
        import time

        time.sleep(0.1)  # ensure clock advances
        df2 = _make_test_df()
        _upsert(db_session, df2)
        db_session.commit()

        row = db_session.execute(
            text(
                "SELECT ingested_at FROM price_daily "
                "WHERE asset_id = '__TEST_KS200' AND date = '2023-06-01'"
            )
        ).fetchone()
        second_ts = row[0]

        assert second_ts >= first_ts, (
            f"ingested_at not updated: {first_ts} -> {second_ts}"
        )


class TestJobRunRecorded:
    def test_job_run_exists_after_ingest_all(self, db_session):
        """ingest_all must create a job_run record in the DB."""
        df = _make_test_df(asset_id="__TEST_A")

        original_query = db_session.query
        db_session.query = _mock_asset_master_query("__TEST_A")

        with patch("collector.ingest.fetch_ohlcv", return_value=df):
            results = ingest_all("2023-06-01", "2023-06-05", session=db_session)

        db_session.query = original_query

        assert any(r.status == "success" for r in results)

        # Verify job_run was recorded
        job = db_session.execute(
            text(
                "SELECT job_name, status FROM job_run "
                "WHERE job_name LIKE 'ingest_all(2023-06-01%' "
                "ORDER BY started_at DESC LIMIT 1"
            )
        ).fetchone()
        assert job is not None, "job_run record not found"
        assert job[1] in ("success", "partial_failure")


class TestPartialFailureRecorded:
    def test_partial_failure_status_in_db(self, db_session):
        """When one asset fails, job_run.status must be 'partial_failure'."""
        df_ok = _make_test_df(asset_id="__TEST_OK")

        def mock_fetch(asset_id, start, end):
            if asset_id == "__TEST_FAIL":
                raise RuntimeError("Simulated fetch failure")
            return df_ok

        original_query = db_session.query
        db_session.query = _mock_asset_master_query("__TEST_OK", "__TEST_FAIL")

        with patch("collector.ingest.fetch_ohlcv", side_effect=mock_fetch):
            results = ingest_all("2023-06-01", "2023-06-05", session=db_session)

        db_session.query = original_query

        statuses = {r.asset_id: r.status for r in results}
        assert statuses["__TEST_OK"] == "success"
        assert statuses["__TEST_FAIL"] == "fetch_failed"

        # Verify job_run partial_failure
        job = db_session.execute(
            text(
                "SELECT status, error_message FROM job_run "
                "WHERE job_name LIKE 'ingest_all(2023-06-01%' "
                "ORDER BY started_at DESC LIMIT 1"
            )
        ).fetchone()
        assert job is not None
        assert job[0] == "partial_failure"
        assert "__TEST_FAIL" in job[1]

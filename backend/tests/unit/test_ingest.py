"""Tests for collector.ingest."""

import json
from unittest.mock import MagicMock, patch

from collector.ingest import (
    IngestResult,
    _finish_job_run,
    _upsert,
    ingest_all,
    ingest_asset,
)


class TestIngestAsset:
    def test_ingest_asset_success(self, sample_ohlcv_df):
        """Successful ingest must return status='success'."""
        with patch("collector.ingest.fetch_ohlcv", return_value=sample_ohlcv_df):
            result = ingest_asset("KS200", "2026-01-01", "2026-01-10")
            assert result.status == "success"
            assert result.row_count == 3
            assert result.errors == []
            assert result.elapsed_ms > 0

    def test_ingest_asset_fetch_failure(self):
        """Fetch failure must return status='fetch_failed'."""
        with patch("collector.ingest.fetch_ohlcv", side_effect=RuntimeError("API down")):
            result = ingest_asset("KS200", "2026-01-01", "2026-01-10")
            assert result.status == "fetch_failed"
            assert any("API down" in e for e in result.errors)

    def test_ingest_asset_validation_failure(self, invalid_ohlcv_high_low):
        """Validation failure must return status='validation_failed'."""
        with patch("collector.ingest.fetch_ohlcv", return_value=invalid_ohlcv_high_low):
            result = ingest_asset("KS200", "2026-01-01", "2026-01-10")
            assert result.status == "validation_failed"
            assert any("high_low_inversion" in e for e in result.errors)
            assert result.row_count == 2


class TestUpsert:
    def test_upsert_uses_on_conflict(self, sample_ohlcv_df):
        """_upsert must use INSERT ... ON CONFLICT DO UPDATE."""
        mock_session = MagicMock()
        row_count = _upsert(mock_session, sample_ohlcv_df)

        assert row_count == 3
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

        # Verify the executed statement is a PostgreSQL INSERT with on_conflict
        stmt = mock_session.execute.call_args[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
        assert "ON CONFLICT" in compiled
        assert "DO UPDATE SET" in compiled

    def test_upsert_chunking(self, sample_ohlcv_df):
        """_upsert with chunk_size=2 must execute twice for 3 rows."""
        mock_session = MagicMock()
        row_count = _upsert(mock_session, sample_ohlcv_df, chunk_size=2)

        assert row_count == 3
        assert mock_session.execute.call_count == 2  # 2 + 1 rows


class TestJobRun:
    def test_job_run_created_on_ingest_all(self, sample_ohlcv_df):
        """ingest_all with session must create a job_run record."""
        mock_session = MagicMock()
        # Make query return empty list so it falls back to SYMBOL_MAP
        mock_session.query.return_value.filter.return_value.all.return_value = []

        with (
            patch("collector.ingest.fetch_ohlcv", return_value=sample_ohlcv_df),
            patch("collector.fdr_client.SYMBOL_MAP", {"TEST1": {}}),
            patch("collector.ingest._upsert", return_value=3),
        ):
            ingest_all("2026-01-01", "2026-01-10", session=mock_session)

        # job_run should have been added to session
        add_calls = mock_session.add.call_args_list
        assert len(add_calls) >= 1
        job_obj = add_calls[0][0][0]
        assert job_obj.job_name.startswith("ingest_all(")
        assert job_obj.status in ("success", "running")

    def test_job_run_partial_failure_status(self):
        """partial failure: some success + some failure → 'partial_failure'."""
        mock_session = MagicMock()
        job = MagicMock()
        job.status = "running"

        results = [
            IngestResult(asset_id="A", status="success", row_count=10),
            IngestResult(asset_id="B", status="fetch_failed", errors=["timeout"]),
        ]
        _finish_job_run(mock_session, job, results)

        assert job.status == "partial_failure"
        assert job.ended_at is not None
        error_data = json.loads(job.error_message)
        assert len(error_data) == 1
        assert error_data[0]["asset_id"] == "B"

    def test_job_run_all_success_status(self):
        """All success → 'success' status, no error_message set."""
        mock_session = MagicMock()
        job = MagicMock()
        job.error_message = None

        results = [
            IngestResult(asset_id="A", status="success"),
            IngestResult(asset_id="B", status="success"),
        ]
        _finish_job_run(mock_session, job, results)

        assert job.status == "success"
        assert job.error_message is None

    def test_job_run_all_failure_status(self):
        """All failures → 'failure' status."""
        mock_session = MagicMock()
        job = MagicMock()

        results = [
            IngestResult(asset_id="A", status="fetch_failed", errors=["err"]),
        ]
        _finish_job_run(mock_session, job, results)

        assert job.status == "failure"


class TestIngestAll:
    def test_ingest_all_partial_failure(self, sample_ohlcv_df):
        """One asset failure must not stop others."""
        call_count = {"n": 0}

        def mock_fetch(asset_id, start, end):
            call_count["n"] += 1
            if asset_id == "005930":
                raise RuntimeError("Samsung fetch failed")
            return sample_ohlcv_df

        with patch("collector.ingest.fetch_ohlcv", side_effect=mock_fetch):
            results = ingest_all("2026-01-01", "2026-01-10")
            statuses = {r.asset_id: r.status for r in results}
            assert statuses["005930"] == "fetch_failed"
            # Others should succeed
            success_count = sum(1 for r in results if r.status == "success")
            assert success_count == 6  # 7 total - 1 failed

    def test_ingest_all_returns_all_assets(self, sample_ohlcv_df):
        """Must attempt all 7 assets."""
        with patch("collector.ingest.fetch_ohlcv", return_value=sample_ohlcv_df):
            results = ingest_all("2026-01-01", "2026-01-10")
            assert len(results) == 7

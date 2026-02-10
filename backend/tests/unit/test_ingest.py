"""Tests for collector.ingest."""

from unittest.mock import patch

from collector.ingest import ingest_all, ingest_asset


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

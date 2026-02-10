"""Tests for collector.validators."""

from datetime import datetime, timezone

import pandas as pd

from collector.validators import validate_ohlcv


class TestValidateOhlcv:
    def test_valid_data_passes(self, sample_ohlcv_df):
        """Valid data must pass validation."""
        result = validate_ohlcv(sample_ohlcv_df)
        assert result.is_valid is True
        assert result.errors == []
        assert result.row_count == 3

    def test_high_low_inversion(self, invalid_ohlcv_high_low):
        """Must detect high < low inversion."""
        result = validate_ohlcv(invalid_ohlcv_high_low)
        assert result.is_valid is False
        assert any("high_low_inversion" in e for e in result.errors)

    def test_negative_price(self, invalid_ohlcv_negative):
        """Must detect negative prices."""
        result = validate_ohlcv(invalid_ohlcv_negative)
        assert result.is_valid is False
        assert any("negative_price" in e for e in result.errors)

    def test_empty_dataframe(self):
        """Must detect empty DataFrame."""
        result = validate_ohlcv(pd.DataFrame())
        assert result.is_valid is False
        assert "empty_dataframe" in result.errors

    def test_none_dataframe(self):
        """Must handle None input."""
        result = validate_ohlcv(None)
        assert result.is_valid is False
        assert "empty_dataframe" in result.errors

    def test_missing_columns(self):
        """Must detect missing required columns."""
        df = pd.DataFrame({"asset_id": ["KS200"], "date": ["2026-01-02"]})
        result = validate_ohlcv(df)
        assert result.is_valid is False
        assert any("missing_columns" in e for e in result.errors)

    def test_duplicate_key(self):
        """Must detect duplicate (asset_id, date) keys."""
        df = pd.DataFrame({
            "asset_id": ["KS200", "KS200"],
            "date": pd.to_datetime(["2026-01-02", "2026-01-02"]),
            "open": [100.0, 101.0],
            "high": [105.0, 106.0],
            "low": [98.0, 99.0],
            "close": [103.0, 104.0],
            "volume": [50000, 60000],
            "source": ["fdr", "fdr"],
            "ingested_at": [datetime.now(timezone.utc)] * 2,
        })
        result = validate_ohlcv(df)
        assert result.is_valid is False
        assert any("duplicate_key" in e for e in result.errors)

    def test_zero_volume_warning(self):
        """Zero volume must produce warning, not error."""
        df = pd.DataFrame({
            "asset_id": ["KS200"],
            "date": pd.to_datetime(["2026-01-02"]),
            "open": [100.0],
            "high": [105.0],
            "low": [98.0],
            "close": [103.0],
            "volume": [0],
            "source": ["fdr"],
            "ingested_at": [datetime.now(timezone.utc)],
        })
        result = validate_ohlcv(df)
        assert result.is_valid is True
        assert any("zero_volume" in w for w in result.warnings)

    def test_negative_volume(self):
        """Negative volume must be an error."""
        df = pd.DataFrame({
            "asset_id": ["KS200"],
            "date": pd.to_datetime(["2026-01-02"]),
            "open": [100.0],
            "high": [105.0],
            "low": [98.0],
            "close": [103.0],
            "volume": [-100],
            "source": ["fdr"],
            "ingested_at": [datetime.now(timezone.utc)],
        })
        result = validate_ohlcv(df)
        assert result.is_valid is False
        assert any("negative_volume" in e for e in result.errors)

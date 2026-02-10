"""Tests for collector.fdr_client."""

from unittest.mock import patch

import pandas as pd
import pytest

from collector.fdr_client import SYMBOL_MAP, _standardize, fetch_ohlcv


class TestSymbolMap:
    def test_symbol_map_completeness(self):
        """All 7 assets must be in SYMBOL_MAP."""
        expected = {"KS200", "005930", "000660", "SOXL", "BTC", "GC=F", "SI=F"}
        assert set(SYMBOL_MAP.keys()) == expected

    def test_symbol_map_fdr_symbol(self):
        """Each entry must have fdr_symbol and category."""
        for asset_id, info in SYMBOL_MAP.items():
            assert "fdr_symbol" in info, f"{asset_id} missing fdr_symbol"
            assert "category" in info, f"{asset_id} missing category"

    def test_btc_has_fallback(self):
        """BTC must have a fallback symbol."""
        assert "fallback" in SYMBOL_MAP["BTC"]
        assert SYMBOL_MAP["BTC"]["fallback"] == "BTC/USD"


class TestStandardize:
    def test_columns(self, mock_fdr_dataframe):
        """Standardized DataFrame must have correct columns."""
        result = _standardize(mock_fdr_dataframe, "KS200")
        expected_cols = [
            "asset_id", "date", "open", "high", "low", "close",
            "volume", "source", "ingested_at",
        ]
        assert list(result.columns) == expected_cols

    def test_asset_id_added(self, mock_fdr_dataframe):
        """asset_id column must be set correctly."""
        result = _standardize(mock_fdr_dataframe, "KS200")
        assert (result["asset_id"] == "KS200").all()

    def test_source_is_fdr(self, mock_fdr_dataframe):
        """source column must be 'fdr'."""
        result = _standardize(mock_fdr_dataframe, "KS200")
        assert (result["source"] == "fdr").all()

    def test_volume_int(self, mock_fdr_dataframe):
        """volume must be integer type."""
        result = _standardize(mock_fdr_dataframe, "KS200")
        assert result["volume"].dtype in ("int64", "int32")


class TestFetchOhlcv:
    def test_fetch_ohlcv_columns(self, mock_fdr_dataframe):
        """fetch_ohlcv must return standardized columns."""
        with patch("collector.fdr_client._fetch_raw", return_value=mock_fdr_dataframe):
            result = fetch_ohlcv("KS200", "2026-01-01", "2026-01-10")
            expected_cols = [
                "asset_id", "date", "open", "high", "low", "close",
                "volume", "source", "ingested_at",
            ]
            assert list(result.columns) == expected_cols
            assert len(result) == 2

    def test_fetch_ohlcv_unknown_asset(self):
        """Unknown asset_id must raise ValueError."""
        with pytest.raises(ValueError, match="Unknown asset_id"):
            fetch_ohlcv("INVALID", "2026-01-01", "2026-01-10")

    def test_fetch_ohlcv_empty_raises(self):
        """Empty result must raise after retries."""
        with patch("collector.fdr_client._fetch_raw", return_value=pd.DataFrame()):
            with pytest.raises(RuntimeError, match="All retries exhausted"):
                fetch_ohlcv("KS200", "2026-01-01", "2026-01-10")

    def test_fetch_ohlcv_btc_fallback(self, mock_fdr_dataframe):
        """BTC must fallback to BTC/USD on primary failure."""
        call_count = {"n": 0}

        def side_effect(symbol, start, end):
            call_count["n"] += 1
            if symbol == "BTC/KRW":
                raise ConnectionError("Primary failed")
            return mock_fdr_dataframe

        with patch("collector.fdr_client._fetch_raw", side_effect=side_effect):
            with patch("collector.fdr_client.BASE_DELAY", 0):
                result = fetch_ohlcv("BTC", "2026-01-01", "2026-01-10")
                assert len(result) == 2
                assert (result["asset_id"] == "BTC").all()
                # Should have tried primary 3 times + fallback
                assert call_count["n"] >= 4

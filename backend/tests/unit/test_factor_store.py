"""Tests for research_engine.factor_store module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from research_engine.factor_store import (
    FactorStoreResult,
    _factors_to_records,
    store_factors_all,
    store_factors_for_asset,
    upsert_factors,
)
from research_engine.factors import ALL_FACTOR_NAMES, FACTOR_VERSION


def _make_ohlcv(n=100, base_price=100.0, seed=42):
    """Generate deterministic OHLCV DataFrame for testing."""
    rng = np.random.RandomState(seed)
    dates = pd.bdate_range("2025-06-01", periods=n)
    returns = rng.normal(0.001, 0.02, n)
    close = base_price * np.cumprod(1 + returns)
    high = close * (1 + rng.uniform(0, 0.02, n))
    low = close * (1 - rng.uniform(0, 0.02, n))
    open_ = close * (1 + rng.uniform(-0.01, 0.01, n))
    volume = rng.randint(10000, 100000, n)

    return pd.DataFrame(
        {
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )


def _make_factor_df():
    """Create a small factor DataFrame for testing."""
    dates = pd.bdate_range("2025-06-01", periods=5)
    return pd.DataFrame(
        {
            "ret_1d": [np.nan, 0.01, -0.02, 0.015, 0.005],
            "sma_20": [np.nan, np.nan, np.nan, np.nan, 100.5],
            "rsi_14": [np.nan, np.nan, np.nan, np.nan, 55.3],
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )


# --- _factors_to_records ---


class TestFactorsToRecords:
    def test_basic_conversion(self):
        df = _make_factor_df()
        records = _factors_to_records("KS200", df)

        # Only non-NaN values should produce records
        assert len(records) > 0
        for r in records:
            assert "asset_id" in r
            assert "date" in r
            assert "factor_name" in r
            assert "version" in r
            assert "value" in r
            assert r["asset_id"] == "KS200"
            assert r["version"] == FACTOR_VERSION

    def test_nan_values_skipped(self):
        df = _make_factor_df()
        records = _factors_to_records("KS200", df)

        # Count non-NaN values manually
        expected_count = 0
        for col in df.columns:
            if col in ALL_FACTOR_NAMES:
                expected_count += df[col].notna().sum()

        assert len(records) == expected_count

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=["ret_1d", "sma_20"])
        df.index.name = "date"
        records = _factors_to_records("KS200", df)
        assert records == []

    def test_all_nan_dataframe(self):
        dates = pd.bdate_range("2025-06-01", periods=3)
        df = pd.DataFrame(
            {"ret_1d": [np.nan, np.nan, np.nan]},
            index=pd.DatetimeIndex(dates, name="date"),
        )
        records = _factors_to_records("KS200", df)
        assert records == []

    def test_custom_version(self):
        df = _make_factor_df()
        records = _factors_to_records("KS200", df, version="v2")
        for r in records:
            assert r["version"] == "v2"

    def test_non_factor_columns_ignored(self):
        dates = pd.bdate_range("2025-06-01", periods=3)
        df = pd.DataFrame(
            {
                "ret_1d": [0.01, 0.02, 0.03],
                "not_a_factor": [1.0, 2.0, 3.0],
            },
            index=pd.DatetimeIndex(dates, name="date"),
        )
        records = _factors_to_records("KS200", df)
        factor_names = {r["factor_name"] for r in records}
        assert "not_a_factor" not in factor_names
        assert "ret_1d" in factor_names

    def test_value_is_float(self):
        dates = pd.bdate_range("2025-06-01", periods=2)
        df = pd.DataFrame(
            {"ret_1d": [1, 2]},  # int values
            index=pd.DatetimeIndex(dates, name="date"),
        )
        records = _factors_to_records("KS200", df)
        for r in records:
            assert isinstance(r["value"], float)

    def test_date_is_date_object(self):
        """date should be a date (not datetime) for DB compatibility."""
        import datetime

        df = _make_factor_df()
        records = _factors_to_records("KS200", df)
        for r in records:
            assert isinstance(r["date"], datetime.date)


# --- upsert_factors ---


class TestUpsertFactors:
    def test_empty_records(self):
        session = MagicMock()
        count = upsert_factors(session, [])
        assert count == 0
        session.execute.assert_not_called()

    @patch("research_engine.factor_store.insert")
    def test_calls_execute_with_chunks(self, mock_insert):
        session = MagicMock()
        mock_stmt = MagicMock()
        mock_insert.return_value.values.return_value = mock_stmt
        mock_stmt.on_conflict_do_update.return_value = mock_stmt

        rec = {
            "asset_id": "KS200", "date": "2025-06-01",
            "factor_name": "ret_1d", "version": "v1", "value": 0.01,
        }
        records = [rec] * 5

        count = upsert_factors(session, records, chunk_size=3)
        assert count == 5
        # 5 records with chunk_size=3 → 2 chunks
        assert session.execute.call_count == 2
        session.flush.assert_called_once()

    @patch("research_engine.factor_store.insert")
    def test_single_chunk(self, mock_insert):
        session = MagicMock()
        mock_stmt = MagicMock()
        mock_insert.return_value.values.return_value = mock_stmt
        mock_stmt.on_conflict_do_update.return_value = mock_stmt

        rec = {
            "asset_id": "KS200", "date": "2025-06-01",
            "factor_name": "ret_1d", "version": "v1", "value": 0.01,
        }
        records = [rec] * 3

        count = upsert_factors(session, records, chunk_size=1000)
        assert count == 3
        assert session.execute.call_count == 1


# --- store_factors_for_asset ---


class TestStoreFactorsForAsset:
    @patch("research_engine.factor_store.upsert_factors")
    @patch("research_engine.factor_store.compute_all_factors")
    @patch("research_engine.factor_store.preprocess")
    def test_success_flow(self, mock_preprocess, mock_compute, mock_upsert):
        session = MagicMock()
        ohlcv = _make_ohlcv(n=30)
        mock_preprocess.return_value = ohlcv

        factor_df = _make_factor_df()
        mock_compute.return_value = factor_df
        mock_upsert.return_value = 10

        result = store_factors_for_asset(session, "KS200")

        assert isinstance(result, FactorStoreResult)
        assert result.status == "success"
        assert result.asset_id == "KS200"
        assert result.row_count == 10
        assert result.errors == []

        mock_preprocess.assert_called_once()
        mock_compute.assert_called_once_with(ohlcv)
        mock_upsert.assert_called_once()
        session.commit.assert_called_once()

    @patch("research_engine.factor_store.preprocess")
    def test_preprocess_error(self, mock_preprocess):
        session = MagicMock()
        mock_preprocess.side_effect = ValueError("No price data for TEST")

        result = store_factors_for_asset(session, "TEST")

        assert result.status == "error"
        assert "No price data" in result.errors[0]
        session.rollback.assert_called_once()

    @patch("research_engine.factor_store.upsert_factors")
    @patch("research_engine.factor_store.compute_all_factors")
    @patch("research_engine.factor_store.preprocess")
    def test_db_error_rollback(self, mock_preprocess, mock_compute, mock_upsert):
        session = MagicMock()
        mock_preprocess.return_value = _make_ohlcv(n=30)
        mock_compute.return_value = _make_factor_df()
        mock_upsert.side_effect = Exception("DB connection lost")

        result = store_factors_for_asset(session, "KS200")

        assert result.status == "error"
        assert "DB connection lost" in result.errors[0]
        session.rollback.assert_called_once()

    @patch("research_engine.factor_store.upsert_factors")
    @patch("research_engine.factor_store.compute_all_factors")
    @patch("research_engine.factor_store.preprocess")
    def test_custom_version(self, mock_preprocess, mock_compute, mock_upsert):
        session = MagicMock()
        mock_preprocess.return_value = _make_ohlcv(n=30)
        mock_compute.return_value = _make_factor_df()
        mock_upsert.return_value = 5

        result = store_factors_for_asset(session, "KS200", version="v2")
        assert result.status == "success"

    @patch("research_engine.factor_store.upsert_factors")
    @patch("research_engine.factor_store.compute_all_factors")
    @patch("research_engine.factor_store.preprocess")
    def test_elapsed_time_recorded(self, mock_preprocess, mock_compute, mock_upsert):
        session = MagicMock()
        mock_preprocess.return_value = _make_ohlcv(n=30)
        mock_compute.return_value = _make_factor_df()
        mock_upsert.return_value = 5

        result = store_factors_for_asset(session, "KS200")
        assert result.elapsed_ms >= 0


# --- store_factors_all ---


class TestStoreFactorsAll:
    @patch("research_engine.factor_store.store_factors_for_asset")
    def test_with_explicit_asset_ids(self, mock_store):
        session = MagicMock()
        mock_store.return_value = FactorStoreResult(
            asset_id="KS200", status="success", row_count=100
        )

        results = store_factors_all(session, asset_ids=["KS200", "005930"])

        assert len(results) == 2
        assert mock_store.call_count == 2

    @patch("research_engine.factor_store.store_factors_for_asset")
    def test_mixed_results(self, mock_store):
        session = MagicMock()
        mock_store.side_effect = [
            FactorStoreResult(asset_id="KS200", status="success", row_count=100),
            FactorStoreResult(asset_id="BAD", status="error", errors=["fail"]),
        ]

        results = store_factors_all(session, asset_ids=["KS200", "BAD"])
        assert results[0].status == "success"
        assert results[1].status == "error"

    @patch("research_engine.factor_store.store_factors_for_asset")
    def test_passes_parameters(self, mock_store):
        session = MagicMock()
        mock_store.return_value = FactorStoreResult(
            asset_id="KS200", status="success"
        )

        store_factors_all(
            session,
            asset_ids=["KS200"],
            start="2025-01-01",
            end="2025-12-31",
            version="v2",
            missing_threshold=0.1,
        )

        mock_store.assert_called_once_with(
            session, "KS200", "2025-01-01", "2025-12-31", "v2", 0.1
        )


# --- FactorStoreResult ---


class TestFactorStoreResult:
    def test_default_values(self):
        r = FactorStoreResult(asset_id="KS200", status="success")
        assert r.row_count == 0
        assert r.factor_count == 0
        assert r.errors == []
        assert r.elapsed_ms == 0.0

    def test_error_result(self):
        r = FactorStoreResult(
            asset_id="KS200",
            status="error",
            errors=["something broke"],
        )
        assert r.status == "error"
        assert len(r.errors) == 1

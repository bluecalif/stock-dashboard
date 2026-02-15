"""Tests for research_engine.factor_store module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from research_engine.factor_store import (
    _factors_to_records,
    _upsert_factors,
    store_factors_all,
    store_factors_for_asset,
)
from research_engine.factors import ALL_FACTOR_NAMES, FACTOR_VERSION


def _make_ohlcv(n=150, base_price=100.0, seed=42):
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


@pytest.fixture
def ohlcv():
    return _make_ohlcv(n=150)


@pytest.fixture
def factors_df(ohlcv):
    from research_engine.factors import compute_all_factors
    return compute_all_factors(ohlcv)


# --- _factors_to_records ---


class TestFactorsToRecords:
    def test_basic_conversion(self, factors_df):
        """Records should have correct keys and skip NaNs."""
        records = _factors_to_records("KS200", factors_df)
        assert len(records) > 0
        first = records[0]
        assert set(first.keys()) == {"asset_id", "date", "factor_name", "version", "value"}
        assert first["asset_id"] == "KS200"
        assert first["version"] == FACTOR_VERSION

    def test_skips_nan_values(self):
        """NaN values must not appear in records."""
        df = pd.DataFrame(
            {"factor_a": [1.0, np.nan, 3.0], "factor_b": [np.nan, 2.0, np.nan]},
            index=pd.date_range("2025-01-01", periods=3),
        )
        records = _factors_to_records("TEST", df)
        # factor_a: 2 non-NaN, factor_b: 1 non-NaN → total 3
        assert len(records) == 3
        for r in records:
            assert not pd.isna(r["value"])

    def test_all_nan_produces_empty(self):
        """All-NaN DataFrame must produce no records."""
        df = pd.DataFrame(
            {"f1": [np.nan, np.nan]},
            index=pd.date_range("2025-01-01", periods=2),
        )
        records = _factors_to_records("TEST", df)
        assert records == []

    def test_custom_version(self, factors_df):
        """Custom version string should propagate to records."""
        records = _factors_to_records("KS200", factors_df, version="v2")
        assert all(r["version"] == "v2" for r in records)

    def test_factor_names_match(self, factors_df):
        """All factor names in records should be from ALL_FACTOR_NAMES."""
        records = _factors_to_records("KS200", factors_df)
        factor_names = {r["factor_name"] for r in records}
        assert factor_names == set(ALL_FACTOR_NAMES)

    def test_date_is_date_not_datetime(self, factors_df):
        """Date values should be date objects, not datetime."""
        import datetime

        records = _factors_to_records("KS200", factors_df)
        for r in records:
            assert isinstance(r["date"], datetime.date)


# --- _upsert_factors ---


class TestUpsertFactors:
    def test_upsert_uses_on_conflict(self):
        """Must use INSERT ... ON CONFLICT DO UPDATE."""
        records = [{
            "asset_id": "KS200", "date": "2025-01-02",
            "factor_name": "ret_1d", "version": "v1", "value": 0.01,
        }]
        mock_session = MagicMock()
        row_count = _upsert_factors(mock_session, records)

        assert row_count == 1
        mock_session.execute.assert_called_once()
        mock_session.flush.assert_called_once()

        stmt = mock_session.execute.call_args[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": False}))
        assert "ON CONFLICT" in compiled
        assert "DO UPDATE SET" in compiled

    def test_upsert_chunking(self):
        """Chunk size should control number of execute calls."""
        records = [
            {
                "asset_id": "T", "date": f"2025-01-0{i}",
                "factor_name": "ret_1d", "version": "v1", "value": 0.01,
            }
            for i in range(1, 6)
        ]
        mock_session = MagicMock()
        row_count = _upsert_factors(mock_session, records, chunk_size=2)

        assert row_count == 5
        assert mock_session.execute.call_count == 3  # 2+2+1

    def test_empty_records(self):
        """Empty records should produce zero rows and no execute calls."""
        mock_session = MagicMock()
        row_count = _upsert_factors(mock_session, [])
        assert row_count == 0
        mock_session.execute.assert_not_called()


# --- store_factors_for_asset ---


class TestStoreFactorsForAsset:
    def test_success(self, ohlcv):
        """Successful pipeline: preprocess → compute → store."""
        mock_session = MagicMock()

        with (
            patch("research_engine.factor_store.preprocess", return_value=ohlcv),
            patch("research_engine.factor_store._upsert_factors", return_value=1000),
        ):
            result = store_factors_for_asset(mock_session, "KS200")

        assert result.status == "success"
        assert result.row_count == 1000
        assert result.factor_count == 15
        assert result.errors == []
        assert result.elapsed_ms > 0
        mock_session.commit.assert_called_once()

    def test_preprocess_failure(self):
        """Preprocess error → status='preprocess_failed'."""
        mock_session = MagicMock()

        with patch("research_engine.factor_store.preprocess", side_effect=ValueError("No data")):
            result = store_factors_for_asset(mock_session, "KS200")

        assert result.status == "preprocess_failed"
        assert any("No data" in e for e in result.errors)
        mock_session.commit.assert_not_called()

    def test_compute_failure(self, ohlcv):
        """Factor computation error → status='compute_failed'."""
        mock_session = MagicMock()
        bad_df = ohlcv.drop(columns=["close"])  # missing column

        with patch("research_engine.factor_store.preprocess", return_value=bad_df):
            result = store_factors_for_asset(mock_session, "KS200")

        assert result.status == "compute_failed"
        assert len(result.errors) > 0

    def test_store_failure(self, ohlcv):
        """DB upsert error → status='store_failed', rollback called."""
        mock_session = MagicMock()

        with (
            patch("research_engine.factor_store.preprocess", return_value=ohlcv),
            patch(
                "research_engine.factor_store._upsert_factors",
                side_effect=RuntimeError("DB error"),
            ),
        ):
            result = store_factors_for_asset(mock_session, "KS200")

        assert result.status == "store_failed"
        assert any("DB error" in e for e in result.errors)
        mock_session.rollback.assert_called_once()


# --- store_factors_all ---


class TestStoreFactorsAll:
    def test_explicit_asset_ids(self, ohlcv):
        """Given asset_ids should be used directly."""
        mock_session = MagicMock()

        with (
            patch("research_engine.factor_store.preprocess", return_value=ohlcv),
            patch("research_engine.factor_store._upsert_factors", return_value=100),
        ):
            results = store_factors_all(mock_session, asset_ids=["KS200", "005930"])

        assert len(results) == 2
        assert all(r.status == "success" for r in results)

    def test_partial_failure(self, ohlcv):
        """One asset failure must not stop others."""
        mock_session = MagicMock()
        call_count = {"n": 0}

        def mock_preprocess(session, asset_id, start=None, end=None, **kwargs):
            call_count["n"] += 1
            if asset_id == "005930":
                raise ValueError("No data for 005930")
            return ohlcv

        with (
            patch("research_engine.factor_store.preprocess", side_effect=mock_preprocess),
            patch("research_engine.factor_store._upsert_factors", return_value=100),
        ):
            results = store_factors_all(mock_session, asset_ids=["KS200", "005930", "SOXL"])

        statuses = {r.asset_id: r.status for r in results}
        assert statuses["KS200"] == "success"
        assert statuses["005930"] == "preprocess_failed"
        assert statuses["SOXL"] == "success"

    def test_fallback_to_symbol_map(self, ohlcv):
        """When asset_ids is None and asset_master query fails, fall back to SYMBOL_MAP."""
        mock_session = MagicMock()
        mock_session.query.side_effect = Exception("DB unavailable")

        with (
            patch("research_engine.factor_store.preprocess", return_value=ohlcv),
            patch("research_engine.factor_store._upsert_factors", return_value=100),
            patch("collector.fdr_client.SYMBOL_MAP", {"T1": {}, "T2": {}}),
        ):
            results = store_factors_all(mock_session)

        assert len(results) == 2

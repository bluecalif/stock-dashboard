"""Tests for research_engine.factor_store module."""

import numpy as np
import pandas as pd

from research_engine.factor_store import (
    FactorStoreResult,
    _factors_to_records,
    _upsert_factors,
)
from research_engine.factors import ALL_FACTOR_NAMES, FACTOR_VERSION


def _make_ohlcv(n=150):
    """Helper: create OHLCV DataFrame with enough rows for all factors."""
    dates = pd.bdate_range("2024-01-02", periods=n)
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    return pd.DataFrame(
        {
            "open": close * 0.999,
            "high": close * 1.02,
            "low": close * 0.98,
            "close": close,
            "volume": np.random.randint(1000, 100000, n),
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )


def _make_factor_df():
    """Helper: create a small factor DataFrame with known values."""
    dates = pd.date_range("2024-06-01", periods=3, freq="B")
    data = {}
    for i, name in enumerate(ALL_FACTOR_NAMES):
        data[name] = [float(i + j) for j in range(3)]
    return pd.DataFrame(data, index=pd.DatetimeIndex(dates, name="date"))


# --- FactorStoreResult ---


class TestFactorStoreResult:
    def test_default_values(self):
        r = FactorStoreResult(asset_id="005930", status="success")
        assert r.row_count == 0
        assert r.errors == []
        assert r.elapsed_ms == 0.0

    def test_with_values(self):
        r = FactorStoreResult(
            asset_id="KS200",
            status="preprocess_failed",
            errors=["No data"],
            elapsed_ms=123.4,
        )
        assert r.asset_id == "KS200"
        assert r.status == "preprocess_failed"
        assert len(r.errors) == 1


# --- _factors_to_records ---


class TestFactorsToRecords:
    def test_basic_conversion(self):
        df = _make_factor_df()
        records = _factors_to_records("005930", df)
        # 3 dates × 15 factors = 45 records
        assert len(records) == 45

    def test_record_structure(self):
        df = _make_factor_df()
        records = _factors_to_records("KS200", df)
        r = records[0]
        assert set(r.keys()) == {"asset_id", "date", "factor_name", "version", "value"}
        assert r["asset_id"] == "KS200"
        assert r["version"] == FACTOR_VERSION

    def test_nan_values_skipped(self):
        df = _make_factor_df()
        # Set some NaN values
        df.iloc[0, 0] = np.nan  # ret_1d at row 0
        df.iloc[1, 1] = np.nan  # ret_5d at row 1
        records = _factors_to_records("005930", df)
        assert len(records) == 43  # 45 - 2 NaN

    def test_all_nan_row(self):
        df = _make_factor_df()
        df.iloc[0] = np.nan
        records = _factors_to_records("005930", df)
        # row 0 all NaN → skip 15, remaining 2 rows × 15 = 30
        assert len(records) == 30

    def test_empty_dataframe(self):
        df = pd.DataFrame(columns=ALL_FACTOR_NAMES)
        df.index.name = "date"
        records = _factors_to_records("005930", df)
        assert len(records) == 0

    def test_custom_version(self):
        df = _make_factor_df().head(1)
        records = _factors_to_records("005930", df, version="v2")
        assert all(r["version"] == "v2" for r in records)

    def test_date_converted_to_date_object(self):
        df = _make_factor_df()
        records = _factors_to_records("005930", df)
        import datetime

        assert isinstance(records[0]["date"], datetime.date)

    def test_value_is_float(self):
        df = _make_factor_df()
        records = _factors_to_records("005930", df)
        for r in records:
            assert isinstance(r["value"], float)

    def test_all_factor_names_present(self):
        df = _make_factor_df()
        records = _factors_to_records("005930", df)
        factor_names = {r["factor_name"] for r in records}
        assert factor_names == set(ALL_FACTOR_NAMES)


# --- _upsert_factors (with mock session) ---


class MockSession:
    """Minimal mock for SQLAlchemy session to test upsert logic."""

    def __init__(self):
        self.executed = []
        self.flushed = False

    def execute(self, stmt):
        self.executed.append(stmt)

    def flush(self):
        self.flushed = True


class TestUpsertFactors:
    def test_single_chunk(self):
        df = _make_factor_df().head(1)
        records = _factors_to_records("005930", df)
        session = MockSession()
        count = _upsert_factors(session, records, chunk_size=1000)
        assert count == 15
        assert len(session.executed) == 1
        assert session.flushed

    def test_multiple_chunks(self):
        df = _make_factor_df()
        records = _factors_to_records("005930", df)
        session = MockSession()
        count = _upsert_factors(session, records, chunk_size=10)
        assert count == 45
        # 45 / 10 = 5 chunks (10, 10, 10, 10, 5)
        assert len(session.executed) == 5
        assert session.flushed

    def test_empty_records(self):
        session = MockSession()
        count = _upsert_factors(session, [], chunk_size=1000)
        assert count == 0
        assert session.flushed


# --- Integration: compute_all_factors → _factors_to_records ---


class TestComputeAndConvert:
    def test_roundtrip(self):
        """Verify that compute_all_factors output converts correctly to records."""
        from research_engine.factors import compute_all_factors

        df = _make_ohlcv(150)
        factor_df = compute_all_factors(df)
        records = _factors_to_records("005930", factor_df)

        # Should have records (some early rows will be NaN but most should be valid)
        assert len(records) > 0

        # All records should have valid structure
        for r in records:
            assert r["asset_id"] == "005930"
            assert r["version"] == FACTOR_VERSION
            assert r["factor_name"] in ALL_FACTOR_NAMES
            assert isinstance(r["value"], float)
            assert not np.isnan(r["value"])

    def test_no_nan_in_records(self):
        """Ensure no NaN values leak into records."""
        from research_engine.factors import compute_all_factors

        df = _make_ohlcv(150)
        factor_df = compute_all_factors(df)
        records = _factors_to_records("005930", factor_df)

        for r in records:
            assert not np.isnan(r["value"]), f"NaN in {r['factor_name']} at {r['date']}"

    def test_factor_count_matches(self):
        """All 15 factor names should appear in output records."""
        from research_engine.factors import compute_all_factors

        df = _make_ohlcv(150)
        factor_df = compute_all_factors(df)
        records = _factors_to_records("005930", factor_df)

        factor_names = {r["factor_name"] for r in records}
        assert factor_names == set(ALL_FACTOR_NAMES)

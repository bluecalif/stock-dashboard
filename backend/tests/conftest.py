"""Shared test fixtures for collector tests."""

from datetime import datetime, timezone

import pandas as pd
import pytest


@pytest.fixture
def sample_ohlcv_df():
    """Valid OHLCV DataFrame for testing."""
    return pd.DataFrame({
        "asset_id": ["KS200"] * 3,
        "date": pd.to_datetime(["2026-01-02", "2026-01-03", "2026-01-06"]),
        "open": [100.0, 102.0, 101.0],
        "high": [105.0, 106.0, 104.0],
        "low": [98.0, 100.0, 99.0],
        "close": [103.0, 104.0, 102.0],
        "volume": [50000, 60000, 55000],
        "source": ["fdr"] * 3,
        "ingested_at": [datetime.now(timezone.utc)] * 3,
    })


@pytest.fixture
def invalid_ohlcv_high_low():
    """DataFrame with high < low inversion."""
    return pd.DataFrame({
        "asset_id": ["KS200"] * 2,
        "date": pd.to_datetime(["2026-01-02", "2026-01-03"]),
        "open": [100.0, 102.0],
        "high": [95.0, 106.0],  # row 0: high < low
        "low": [98.0, 100.0],
        "close": [103.0, 104.0],
        "volume": [50000, 60000],
        "source": ["fdr"] * 2,
        "ingested_at": [datetime.now(timezone.utc)] * 2,
    })


@pytest.fixture
def invalid_ohlcv_negative():
    """DataFrame with negative prices."""
    return pd.DataFrame({
        "asset_id": ["KS200"] * 2,
        "date": pd.to_datetime(["2026-01-02", "2026-01-03"]),
        "open": [-100.0, 102.0],
        "high": [105.0, 106.0],
        "low": [98.0, 100.0],
        "close": [103.0, 104.0],
        "volume": [50000, 60000],
        "source": ["fdr"] * 2,
        "ingested_at": [datetime.now(timezone.utc)] * 2,
    })


@pytest.fixture
def mock_fdr_dataframe():
    """Raw FDR-style DataFrame (before standardization)."""
    df = pd.DataFrame({
        "Open": [100.0, 102.0],
        "High": [105.0, 106.0],
        "Low": [98.0, 100.0],
        "Close": [103.0, 104.0],
        "Volume": [50000, 60000],
    }, index=pd.DatetimeIndex(["2026-01-02", "2026-01-03"], name="Date"))
    return df

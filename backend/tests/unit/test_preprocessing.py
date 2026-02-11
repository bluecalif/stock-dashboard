"""Tests for research_engine.preprocessing module."""

import numpy as np
import pandas as pd
import pytest

from research_engine.preprocessing import (
    align_calendar,
    check_missing,
    flag_outliers,
    get_category,
    preprocess_from_df,
)


def _make_df(dates, closes, volumes=None):
    """Helper: create a simple OHLCV DataFrame indexed by date."""
    n = len(dates)
    if volumes is None:
        volumes = [10000] * n
    df = pd.DataFrame(
        {
            "open": closes,
            "high": [c * 1.02 for c in closes],
            "low": [c * 0.98 for c in closes],
            "close": closes,
            "volume": volumes,
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )
    return df


# --- get_category ---


class TestGetCategory:
    def test_known_stock(self):
        assert get_category("005930") == "stock"

    def test_known_crypto(self):
        assert get_category("BTC") == "crypto"

    def test_known_commodity(self):
        assert get_category("GC=F") == "commodity"

    def test_unknown(self):
        assert get_category("UNKNOWN") == "unknown"


# --- align_calendar ---


class TestAlignCalendar:
    def test_stock_fills_business_days(self):
        """Mon, Wed → should fill Tue."""
        dates = ["2026-01-05", "2026-01-07"]  # Mon, Wed
        df = _make_df(dates, [100.0, 102.0])
        result = align_calendar(df, "stock")

        assert len(result) == 3  # Mon, Tue, Wed
        assert result["is_filled"].iloc[1]
        assert result["close"].iloc[1] == 100.0  # ffill from Mon
        assert result["volume"].iloc[1] == 0  # filled row has 0 volume

    def test_stock_excludes_weekends(self):
        """Fri to next Mon → 2 rows (no Sat/Sun)."""
        dates = ["2026-01-09", "2026-01-12"]  # Fri, Mon
        df = _make_df(dates, [100.0, 102.0])
        result = align_calendar(df, "stock")

        assert len(result) == 2  # Fri and Mon only, no weekend

    def test_crypto_includes_weekends(self):
        """Fri to Mon → 4 rows including Sat, Sun."""
        dates = ["2026-01-09", "2026-01-12"]  # Fri, Mon
        df = _make_df(dates, [100.0, 102.0])
        result = align_calendar(df, "crypto")

        assert len(result) == 4  # Fri, Sat, Sun, Mon
        assert result["is_filled"].sum() == 2  # Sat, Sun filled

    def test_empty_df(self):
        df = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([], name="date"),
        )
        result = align_calendar(df, "stock")
        assert len(result) == 0
        assert "is_filled" in result.columns

    def test_single_row(self):
        df = _make_df(["2026-01-05"], [100.0])
        result = align_calendar(df, "stock")
        assert len(result) == 1
        assert not result["is_filled"].iloc[0]

    def test_no_gap(self):
        """Consecutive business days → no fills."""
        dates = ["2026-01-05", "2026-01-06", "2026-01-07"]  # Mon, Tue, Wed
        df = _make_df(dates, [100.0, 101.0, 102.0])
        result = align_calendar(df, "stock")
        assert len(result) == 3
        assert result["is_filled"].sum() == 0


# --- check_missing ---


class TestCheckMissing:
    def test_no_missing(self):
        df = _make_df(["2026-01-05", "2026-01-06"], [100.0, 101.0])
        df = align_calendar(df, "stock")
        is_ok, ratio, count = check_missing(df, threshold=0.05)
        assert is_ok is True
        assert count == 0
        assert ratio == 0.0

    def test_within_threshold(self):
        """1 filled out of 21 rows = ~4.8% < 5%."""
        dates = pd.bdate_range("2026-01-05", periods=20).tolist()
        dates.pop(5)  # remove one business day
        closes = [100.0 + i for i in range(len(dates))]
        df = _make_df(dates, closes)
        df = align_calendar(df, "stock")

        is_ok, ratio, count = check_missing(df, threshold=0.05)
        assert is_ok is True
        assert count == 1

    def test_exceeds_threshold(self):
        """Many gaps → fails."""
        dates = ["2026-01-05", "2026-01-19"]  # 2-week gap
        df = _make_df(dates, [100.0, 110.0])
        df = align_calendar(df, "stock")

        is_ok, ratio, count = check_missing(df, threshold=0.05)
        assert is_ok is False
        assert count > 1

    def test_empty_df(self):
        df = pd.DataFrame(columns=["close"])
        is_ok, ratio, count = check_missing(df)
        assert is_ok is False

    def test_without_is_filled_column(self):
        """Falls back to counting NaN in close."""
        df = pd.DataFrame(
            {"close": [100.0, np.nan, 102.0]},
            index=pd.date_range("2026-01-05", periods=3),
        )
        is_ok, ratio, count = check_missing(df, threshold=0.5)
        assert is_ok is True
        assert count == 1


# --- flag_outliers ---


class TestFlagOutliers:
    def test_no_outliers_normal_data(self):
        closes = [100.0 + i * 0.5 for i in range(20)]
        df = _make_df(pd.bdate_range("2026-01-05", periods=20), closes)
        result = flag_outliers(df)
        assert result["is_outlier"].sum() == 0

    def test_detects_spike(self):
        """One extreme return should be flagged."""
        closes = [100.0] * 19 + [200.0]  # 100% jump at the end
        df = _make_df(pd.bdate_range("2026-01-05", periods=20), closes)
        result = flag_outliers(df, z_threshold=3.0)
        assert result["is_outlier"].iloc[-1]

    def test_first_row_never_outlier(self):
        closes = [200.0, 100.0, 100.0, 100.0, 100.0]
        df = _make_df(pd.bdate_range("2026-01-05", periods=5), closes)
        result = flag_outliers(df)
        assert not result["is_outlier"].iloc[0]

    def test_constant_prices(self):
        """All same price → std=0 → no outliers."""
        closes = [100.0] * 10
        df = _make_df(pd.bdate_range("2026-01-05", periods=10), closes)
        result = flag_outliers(df)
        assert result["is_outlier"].sum() == 0


# --- preprocess_from_df ---


class TestPreprocessFromDf:
    def test_full_pipeline(self):
        dates = pd.bdate_range("2026-01-05", periods=20)
        closes = [100.0 + i * 0.5 for i in range(20)]
        df = _make_df(dates, closes)
        result = preprocess_from_df(df, category="stock")

        assert "is_filled" in result.columns
        assert "is_outlier" in result.columns
        assert len(result) == 20

    def test_raises_on_too_many_missing(self):
        dates = ["2026-01-05", "2026-02-06"]
        df = _make_df(dates, [100.0, 110.0])

        with pytest.raises(ValueError, match="Missing data"):
            preprocess_from_df(df, category="stock", missing_threshold=0.01)

    def test_crypto_pipeline(self):
        dates = pd.date_range("2026-01-05", periods=10, freq="D")
        closes = [50000.0 + i * 100 for i in range(10)]
        df = _make_df(dates, closes)
        result = preprocess_from_df(df, category="crypto")

        assert len(result) == 10
        assert result["is_filled"].sum() == 0

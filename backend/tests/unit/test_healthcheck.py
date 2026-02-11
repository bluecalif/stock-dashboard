"""Tests for scripts/healthcheck.py — data freshness check."""

from datetime import date
from unittest.mock import MagicMock

from scripts.healthcheck import (
    check_freshness,
    expected_latest_date,
    format_healthcheck_message,
    previous_business_day,
)

# --- previous_business_day ---


class TestPreviousBusinessDay:
    def test_friday_from_monday(self):
        # Monday 2026-02-09 → previous bday = Friday 2026-02-06
        assert previous_business_day(date(2026, 2, 9)) == date(2026, 2, 6)

    def test_thursday_from_friday(self):
        # Friday 2026-02-06 → Thursday 2026-02-05
        assert previous_business_day(date(2026, 2, 6)) == date(2026, 2, 5)

    def test_friday_from_saturday(self):
        # Saturday 2026-02-07 → Friday 2026-02-06
        assert previous_business_day(date(2026, 2, 7)) == date(2026, 2, 6)

    def test_friday_from_sunday(self):
        # Sunday 2026-02-08 → Friday 2026-02-06
        assert previous_business_day(date(2026, 2, 8)) == date(2026, 2, 6)


# --- expected_latest_date ---


class TestExpectedLatestDate:
    def test_stock_on_monday(self):
        # Monday → expect Friday
        assert expected_latest_date("stock", date(2026, 2, 9)) == date(2026, 2, 6)

    def test_stock_on_wednesday(self):
        # Wednesday → expect Tuesday
        assert expected_latest_date("stock", date(2026, 2, 11)) == date(2026, 2, 10)

    def test_crypto_on_monday(self):
        # Crypto: always yesterday regardless of weekday
        assert expected_latest_date("crypto", date(2026, 2, 9)) == date(2026, 2, 8)

    def test_crypto_on_sunday(self):
        assert expected_latest_date("crypto", date(2026, 2, 8)) == date(2026, 2, 7)

    def test_commodity_same_as_stock(self):
        assert expected_latest_date("commodity", date(2026, 2, 9)) == date(2026, 2, 6)

    def test_index_same_as_stock(self):
        assert expected_latest_date("index", date(2026, 2, 11)) == date(2026, 2, 10)

    def test_etf_same_as_stock(self):
        assert expected_latest_date("etf", date(2026, 2, 11)) == date(2026, 2, 10)


# --- check_freshness (mocked DB) ---


def _make_mock_session(rows):
    """Create a mock session that returns given rows from execute()."""
    mock_session = MagicMock()
    mock_result = MagicMock()
    mock_result.all.return_value = rows
    mock_session.execute.return_value = mock_result
    return mock_session


class TestCheckFreshness:
    def test_all_fresh(self):
        today = date(2026, 2, 11)  # Wednesday
        expected_stock = date(2026, 2, 10)  # Tuesday
        expected_crypto = date(2026, 2, 10)  # Yesterday

        rows = [
            ("005930", "삼성전자", "stock", expected_stock),
            ("BTC", "Bitcoin", "crypto", expected_crypto),
        ]
        session = _make_mock_session(rows)
        results = check_freshness(session, today=today)

        assert len(results) == 2
        assert all(r["status"] == "OK" for r in results)

    def test_detects_stale_asset(self):
        today = date(2026, 2, 11)  # Wednesday

        rows = [
            ("005930", "삼성전자", "stock", date(2026, 2, 7)),  # Friday — stale
            ("BTC", "Bitcoin", "crypto", date(2026, 2, 10)),  # Yesterday — OK
        ]
        session = _make_mock_session(rows)
        results = check_freshness(session, today=today)

        stock = next(r for r in results if r["asset_id"] == "005930")
        crypto = next(r for r in results if r["asset_id"] == "BTC")

        assert stock["status"] == "STALE"
        assert crypto["status"] == "OK"

    def test_detects_no_data(self):
        today = date(2026, 2, 11)

        rows = [
            ("SOXL", "SOXL ETF", "etf", None),  # No data at all
        ]
        session = _make_mock_session(rows)
        results = check_freshness(session, today=today)

        assert results[0]["status"] == "NO_DATA"
        assert results[0]["actual_date"] is None

    def test_ok_when_ahead_of_expected(self):
        today = date(2026, 2, 11)

        rows = [
            ("BTC", "Bitcoin", "crypto", date(2026, 2, 11)),  # Today — ahead of T-1
        ]
        session = _make_mock_session(rows)
        results = check_freshness(session, today=today)

        assert results[0]["status"] == "OK"


# --- format_healthcheck_message ---


class TestFormatMessage:
    def test_includes_stale_assets(self):
        results = [
            {"asset_id": "005930", "name": "삼성전자", "category": "stock",
             "expected_date": "2026-02-10", "actual_date": "2026-02-07", "status": "STALE"},
            {"asset_id": "BTC", "name": "Bitcoin", "category": "crypto",
             "expected_date": "2026-02-10", "actual_date": "2026-02-10", "status": "OK"},
        ]
        msg = format_healthcheck_message(results)

        assert "005930" in msg
        assert "STALE" in msg
        assert "BTC" not in msg  # OK assets excluded

    def test_no_data_shown(self):
        results = [
            {"asset_id": "SOXL", "name": "SOXL ETF", "category": "etf",
             "expected_date": "2026-02-10", "actual_date": None, "status": "NO_DATA"},
        ]
        msg = format_healthcheck_message(results)

        assert "SOXL" in msg
        assert "없음" in msg

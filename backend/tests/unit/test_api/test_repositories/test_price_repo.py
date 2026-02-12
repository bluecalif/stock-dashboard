"""Tests for price_repo."""

import datetime

from api.repositories import price_repo


class TestGetPrices:
    def test_returns_all_for_asset(self, db, seed_prices):
        result = price_repo.get_prices(db, "KS200")
        assert len(result) == 5

    def test_order_desc(self, db, seed_prices):
        result = price_repo.get_prices(db, "KS200")
        dates = [r.date for r in result]
        assert dates == sorted(dates, reverse=True)

    def test_date_filter_start(self, db, seed_prices):
        result = price_repo.get_prices(db, "KS200", start_date=datetime.date(2026, 1, 8))
        assert all(r.date >= datetime.date(2026, 1, 8) for r in result)
        assert len(result) == 2  # Jan 8, Jan 9

    def test_date_filter_end(self, db, seed_prices):
        result = price_repo.get_prices(db, "KS200", end_date=datetime.date(2026, 1, 6))
        assert all(r.date <= datetime.date(2026, 1, 6) for r in result)
        assert len(result) == 2  # Jan 5, Jan 6

    def test_pagination(self, db, seed_prices):
        page1 = price_repo.get_prices(db, "KS200", limit=2, offset=0)
        page2 = price_repo.get_prices(db, "KS200", limit=2, offset=2)
        assert len(page1) == 2
        assert len(page2) == 2
        assert page1[0].date != page2[0].date

    def test_empty_result(self, db, seed_prices):
        result = price_repo.get_prices(db, "NONEXIST")
        assert result == []


class TestGetLatestPrice:
    def test_returns_latest(self, db, seed_prices):
        result = price_repo.get_latest_price(db, "KS200")
        assert result is not None
        assert result.date == datetime.date(2026, 1, 9)

    def test_none_for_missing(self, db, seed_assets):
        result = price_repo.get_latest_price(db, "NONEXIST")
        assert result is None

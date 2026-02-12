"""Tests for factor_repo."""

import datetime

from api.repositories import factor_repo


class TestGetFactors:
    def test_returns_all(self, db, seed_factors):
        result = factor_repo.get_factors(db)
        assert len(result) == 4

    def test_filter_asset(self, db, seed_factors):
        result = factor_repo.get_factors(db, asset_id="KS200")
        assert len(result) == 4

    def test_filter_asset_no_match(self, db, seed_factors):
        result = factor_repo.get_factors(db, asset_id="NONEXIST")
        assert result == []

    def test_filter_factor_name(self, db, seed_factors):
        result = factor_repo.get_factors(db, factor_name="momentum_20d")
        assert len(result) == 4

    def test_date_filter(self, db, seed_factors):
        result = factor_repo.get_factors(
            db,
            start_date=datetime.date(2026, 1, 6),
            end_date=datetime.date(2026, 1, 7),
        )
        assert len(result) == 2

    def test_pagination(self, db, seed_factors):
        result = factor_repo.get_factors(db, limit=2, offset=0)
        assert len(result) == 2

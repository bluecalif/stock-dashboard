"""Tests for asset_repo."""

from api.repositories import asset_repo


class TestGetAll:
    def test_returns_all(self, db, seed_assets):
        result = asset_repo.get_all(db)
        assert len(result) == 3

    def test_filter_active(self, db, seed_assets):
        result = asset_repo.get_all(db, is_active=True)
        assert len(result) == 2
        assert all(a.is_active for a in result)

    def test_filter_inactive(self, db, seed_assets):
        result = asset_repo.get_all(db, is_active=False)
        assert len(result) == 1
        assert result[0].asset_id == "INACTIVE"

    def test_empty_db(self, db):
        result = asset_repo.get_all(db)
        assert result == []

    def test_order_by_asset_id(self, db, seed_assets):
        result = asset_repo.get_all(db)
        ids = [a.asset_id for a in result]
        assert ids == sorted(ids)

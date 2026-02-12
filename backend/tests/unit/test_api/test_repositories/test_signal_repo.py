"""Tests for signal_repo."""

import datetime

from api.repositories import signal_repo


class TestGetSignals:
    def test_returns_all(self, db, seed_signals):
        result = signal_repo.get_signals(db)
        assert len(result) == 4

    def test_filter_asset(self, db, seed_signals):
        result = signal_repo.get_signals(db, asset_id="KS200")
        assert len(result) == 4

    def test_filter_strategy(self, db, seed_signals):
        result = signal_repo.get_signals(db, strategy_id="mom_20")
        assert len(result) == 2

    def test_date_filter(self, db, seed_signals):
        result = signal_repo.get_signals(db, start_date=datetime.date(2026, 1, 6))
        assert len(result) == 2

    def test_empty(self, db, seed_signals):
        result = signal_repo.get_signals(db, asset_id="NONEXIST")
        assert result == []


class TestGetLatestSignal:
    def test_returns_latest(self, db, seed_signals):
        result = signal_repo.get_latest_signal(db, "KS200")
        assert result is not None
        assert result.date == datetime.date(2026, 1, 6)

    def test_filter_strategy(self, db, seed_signals):
        result = signal_repo.get_latest_signal(db, "KS200", strategy_id="trend_60")
        assert result is not None
        assert result.strategy_id == "trend_60"
        assert result.date == datetime.date(2026, 1, 6)

    def test_none_for_missing(self, db, seed_signals):
        result = signal_repo.get_latest_signal(db, "NONEXIST")
        assert result is None

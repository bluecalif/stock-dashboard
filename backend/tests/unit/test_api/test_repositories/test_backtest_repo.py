"""Tests for backtest_repo."""

import datetime
import uuid

from db.models import BacktestEquityCurve, BacktestRun, BacktestTradeLog
from api.repositories import backtest_repo


class TestGetRuns:
    def test_returns_all(self, db, seed_backtest):
        result = backtest_repo.get_runs(db)
        assert len(result) == 1

    def test_filter_strategy(self, db, seed_backtest):
        result = backtest_repo.get_runs(db, strategy_id="mom_20")
        assert len(result) == 1

    def test_filter_no_match(self, db, seed_backtest):
        result = backtest_repo.get_runs(db, strategy_id="nonexist")
        assert result == []

    def test_filter_asset(self, db, seed_backtest):
        result = backtest_repo.get_runs(db, asset_id="KS200")
        assert len(result) == 1


class TestGetRunById:
    def test_found(self, db, seed_backtest):
        run_id = seed_backtest.run_id
        result = backtest_repo.get_run_by_id(db, run_id)
        assert result is not None
        assert result.strategy_id == "mom_20"

    def test_not_found(self, db, seed_backtest):
        result = backtest_repo.get_run_by_id(db, uuid.uuid4())
        assert result is None


class TestEquityCurve:
    def test_returns_curve(self, db, seed_backtest):
        result = backtest_repo.get_equity_curve(db, seed_backtest.run_id)
        assert len(result) == 3
        dates = [r.date for r in result]
        assert dates == sorted(dates)  # asc order


class TestTrades:
    def test_returns_trades(self, db, seed_backtest):
        result = backtest_repo.get_trades(db, seed_backtest.run_id)
        assert len(result) == 1
        assert result[0].side == "long"


class TestCreateRun:
    def test_insert_and_return(self, db, seed_assets):
        run = BacktestRun(
            run_id=uuid.uuid4(),
            strategy_id="test_strat",
            asset_id="KS200",
            config_json={"param": 1},
            started_at=datetime.datetime(2026, 2, 1, 10, 0, tzinfo=datetime.timezone.utc),
            status="running",
        )
        result = backtest_repo.create_run(db, run)
        assert result.strategy_id == "test_strat"
        # Verify it's in DB
        found = backtest_repo.get_run_by_id(db, run.run_id)
        assert found is not None


class TestBulkInsert:
    def test_bulk_equity(self, db, seed_backtest):
        run_id = seed_backtest.run_id
        new_rows = [
            BacktestEquityCurve(run_id=run_id, date=datetime.date(2026, 1, 10), equity=10500, drawdown=0.01),
        ]
        backtest_repo.bulk_insert_equity(db, new_rows)
        result = backtest_repo.get_equity_curve(db, run_id)
        assert len(result) == 4

    def test_bulk_trades(self, db, seed_backtest):
        run_id = seed_backtest.run_id
        new_rows = [
            BacktestTradeLog(
                run_id=run_id, asset_id="KS200",
                entry_date=datetime.date(2026, 1, 8), entry_price=102.0,
                side="short", shares=5,
            ),
        ]
        backtest_repo.bulk_insert_trades(db, new_rows)
        result = backtest_repo.get_trades(db, run_id)
        assert len(result) == 2

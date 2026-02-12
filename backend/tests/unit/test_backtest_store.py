"""Tests for backtest_store module."""

from __future__ import annotations

import uuid
from datetime import date
from unittest.mock import MagicMock

import pandas as pd

from research_engine.backtest import BacktestConfig, BacktestResult, TradeRecord
from research_engine.backtest_store import (
    BacktestStoreResult,
    _config_to_dict,
    _equity_curve_to_records,
    _trades_to_records,
    store_backtest_result,
)
from research_engine.metrics import PerformanceMetrics

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_equity_curve(n: int = 5) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=n, freq="B")
    return pd.DataFrame({
        "date": dates,
        "equity": [10_000_000 + i * 100_000 for i in range(n)],
        "drawdown": [0.0] * n,
    })


def _make_trades(n: int = 2) -> list[TradeRecord]:
    return [
        TradeRecord(
            asset_id="005930",
            entry_date=date(2024, 1, 2),
            entry_price=70000.0,
            exit_date=date(2024, 1, 5),
            exit_price=72000.0,
            side="long",
            shares=100.0,
            pnl=200000.0,
            cost=14200.0,
        ),
        TradeRecord(
            asset_id="005930",
            entry_date=date(2024, 1, 8),
            entry_price=71000.0,
            exit_date=None,
            exit_price=None,
            side="long",
            shares=100.0,
            pnl=None,
            cost=7100.0,
        ),
    ][:n]


def _make_backtest_result() -> BacktestResult:
    return BacktestResult(
        strategy_id="momentum_v1",
        asset_id="005930",
        config=BacktestConfig(),
        equity_curve=_make_equity_curve(),
        trades=_make_trades(),
        buy_hold_equity=pd.DataFrame(),
    )


def _make_metrics() -> PerformanceMetrics:
    return PerformanceMetrics(
        total_return=0.05,
        cagr=0.12,
        mdd=-0.08,
        volatility=0.15,
        sharpe=0.8,
        sortino=1.2,
        calmar=1.5,
        win_rate=0.6,
        num_trades=2,
        avg_trade_pnl=100000.0,
        turnover=0.5,
        bh_total_return=0.03,
        bh_cagr=0.07,
        excess_return=0.02,
    )


# ---------------------------------------------------------------------------
# _config_to_dict tests
# ---------------------------------------------------------------------------

class TestConfigToDict:
    def test_default_config(self):
        d = _config_to_dict(BacktestConfig())
        assert d["initial_cash"] == 10_000_000
        assert d["commission_pct"] == 0.001
        assert d["slippage_pct"] == 0.0
        assert d["allow_short"] is False

    def test_custom_config(self):
        cfg = BacktestConfig(initial_cash=5_000_000, commission_pct=0.002)
        d = _config_to_dict(cfg)
        assert d["initial_cash"] == 5_000_000
        assert d["commission_pct"] == 0.002


# ---------------------------------------------------------------------------
# _equity_curve_to_records tests
# ---------------------------------------------------------------------------

class TestEquityCurveToRecords:
    def test_basic_conversion(self):
        run_id = uuid.uuid4()
        df = _make_equity_curve(3)
        records = _equity_curve_to_records(run_id, df)

        assert len(records) == 3
        assert all(r["run_id"] == run_id for r in records)
        assert records[0]["equity"] == 10_000_000
        assert records[2]["equity"] == 10_200_000
        assert all(isinstance(r["date"], date) for r in records)

    def test_empty_df(self):
        run_id = uuid.uuid4()
        df = pd.DataFrame(columns=["date", "equity", "drawdown"])
        records = _equity_curve_to_records(run_id, df)
        assert records == []


# ---------------------------------------------------------------------------
# _trades_to_records tests
# ---------------------------------------------------------------------------

class TestTradesToRecords:
    def test_basic_conversion(self):
        run_id = uuid.uuid4()
        trades = _make_trades(2)
        records = _trades_to_records(run_id, trades)

        assert len(records) == 2
        assert all(r["run_id"] == run_id for r in records)
        assert records[0]["entry_price"] == 70000.0
        assert records[0]["exit_price"] == 72000.0
        assert records[0]["shares"] == 100.0
        assert records[1]["exit_date"] is None
        assert records[1]["pnl"] is None

    def test_empty_trades(self):
        run_id = uuid.uuid4()
        records = _trades_to_records(run_id, [])
        assert records == []


# ---------------------------------------------------------------------------
# store_backtest_result tests
# ---------------------------------------------------------------------------

class TestStoreBacktestResult:
    def test_success(self):
        session = MagicMock()
        result = _make_backtest_result()
        metrics = _make_metrics()

        store_result = store_backtest_result(session, result, metrics)

        assert store_result.status == "success"
        assert store_result.strategy_id == "momentum_v1"
        assert store_result.asset_id == "005930"
        assert store_result.run_id is not None
        assert store_result.row_count_equity == 5
        assert store_result.row_count_trades == 2
        assert store_result.elapsed_ms > 0
        assert store_result.errors == []

        # Verify session methods called
        session.add.assert_called_once()
        session.flush.assert_called_once()
        assert session.bulk_insert_mappings.call_count == 2
        session.commit.assert_called_once()
        session.rollback.assert_not_called()

    def test_empty_trades(self):
        session = MagicMock()
        result = _make_backtest_result()
        result.trades = []
        metrics = _make_metrics()

        store_result = store_backtest_result(session, result, metrics)

        assert store_result.status == "success"
        assert store_result.row_count_trades == 0
        # Only equity curve bulk insert (not trades)
        session.bulk_insert_mappings.assert_called_once()

    def test_db_error_rollback(self):
        session = MagicMock()
        session.flush.side_effect = Exception("connection lost")
        result = _make_backtest_result()
        metrics = _make_metrics()

        store_result = store_backtest_result(session, result, metrics)

        assert store_result.status == "store_failed"
        assert store_result.run_id is None
        assert "connection lost" in store_result.errors[0]
        session.rollback.assert_called_once()
        session.commit.assert_not_called()

    def test_commit_error_rollback(self):
        session = MagicMock()
        session.commit.side_effect = Exception("integrity violation")
        result = _make_backtest_result()
        metrics = _make_metrics()

        store_result = store_backtest_result(session, result, metrics)

        assert store_result.status == "store_failed"
        assert "integrity violation" in store_result.errors[0]
        session.rollback.assert_called_once()

    def test_run_record_fields(self):
        session = MagicMock()
        result = _make_backtest_result()
        metrics = _make_metrics()

        store_backtest_result(session, result, metrics)

        # Check the BacktestRun object passed to session.add
        run_obj = session.add.call_args[0][0]
        assert run_obj.strategy_id == "momentum_v1"
        assert run_obj.asset_id == "005930"
        assert run_obj.status == "success"  # updated after commit
        assert run_obj.config_json["initial_cash"] == 10_000_000
        assert run_obj.metrics_json["total_return"] is not None

    def test_multi_asset_result(self):
        session = MagicMock()
        result = _make_backtest_result()
        result.asset_id = "MULTI"
        metrics = _make_metrics()

        store_result = store_backtest_result(session, result, metrics)

        assert store_result.status == "success"
        assert store_result.asset_id == "MULTI"


# ---------------------------------------------------------------------------
# BacktestStoreResult dataclass tests
# ---------------------------------------------------------------------------

class TestBacktestStoreResult:
    def test_defaults(self):
        r = BacktestStoreResult(strategy_id="test", asset_id="005930", status="success")
        assert r.run_id is None
        assert r.row_count_equity == 0
        assert r.row_count_trades == 0
        assert r.errors == []
        assert r.elapsed_ms == 0.0

    def test_error_result(self):
        r = BacktestStoreResult(
            strategy_id="test",
            asset_id="005930",
            status="store_failed",
            errors=["db_error: timeout"],
        )
        assert r.status == "store_failed"
        assert len(r.errors) == 1

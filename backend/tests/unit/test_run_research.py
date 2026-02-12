"""Unit tests for scripts/run_research.py CLI argument parsing and helpers."""

import pytest

from scripts.run_research import _resolve_strategy_names, parse_args


class TestParseArgs:
    def test_required_args(self):
        args = parse_args(["--start", "2025-01-01", "--end", "2025-12-31"])
        assert args.start == "2025-01-01"
        assert args.end == "2025-12-31"
        assert args.assets is None
        assert args.strategy is None
        assert args.initial_cash == 10_000_000
        assert args.skip_backtest is False
        assert args.log_level == "INFO"

    def test_all_args(self):
        args = parse_args([
            "--start", "2025-06-01",
            "--end", "2025-12-31",
            "--assets", "KS200,005930",
            "--strategy", "momentum,trend",
            "--initial-cash", "5000000",
            "--skip-backtest",
            "--log-level", "DEBUG",
        ])
        assert args.assets == "KS200,005930"
        assert args.strategy == "momentum,trend"
        assert args.initial_cash == 5_000_000
        assert args.skip_backtest is True
        assert args.log_level == "DEBUG"

    def test_missing_required_arg_start(self):
        with pytest.raises(SystemExit):
            parse_args(["--end", "2025-12-31"])

    def test_missing_required_arg_end(self):
        with pytest.raises(SystemExit):
            parse_args(["--start", "2025-01-01"])


class TestResolveStrategyNames:
    def test_none_returns_all(self):
        names = _resolve_strategy_names(None)
        assert "momentum" in names
        assert "trend" in names
        assert "mean_reversion" in names

    def test_single_strategy(self):
        names = _resolve_strategy_names("momentum")
        assert names == ["momentum"]

    def test_multiple_strategies(self):
        names = _resolve_strategy_names("momentum,trend")
        assert names == ["momentum", "trend"]

    def test_unknown_strategy_exits(self):
        with pytest.raises(SystemExit):
            _resolve_strategy_names("unknown_strat")

    def test_whitespace_handling(self):
        names = _resolve_strategy_names(" momentum , trend ")
        assert names == ["momentum", "trend"]

"""Tests for signal_store module."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

from research_engine.signal_store import (
    SignalStoreResult,
    _signal_result_to_records,
    store_signals_all,
    store_signals_for_asset,
)
from research_engine.strategies.base import SignalResult, _empty_signal_df

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_factors_df(n: int = 60) -> pd.DataFrame:
    """Generate a synthetic factors+price DataFrame."""
    dates = pd.bdate_range("2024-01-01", periods=n, freq="B")
    rng = np.random.default_rng(42)
    return pd.DataFrame({
        "close": 100 + np.cumsum(rng.normal(0, 1, n)),
        "open": 100 + np.cumsum(rng.normal(0, 1, n)),
        "high": 105 + np.cumsum(rng.normal(0, 1, n)),
        "low": 95 + np.cumsum(rng.normal(0, 1, n)),
        "volume": rng.integers(1000, 10000, n).astype(float),
        "ret_63d": rng.normal(0.03, 0.15, n),
        "vol_20": rng.uniform(0.10, 0.35, n),
        "sma_20": 100 + np.cumsum(rng.normal(0, 0.5, n)),
        "sma_60": 100 + np.cumsum(rng.normal(0, 0.3, n)),
    }, index=dates)


def _make_signal_result(n: int = 10) -> SignalResult:
    """Create a mock SignalResult for testing."""
    dates = pd.bdate_range("2024-01-01", periods=n, freq="B")
    signals = pd.DataFrame({
        "date": dates,
        "signal": [0, 0, 1, 1, 1, 0, 0, 1, 1, 0][:n],
        "score": [0.0, 0.0, 0.8, 0.9, 0.7, 0.0, 0.0, 0.6, 0.5, 0.0][:n],
        "action": ["hold", "hold", "entry", "hold", "hold",
                    "exit", "hold", "entry", "hold", "exit"][:n],
        "meta_json": [None] * n,
    })
    return SignalResult(
        asset_id="TEST",
        strategy_id="momentum",
        signals=signals,
        n_entry=2,
        n_exit=2,
        n_hold=6,
    )


# ---------------------------------------------------------------------------
# _signal_result_to_records
# ---------------------------------------------------------------------------

class TestSignalResultToRecords:
    def test_converts_to_list_of_dicts(self):
        sr = _make_signal_result(5)
        records = _signal_result_to_records("TEST", "momentum", sr)
        assert len(records) == 5
        assert all(isinstance(r, dict) for r in records)

    def test_record_has_required_keys(self):
        sr = _make_signal_result(3)
        records = _signal_result_to_records("TEST", "momentum", sr)
        required = {"asset_id", "date", "strategy_id", "signal", "score", "action", "meta_json"}
        for r in records:
            assert required <= set(r.keys())

    def test_asset_id_and_strategy_set(self):
        sr = _make_signal_result(3)
        records = _signal_result_to_records("KS200", "trend", sr)
        for r in records:
            assert r["asset_id"] == "KS200"
            assert r["strategy_id"] == "trend"

    def test_signal_values_preserved(self):
        sr = _make_signal_result(5)
        records = _signal_result_to_records("TEST", "momentum", sr)
        signals = [r["signal"] for r in records]
        assert signals == [0, 0, 1, 1, 1]

    def test_empty_signal_result(self):
        sr = SignalResult(
            asset_id="TEST",
            strategy_id="momentum",
            signals=_empty_signal_df(),
        )
        records = _signal_result_to_records("TEST", "momentum", sr)
        assert records == []


# ---------------------------------------------------------------------------
# store_signals_for_asset
# ---------------------------------------------------------------------------

class TestStoreSignalsForAsset:
    @patch("research_engine.signal_store._delete_and_insert_signals", return_value=10)
    @patch("research_engine.signal_store._signal_result_to_records")
    @patch("research_engine.signal_store.get_strategy")
    def test_success_flow(self, mock_get, mock_records, mock_insert):
        sr = _make_signal_result()
        mock_strat = MagicMock()
        mock_strat.strategy_id = "momentum"
        mock_strat.generate_signals.return_value = sr
        mock_get.return_value = mock_strat
        mock_records.return_value = [{"dummy": True}] * 10

        session = MagicMock()
        factors = _make_factors_df()

        result = store_signals_for_asset(session, "TEST", "momentum", factors)
        assert isinstance(result, SignalStoreResult)
        assert result.status == "success"
        assert result.row_count == 10
        session.commit.assert_called_once()

    @patch("research_engine.signal_store.get_strategy")
    def test_compute_failure(self, mock_get):
        mock_strat = MagicMock()
        mock_strat.strategy_id = "momentum"
        mock_strat.generate_signals.side_effect = ValueError("bad data")
        mock_get.return_value = mock_strat

        session = MagicMock()
        factors = _make_factors_df()

        result = store_signals_for_asset(session, "TEST", "momentum", factors)
        assert result.status == "compute_failed"
        assert len(result.errors) == 1

    @patch("research_engine.signal_store.get_strategy")
    def test_empty_signals_returns_success(self, mock_get):
        empty_sr = SignalResult(
            asset_id="TEST",
            strategy_id="momentum",
            signals=_empty_signal_df(),
        )
        mock_strat = MagicMock()
        mock_strat.strategy_id = "momentum"
        mock_strat.generate_signals.return_value = empty_sr
        mock_get.return_value = mock_strat

        session = MagicMock()
        factors = _make_factors_df()

        result = store_signals_for_asset(session, "TEST", "momentum", factors)
        assert result.status == "success"
        assert result.row_count == 0

    @patch("research_engine.signal_store._delete_and_insert_signals")
    @patch("research_engine.signal_store._signal_result_to_records", return_value=[{}])
    @patch("research_engine.signal_store.get_strategy")
    def test_db_failure_rollback(self, mock_get, mock_records, mock_insert):
        sr = _make_signal_result()
        mock_strat = MagicMock()
        mock_strat.strategy_id = "momentum"
        mock_strat.generate_signals.return_value = sr
        mock_get.return_value = mock_strat
        mock_insert.side_effect = RuntimeError("db error")

        session = MagicMock()
        factors = _make_factors_df()

        result = store_signals_for_asset(session, "TEST", "momentum", factors)
        assert result.status == "store_failed"
        session.rollback.assert_called_once()

    def test_strategy_kwargs_passed(self):
        """Integration test: real strategy with custom params."""
        factors = _make_factors_df()
        session = MagicMock()

        # Mock DB operations only
        with patch("research_engine.signal_store._delete_and_insert_signals", return_value=5):
            result = store_signals_for_asset(
                session, "TEST", "momentum", factors,
                ret_threshold=0.10, vol_cap=0.50,
            )
        assert result.status == "success"


# ---------------------------------------------------------------------------
# store_signals_all
# ---------------------------------------------------------------------------

class TestStoreSignalsAll:
    @patch("research_engine.signal_store.store_signals_for_asset")
    def test_processes_all_combinations(self, mock_store):
        mock_store.return_value = SignalStoreResult(
            asset_id="X", strategy_id="momentum", status="success", row_count=10
        )

        session = MagicMock()
        factors_by_asset = {
            "KS200": _make_factors_df(),
            "005930": _make_factors_df(),
        }

        results = store_signals_all(
            session, factors_by_asset, strategy_names=["momentum", "trend"]
        )
        # 2 assets × 2 strategies = 4 calls
        assert mock_store.call_count == 4
        assert len(results) == 4

    @patch("research_engine.signal_store.store_signals_for_asset")
    def test_default_strategies_uses_registry(self, mock_store):
        mock_store.return_value = SignalStoreResult(
            asset_id="X", strategy_id="momentum", status="success", row_count=5
        )

        session = MagicMock()
        factors_by_asset = {"KS200": _make_factors_df()}

        store_signals_all(session, factors_by_asset)
        # Should use all 3 strategies from registry
        assert mock_store.call_count == 3

    @patch("research_engine.signal_store.store_signals_for_asset")
    def test_mixed_success_failure(self, mock_store):
        mock_store.side_effect = [
            SignalStoreResult(
                asset_id="A", strategy_id="momentum",
                status="success", row_count=10,
            ),
            SignalStoreResult(
                asset_id="A", strategy_id="trend",
                status="compute_failed", errors=["err"],
            ),
        ]

        session = MagicMock()
        factors_by_asset = {"A": _make_factors_df()}

        results = store_signals_all(
            session, factors_by_asset, strategy_names=["momentum", "trend"]
        )
        assert len(results) == 2
        assert results[0].status == "success"
        assert results[1].status == "compute_failed"

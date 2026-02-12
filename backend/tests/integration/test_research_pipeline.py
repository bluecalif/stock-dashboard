"""Integration tests for the research pipeline (factors → signals → backtest → DB).

Requires INTEGRATION_TEST=1 and a real database connection.
"""

import os

import pandas as pd
import pytest

from research_engine.backtest import BacktestConfig, run_backtest
from research_engine.backtest_store import store_backtest_result
from research_engine.factor_store import store_factors_for_asset
from research_engine.factors import compute_all_factors
from research_engine.metrics import compute_metrics, metrics_to_dict
from research_engine.preprocessing import preprocess
from research_engine.signal_store import store_signals_for_asset
from research_engine.strategies import STRATEGY_REGISTRY

pytestmark = pytest.mark.skipif(
    not os.environ.get("INTEGRATION_TEST"),
    reason="Set INTEGRATION_TEST=1 to run integration tests",
)


class TestResearchPipelineE2E:
    """End-to-end research pipeline test using real DB data."""

    def _get_test_asset(self, db_session) -> str | None:
        """Find an asset with enough price data for testing."""
        from sqlalchemy import func

        from db.models import PriceDaily

        result = (
            db_session.query(PriceDaily.asset_id, func.count(PriceDaily.id))
            .group_by(PriceDaily.asset_id)
            .having(func.count(PriceDaily.id) >= 200)
            .first()
        )
        return result[0] if result else None

    def test_factor_store_for_asset(self, db_session):
        """Test factor computation and storage for a real asset."""
        asset_id = self._get_test_asset(db_session)
        if asset_id is None:
            pytest.skip("No asset with >= 200 rows of price data")

        result = store_factors_for_asset(db_session, asset_id)
        assert result.status == "success"
        assert result.row_count > 0
        assert result.factor_count == 15

    def test_full_pipeline_single_asset(self, db_session):
        """Full E2E: preprocess → factors → signals → backtest → metrics → store."""
        asset_id = self._get_test_asset(db_session)
        if asset_id is None:
            pytest.skip("No asset with >= 200 rows of price data")

        # 1. Preprocess
        df = preprocess(db_session, asset_id)
        assert len(df) >= 200
        assert "close" in df.columns

        # 2. Compute factors
        factors_df = compute_all_factors(df)
        assert len(factors_df.columns) == 15
        assert len(factors_df) == len(df)

        # 3. Generate signals for each strategy
        for strat_name in STRATEGY_REGISTRY:
            sig_result = store_signals_for_asset(
                db_session, asset_id, strat_name, factors_df
            )
            assert sig_result.status == "success"

            # 4. Backtest
            from db.models import SignalDaily

            sig_rows = (
                db_session.query(SignalDaily)
                .filter(
                    SignalDaily.asset_id == asset_id,
                    SignalDaily.strategy_id == sig_result.strategy_id,
                )
                .all()
            )
            signals_df = pd.DataFrame(
                [{"date": r.date, "signal": r.signal} for r in sig_rows]
            )
            if signals_df.empty:
                continue

            config = BacktestConfig(initial_cash=10_000_000)
            bt_result = run_backtest(
                prices=df,
                signals=signals_df,
                asset_id=asset_id,
                strategy_id=sig_result.strategy_id,
                config=config,
            )
            assert not bt_result.equity_curve.empty

            # 5. Metrics
            metrics = compute_metrics(bt_result)
            assert metrics.num_trades >= 0
            m_dict = metrics_to_dict(metrics)
            assert "cagr" in m_dict
            assert "sharpe" in m_dict

            # 6. Store backtest result
            store_result = store_backtest_result(db_session, bt_result, metrics)
            assert store_result.status == "success"
            assert store_result.run_id is not None

    def test_factor_store_all_assets(self, db_session):
        """Test factor computation for all assets with sufficient data."""
        from sqlalchemy import func

        from db.models import PriceDaily

        assets = (
            db_session.query(PriceDaily.asset_id, func.count(PriceDaily.id))
            .group_by(PriceDaily.asset_id)
            .having(func.count(PriceDaily.id) >= 200)
            .all()
        )
        if not assets:
            pytest.skip("No assets with >= 200 rows of price data")

        for asset_id, _ in assets:
            result = store_factors_for_asset(db_session, asset_id)
            assert result.status == "success", (
                f"Factor store failed for {asset_id}: {result.errors}"
            )

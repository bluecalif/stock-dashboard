"""Backtest execution service — orchestrates research_engine pipeline."""

from __future__ import annotations

import logging

from sqlalchemy.orm import Session

from api.schemas.backtest import BacktestRunRequest, BacktestRunResponse
from research_engine.backtest import BacktestConfig, run_backtest, run_backtest_multi
from research_engine.backtest_store import store_backtest_result
from research_engine.factors import compute_all_factors
from research_engine.metrics import compute_metrics
from research_engine.preprocessing import load_prices, preprocess
from research_engine.strategies import STRATEGY_REGISTRY, get_strategy

logger = logging.getLogger(__name__)

VALID_ASSET_IDS = {"KS200", "005930", "000660", "SOXL", "BTC", "GC=F", "SI=F"}


def run_backtest_on_demand(
    request: BacktestRunRequest,
    db: Session,
) -> BacktestRunResponse:
    """Execute a backtest and store results.

    Args:
        request: BacktestRunRequest with strategy/asset/config.
        db: SQLAlchemy session.

    Returns:
        BacktestRunResponse with run_id and metrics.

    Raises:
        ValueError: Invalid strategy_id, asset_id, or insufficient data.
        RuntimeError: DB storage failure.
    """
    # 1. Validate strategy_id
    if request.strategy_id not in STRATEGY_REGISTRY:
        available = list(STRATEGY_REGISTRY.keys())
        raise ValueError(
            f"Unknown strategy: {request.strategy_id}. Available: {available}"
        )

    # 2. Validate asset_id
    is_all = request.asset_id.upper() == "ALL"
    if not is_all and request.asset_id not in VALID_ASSET_IDS:
        raise ValueError(
            f"Unknown asset_id: {request.asset_id}. "
            f"Available: {sorted(VALID_ASSET_IDS)} or 'ALL'"
        )

    # 3. Build config
    config = BacktestConfig(
        initial_cash=request.initial_cash,
        commission_pct=request.commission_pct,
    )

    start = str(request.start_date) if request.start_date else None
    end = str(request.end_date) if request.end_date else None

    # 4. Run pipeline
    strategy = get_strategy(request.strategy_id)
    asset_ids = sorted(VALID_ASSET_IDS) if is_all else [request.asset_id]

    if is_all:
        result = _run_multi(db, strategy, asset_ids, config, start, end)
    else:
        result = _run_single(db, strategy, asset_ids[0], config, start, end)

    # 5. Compute metrics
    metrics = compute_metrics(result)

    # 6. Store to DB
    store_result = store_backtest_result(db, result, metrics)
    if store_result.status != "success":
        raise RuntimeError(
            f"Backtest store failed: {'; '.join(store_result.errors)}"
        )

    # 7. Fetch stored run and return response
    from api.repositories import backtest_repo

    run = backtest_repo.get_run_by_id(db, store_result.run_id)
    return BacktestRunResponse.model_validate(run)


def _run_single(db, strategy, asset_id, config, start, end):
    """Run single-asset backtest pipeline."""
    prices = load_prices(db, asset_id, start=start, end=end)
    processed = preprocess(prices, asset_id)
    factors = compute_all_factors(processed)
    signals = strategy.generate_signals(factors, asset_id)
    return run_backtest(
        prices=processed,
        signals=signals.signals,
        asset_id=asset_id,
        strategy_id=strategy.strategy_id,
        config=config,
    )


def _run_multi(db, strategy, asset_ids, config, start, end):
    """Run multi-asset backtest pipeline."""
    price_dict = {}
    signal_dict = {}
    for aid in asset_ids:
        try:
            prices = load_prices(db, aid, start=start, end=end)
            processed = preprocess(prices, aid)
            factors = compute_all_factors(processed)
            sig = strategy.generate_signals(factors, aid)
            price_dict[aid] = processed
            signal_dict[aid] = sig.signals
        except ValueError:
            logger.warning("Skipping asset %s: no data available", aid)
            continue

    if not price_dict:
        raise ValueError("No price data available for any asset")

    return run_backtest_multi(
        price_dict=price_dict,
        signal_dict=signal_dict,
        strategy_id=strategy.strategy_id,
        config=config,
    )

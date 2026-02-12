"""Backtest engine: run signal-based backtests producing equity curves and trade logs."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    initial_cash: float = 10_000_000  # 1천만원
    commission_pct: float = 0.001  # 0.1% 편도
    slippage_pct: float = 0.0  # 향후 확장
    allow_short: bool = False  # MVP: long-only


@dataclass
class TradeRecord:
    asset_id: str
    entry_date: date
    entry_price: float
    exit_date: date | None
    exit_price: float | None
    side: str  # "long"
    shares: float
    pnl: float | None
    cost: float  # 수수료 합계


@dataclass
class BacktestResult:
    strategy_id: str
    asset_id: str  # 다중 자산이면 "MULTI"
    config: BacktestConfig
    equity_curve: pd.DataFrame  # columns: date, equity, drawdown
    trades: list[TradeRecord] = field(default_factory=list)
    buy_hold_equity: pd.DataFrame = field(default_factory=pd.DataFrame)


def run_backtest(
    prices: pd.DataFrame,
    signals: pd.DataFrame,
    asset_id: str,
    strategy_id: str,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    """Run a single-asset backtest.

    Args:
        prices: Date-indexed DataFrame with OHLCV columns (open, high, low, close, volume).
        signals: DataFrame with columns 'date' and 'signal' (+1/0/-1).
        asset_id: Asset identifier.
        strategy_id: Strategy identifier.
        config: Backtest configuration. Uses defaults if None.

    Returns:
        BacktestResult with equity curve, trades, and buy-hold benchmark.
    """
    if config is None:
        config = BacktestConfig()

    # --- Prepare aligned data ---
    sig = signals[["date", "signal"]].copy()
    sig["date"] = pd.to_datetime(sig["date"])
    sig = sig.set_index("date").sort_index()

    pr = prices[["open", "close"]].copy()
    pr.index = pd.to_datetime(pr.index)
    pr = pr.sort_index()

    # Inner join on dates
    merged = pr.join(sig, how="inner")
    if merged.empty:
        return _empty_result(strategy_id, asset_id, config)

    dates = merged.index.tolist()
    opens = merged["open"].values
    closes = merged["close"].values
    sigs = merged["signal"].values.astype(int)

    # --- Simulation ---
    n = len(dates)
    cash = config.initial_cash
    shares = 0.0
    equity_arr = np.zeros(n)
    trades: list[TradeRecord] = []
    entry_date = None
    entry_price = 0.0
    trade_cost = 0.0

    for i in range(n):
        # Next-day execution: signal at t executes at t+1 open
        if i > 0:
            prev_sig = sigs[i - 1]
            curr_open = opens[i]

            # Buy signal & no position
            if prev_sig == 1 and shares == 0.0:
                comm = cash * config.commission_pct
                investable = cash - comm
                shares = investable / curr_open
                entry_date = dates[i]
                entry_price = curr_open
                trade_cost = comm
                cash = 0.0

            # Exit signal & has position
            elif prev_sig == 0 and shares > 0.0:
                proceeds = shares * curr_open
                comm = proceeds * config.commission_pct
                cash = proceeds - comm
                trade_cost += comm

                pnl = cash - config.initial_cash if len(trades) == 0 else (
                    shares * curr_open - shares * entry_price - trade_cost
                )
                # More accurate PnL: sell proceeds - buy cost - total commissions
                sell_proceeds = shares * curr_open
                buy_cost = shares * entry_price
                pnl = sell_proceeds - buy_cost - trade_cost

                trades.append(TradeRecord(
                    asset_id=asset_id,
                    entry_date=entry_date,
                    entry_price=entry_price,
                    exit_date=dates[i],
                    exit_price=curr_open,
                    side="long",
                    shares=shares,
                    pnl=pnl,
                    cost=trade_cost,
                ))
                shares = 0.0
                entry_date = None
                trade_cost = 0.0

        # Mark-to-market
        equity_arr[i] = cash + shares * closes[i]

    # Close open position at last close (record as open trade)
    if shares > 0.0:
        last_close = closes[-1]
        sell_proceeds = shares * last_close
        buy_cost = shares * entry_price
        pnl = sell_proceeds - buy_cost - trade_cost
        trades.append(TradeRecord(
            asset_id=asset_id,
            entry_date=entry_date,
            entry_price=entry_price,
            exit_date=None,
            exit_price=None,
            side="long",
            shares=shares,
            pnl=pnl,
            cost=trade_cost,
        ))

    # --- Equity curve ---
    running_max = np.maximum.accumulate(equity_arr)
    drawdown = equity_arr / running_max - 1.0

    equity_df = pd.DataFrame({
        "date": dates,
        "equity": equity_arr,
        "drawdown": drawdown,
    })

    # --- Buy & Hold benchmark ---
    bh_shares = (config.initial_cash - config.initial_cash * config.commission_pct) / opens[0]
    bh_equity = bh_shares * closes
    buy_hold_df = pd.DataFrame({
        "date": dates,
        "equity": bh_equity,
    })

    logger.info(
        "Backtest %s/%s: %d days, %d trades, final equity=%.0f",
        asset_id, strategy_id, n, len(trades), equity_arr[-1],
    )

    return BacktestResult(
        strategy_id=strategy_id,
        asset_id=asset_id,
        config=config,
        equity_curve=equity_df,
        trades=trades,
        buy_hold_equity=buy_hold_df,
    )


def run_backtest_multi(
    price_dict: dict[str, pd.DataFrame],
    signal_dict: dict[str, pd.DataFrame],
    strategy_id: str,
    config: BacktestConfig | None = None,
) -> BacktestResult:
    """Run multi-asset backtest with equal weighting (1/N).

    Each asset gets an equal share of the initial capital and runs independently.
    Equity curves are summed to produce the portfolio equity.

    Args:
        price_dict: {asset_id: prices_df} mapping.
        signal_dict: {asset_id: signals_df} mapping.
        strategy_id: Strategy identifier.
        config: Backtest configuration. Uses defaults if None.

    Returns:
        BacktestResult with combined equity curve and all trades.
    """
    if config is None:
        config = BacktestConfig()

    asset_ids = sorted(price_dict.keys())
    n_assets = len(asset_ids)

    if n_assets == 0:
        return _empty_result(strategy_id, "MULTI", config)

    # Equal weight per asset
    per_asset_config = BacktestConfig(
        initial_cash=config.initial_cash / n_assets,
        commission_pct=config.commission_pct,
        slippage_pct=config.slippage_pct,
        allow_short=config.allow_short,
    )

    results: list[BacktestResult] = []
    for aid in asset_ids:
        if aid not in signal_dict:
            continue
        r = run_backtest(
            prices=price_dict[aid],
            signals=signal_dict[aid],
            asset_id=aid,
            strategy_id=strategy_id,
            config=per_asset_config,
        )
        results.append(r)

    if not results:
        return _empty_result(strategy_id, "MULTI", config)

    # Merge equity curves on date
    all_trades: list[TradeRecord] = []
    equity_dfs: list[pd.DataFrame] = []

    for r in results:
        all_trades.extend(r.trades)
        eq = r.equity_curve[["date", "equity"]].copy()
        eq = eq.rename(columns={"equity": f"eq_{r.asset_id}"})
        equity_dfs.append(eq)

    merged = equity_dfs[0]
    for df in equity_dfs[1:]:
        merged = merged.merge(df, on="date", how="outer")

    merged = merged.sort_values("date").ffill().bfill()
    eq_cols = [c for c in merged.columns if c.startswith("eq_")]
    merged["equity"] = merged[eq_cols].sum(axis=1)

    running_max = merged["equity"].cummax()
    merged["drawdown"] = merged["equity"] / running_max - 1.0

    combined_equity = merged[["date", "equity", "drawdown"]].reset_index(drop=True)

    # Buy & hold: sum of individual buy-holds
    bh_dfs: list[pd.DataFrame] = []
    for r in results:
        bh = r.buy_hold_equity[["date", "equity"]].copy()
        bh = bh.rename(columns={"equity": f"bh_{r.asset_id}"})
        bh_dfs.append(bh)

    if bh_dfs:
        bh_merged = bh_dfs[0]
        for df in bh_dfs[1:]:
            bh_merged = bh_merged.merge(df, on="date", how="outer")
        bh_merged = bh_merged.sort_values("date").ffill().bfill()
        bh_cols = [c for c in bh_merged.columns if c.startswith("bh_")]
        bh_merged["equity"] = bh_merged[bh_cols].sum(axis=1)
        buy_hold_combined = bh_merged[["date", "equity"]].reset_index(drop=True)
    else:
        buy_hold_combined = pd.DataFrame(columns=["date", "equity"])

    logger.info(
        "Multi-asset backtest %s: %d assets, %d trades, final equity=%.0f",
        strategy_id, n_assets, len(all_trades),
        combined_equity["equity"].iloc[-1] if len(combined_equity) > 0 else 0,
    )

    return BacktestResult(
        strategy_id=strategy_id,
        asset_id="MULTI",
        config=config,
        equity_curve=combined_equity,
        trades=all_trades,
        buy_hold_equity=buy_hold_combined,
    )


def _empty_result(
    strategy_id: str, asset_id: str, config: BacktestConfig
) -> BacktestResult:
    return BacktestResult(
        strategy_id=strategy_id,
        asset_id=asset_id,
        config=config,
        equity_curve=pd.DataFrame(columns=["date", "equity", "drawdown"]),
        trades=[],
        buy_hold_equity=pd.DataFrame(columns=["date", "equity"]),
    )

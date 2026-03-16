"""Signal accuracy service — compute buy/sell success rates for strategy signals.

Core D.2 logic:
  signal=1 (buy) at T → T+forward_days close > T close → success
  signal=-1 (sell) at T → T+forward_days close < T close → success

DR.2 extension:
  compute_indicator_accuracy() — same logic but uses on-the-fly indicator
  signals (from indicator_signal_service) instead of signal_daily rows.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field

import pandas as pd
from sqlalchemy.orm import Session

from api.services.analysis.indicator_signal_service import (
    IndicatorSignal,
    generate_indicator_signals,
)
from db.models import PriceDaily, SignalDaily

# Minimum signal count to produce a meaningful success rate
MIN_SIGNAL_COUNT = 5


@dataclass
class SignalDetail:
    """Per-signal accuracy detail."""

    date: datetime.date
    signal: int           # 1 (buy) or -1 (sell)
    entry_price: float    # close on signal date
    exit_price: float     # close on T+forward_days
    forward_return: float  # (exit - entry) / entry
    success: bool


@dataclass
class SignalAccuracyResult:
    """Aggregated accuracy for one asset + strategy combination."""

    asset_id: str
    strategy_id: str
    forward_days: int
    total_signals: int
    evaluated_signals: int  # signals with valid forward price data

    buy_count: int = 0
    buy_success_count: int = 0
    buy_success_rate: float | None = None
    avg_return_after_buy: float | None = None

    sell_count: int = 0
    sell_success_count: int = 0
    sell_success_rate: float | None = None
    avg_return_after_sell: float | None = None

    details: list[SignalDetail] = field(default_factory=list)
    insufficient_data: bool = False


def compute_signal_accuracy(
    db: Session,
    asset_id: str,
    strategy_id: str,
    *,
    forward_days: int = 5,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    include_details: bool = False,
) -> SignalAccuracyResult:
    """Compute buy/sell success rates for a given asset + strategy.

    Args:
        db: SQLAlchemy session.
        asset_id: Target asset (e.g. "005930").
        strategy_id: Strategy ID (e.g. "momentum").
        forward_days: Number of days to look ahead for return calc.
        start_date: Optional filter — only signals on or after this date.
        end_date: Optional filter — only signals on or before this date.
        include_details: If True, populate per-signal details list.

    Returns:
        SignalAccuracyResult with rates, averages, and optional details.
    """
    # 1. Fetch all non-zero signals for this asset + strategy
    signal_query = db.query(SignalDaily).filter(
        SignalDaily.asset_id == asset_id,
        SignalDaily.strategy_id == strategy_id,
        SignalDaily.signal != 0,
    )
    if start_date:
        signal_query = signal_query.filter(SignalDaily.date >= start_date)
    if end_date:
        signal_query = signal_query.filter(SignalDaily.date <= end_date)
    signals = signal_query.order_by(SignalDaily.date.asc()).all()

    total_signals = len(signals)
    if total_signals == 0:
        return SignalAccuracyResult(
            asset_id=asset_id,
            strategy_id=strategy_id,
            forward_days=forward_days,
            total_signals=0,
            evaluated_signals=0,
            insufficient_data=True,
        )

    # 2. Fetch price data — build date→close lookup
    price_rows = (
        db.query(PriceDaily.date, PriceDaily.close)
        .filter(PriceDaily.asset_id == asset_id)
        .order_by(PriceDaily.date.asc())
        .all()
    )
    if not price_rows:
        return SignalAccuracyResult(
            asset_id=asset_id,
            strategy_id=strategy_id,
            forward_days=forward_days,
            total_signals=total_signals,
            evaluated_signals=0,
            insufficient_data=True,
        )

    # Build ordered date list for forward lookup
    price_df = pd.DataFrame(price_rows, columns=["date", "close"])
    price_df = price_df.sort_values("date").reset_index(drop=True)
    date_to_idx: dict[datetime.date, int] = {
        d: i for i, d in enumerate(price_df["date"])
    }

    # 3. Evaluate each signal
    buy_returns: list[float] = []
    sell_returns: list[float] = []
    details: list[SignalDetail] = []

    for sig in signals:
        idx = date_to_idx.get(sig.date)
        if idx is None:
            continue
        fwd_idx = idx + forward_days
        if fwd_idx >= len(price_df):
            continue  # not enough future data

        entry_price = price_df.iloc[idx]["close"]
        exit_price = price_df.iloc[fwd_idx]["close"]

        if entry_price == 0:
            continue

        forward_return = (exit_price - entry_price) / entry_price

        if sig.signal == 1:
            success = forward_return > 0
            buy_returns.append(forward_return)
        else:  # signal == -1
            success = forward_return < 0
            sell_returns.append(forward_return)

        if include_details:
            details.append(
                SignalDetail(
                    date=sig.date,
                    signal=sig.signal,
                    entry_price=float(entry_price),
                    exit_price=float(exit_price),
                    forward_return=round(forward_return, 6),
                    success=success,
                )
            )

    # 4. Compute aggregated metrics
    evaluated = len(buy_returns) + len(sell_returns)

    result = SignalAccuracyResult(
        asset_id=asset_id,
        strategy_id=strategy_id,
        forward_days=forward_days,
        total_signals=total_signals,
        evaluated_signals=evaluated,
        buy_count=len(buy_returns),
        sell_count=len(sell_returns),
    )

    if include_details:
        result.details = details

    if len(buy_returns) >= MIN_SIGNAL_COUNT:
        buy_successes = sum(1 for r in buy_returns if r > 0)
        result.buy_success_count = buy_successes
        result.buy_success_rate = round(buy_successes / len(buy_returns), 4)
        result.avg_return_after_buy = round(
            sum(buy_returns) / len(buy_returns), 6
        )
    else:
        result.insufficient_data = len(buy_returns) < MIN_SIGNAL_COUNT

    if len(sell_returns) >= MIN_SIGNAL_COUNT:
        sell_successes = sum(1 for r in sell_returns if r < 0)
        result.sell_success_count = sell_successes
        result.sell_success_rate = round(sell_successes / len(sell_returns), 4)
        result.avg_return_after_sell = round(
            sum(sell_returns) / len(sell_returns), 6
        )
    else:
        if result.insufficient_data is not True:
            result.insufficient_data = len(sell_returns) < MIN_SIGNAL_COUNT

    # Both sides have enough data → not insufficient
    if (len(buy_returns) >= MIN_SIGNAL_COUNT
            or len(sell_returns) >= MIN_SIGNAL_COUNT):
        result.insufficient_data = False

    return result


def compute_accuracy_all_strategies(
    db: Session,
    asset_id: str,
    strategy_ids: list[str],
    *,
    forward_days: int = 5,
) -> list[SignalAccuracyResult]:
    """Compute accuracy for multiple strategies at once.

    Convenience wrapper for D.3 (indicator comparison).
    """
    return [
        compute_signal_accuracy(
            db,
            asset_id,
            sid,
            forward_days=forward_days,
        )
        for sid in strategy_ids
    ]


# ---------------------------------------------------------------------------
# DR.2: Indicator-based accuracy (on-the-fly signals from factor_daily)
# ---------------------------------------------------------------------------

def _evaluate_signals_against_prices(
    indicator_signals: list[IndicatorSignal],
    price_df: pd.DataFrame,
    date_to_idx: dict[datetime.date, int],
    forward_days: int,
    include_details: bool,
) -> tuple[list[float], list[float], list[SignalDetail]]:
    """Evaluate indicator signals against price data.

    Returns (buy_returns, sell_returns, details).
    """
    buy_returns: list[float] = []
    sell_returns: list[float] = []
    details: list[SignalDetail] = []

    for sig in indicator_signals:
        if sig.signal not in (1, -1):
            continue  # skip warnings (0) and exit signals (2, -2)

        idx = date_to_idx.get(sig.date)
        if idx is None:
            continue
        fwd_idx = idx + forward_days
        if fwd_idx >= len(price_df):
            continue

        entry_price = price_df.iloc[idx]["close"]
        exit_price = price_df.iloc[fwd_idx]["close"]

        if entry_price == 0:
            continue

        forward_return = (exit_price - entry_price) / entry_price

        if sig.signal == 1:
            success = forward_return > 0
            buy_returns.append(forward_return)
        else:  # signal == -1
            success = forward_return < 0
            sell_returns.append(forward_return)

        if include_details:
            details.append(
                SignalDetail(
                    date=sig.date,
                    signal=sig.signal,
                    entry_price=float(entry_price),
                    exit_price=float(exit_price),
                    forward_return=round(forward_return, 6),
                    success=success,
                )
            )

    return buy_returns, sell_returns, details


def _build_accuracy_result(
    asset_id: str,
    strategy_id: str,
    forward_days: int,
    total_signals: int,
    buy_returns: list[float],
    sell_returns: list[float],
    details: list[SignalDetail],
    include_details: bool,
) -> SignalAccuracyResult:
    """Build SignalAccuracyResult from evaluated returns."""
    evaluated = len(buy_returns) + len(sell_returns)

    result = SignalAccuracyResult(
        asset_id=asset_id,
        strategy_id=strategy_id,
        forward_days=forward_days,
        total_signals=total_signals,
        evaluated_signals=evaluated,
        buy_count=len(buy_returns),
        sell_count=len(sell_returns),
    )

    if include_details:
        result.details = details

    if len(buy_returns) >= MIN_SIGNAL_COUNT:
        buy_successes = sum(1 for r in buy_returns if r > 0)
        result.buy_success_count = buy_successes
        result.buy_success_rate = round(buy_successes / len(buy_returns), 4)
        result.avg_return_after_buy = round(
            sum(buy_returns) / len(buy_returns), 6
        )
    else:
        result.insufficient_data = len(buy_returns) < MIN_SIGNAL_COUNT

    if len(sell_returns) >= MIN_SIGNAL_COUNT:
        sell_successes = sum(1 for r in sell_returns if r < 0)
        result.sell_success_count = sell_successes
        result.sell_success_rate = round(sell_successes / len(sell_returns), 4)
        result.avg_return_after_sell = round(
            sum(sell_returns) / len(sell_returns), 6
        )
    else:
        if result.insufficient_data is not True:
            result.insufficient_data = len(sell_returns) < MIN_SIGNAL_COUNT

    if (len(buy_returns) >= MIN_SIGNAL_COUNT
            or len(sell_returns) >= MIN_SIGNAL_COUNT):
        result.insufficient_data = False

    return result


def compute_indicator_accuracy(
    db: Session,
    asset_id: str,
    indicator_id: str,
    *,
    forward_days: int = 5,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    include_details: bool = False,
    min_gap_days: int = 3,
) -> SignalAccuracyResult:
    """Compute buy/sell success rates using on-the-fly indicator signals.

    Uses generate_indicator_signals() from DR.1 instead of signal_daily table.
    Only works for indicators with buy/sell signals (rsi_14, macd).
    ATR/vol signals (signal=0) and exit signals (|signal|>1) are excluded.

    Args:
        db: SQLAlchemy session.
        asset_id: Target asset (e.g. "005930").
        indicator_id: "rsi_14" or "macd" (atr_vol has no buy/sell signals).
        forward_days: Days to look ahead for return calculation.
        start_date: Optional filter start.
        end_date: Optional filter end.
        include_details: If True, populate per-signal details list.
        min_gap_days: Minimum gap between signals (DI.2). 0 disables.

    Returns:
        SignalAccuracyResult with strategy_id set to indicator_id.
    """
    # 1. Generate on-the-fly signals (with frequency filter)
    indicator_signals = generate_indicator_signals(
        db, asset_id, indicator_id,
        start_date=start_date, end_date=end_date,
        min_gap_days=min_gap_days,
    )

    # Filter to buy/sell only (exclude warnings and exit signals)
    trade_signals = [s for s in indicator_signals if s.signal in (1, -1)]
    total_signals = len(trade_signals)

    if total_signals == 0:
        return SignalAccuracyResult(
            asset_id=asset_id,
            strategy_id=indicator_id,  # reuse field for indicator_id
            forward_days=forward_days,
            total_signals=0,
            evaluated_signals=0,
            insufficient_data=True,
        )

    # 2. Fetch price data for forward return computation
    price_rows = (
        db.query(PriceDaily.date, PriceDaily.close)
        .filter(PriceDaily.asset_id == asset_id)
        .order_by(PriceDaily.date.asc())
        .all()
    )
    if not price_rows:
        return SignalAccuracyResult(
            asset_id=asset_id,
            strategy_id=indicator_id,
            forward_days=forward_days,
            total_signals=total_signals,
            evaluated_signals=0,
            insufficient_data=True,
        )

    price_df = pd.DataFrame(price_rows, columns=["date", "close"])
    price_df = price_df.sort_values("date").reset_index(drop=True)
    date_to_idx: dict[datetime.date, int] = {
        d: i for i, d in enumerate(price_df["date"])
    }

    # 3. Evaluate signals
    buy_returns, sell_returns, details = _evaluate_signals_against_prices(
        trade_signals, price_df, date_to_idx, forward_days, include_details,
    )

    # 4. Build result
    return _build_accuracy_result(
        asset_id=asset_id,
        strategy_id=indicator_id,
        forward_days=forward_days,
        total_signals=total_signals,
        buy_returns=buy_returns,
        sell_returns=sell_returns,
        details=details,
        include_details=include_details,
    )

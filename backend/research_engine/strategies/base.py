"""Base strategy class with common execution rules."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

logger = logging.getLogger(__name__)

# Default commission/slippage: 0.1% one-way (10 bps)
DEFAULT_COMMISSION_PCT = 0.001


@dataclass
class SignalResult:
    """Result of signal generation for one asset."""

    asset_id: str
    strategy_id: str
    signals: pd.DataFrame  # columns: date, signal, score, action, meta_json
    n_entry: int = 0
    n_exit: int = 0
    n_hold: int = 0


class Strategy(ABC):
    """Abstract base class for trading strategies.

    All strategies must implement `_raw_signals()` which computes
    raw signal values from factor data. The base class handles:
    - Signal shifting (next-day execution to avoid look-ahead bias)
    - Commission/slippage configuration
    - Action labeling (entry, exit, hold)
    - Output formatting for signal_daily table
    """

    strategy_id: str  # Must be set by subclass

    def __init__(
        self,
        commission_pct: float = DEFAULT_COMMISSION_PCT,
    ):
        self.commission_pct = commission_pct

    @abstractmethod
    def _raw_signals(self, factors_df: pd.DataFrame) -> pd.DataFrame:
        """Compute raw signals from factor data.

        Args:
            factors_df: DataFrame indexed by date with factor columns.

        Returns:
            DataFrame indexed by date with columns:
                - signal: int (+1=long, 0=neutral, -1=short)
                - score: float (optional confidence/strength, can be NaN)
                - meta: dict or None (strategy-specific metadata)
        """
        ...

    def generate_signals(
        self, factors_df: pd.DataFrame, asset_id: str
    ) -> SignalResult:
        """Generate signals with next-day execution rule.

        Signals at index t are meant to be executed at t+1 open.
        The output DataFrame labels each row with an action:
        - 'entry': position change from 0 to non-zero
        - 'exit': position change from non-zero to 0
        - 'hold': no position change

        Args:
            factors_df: DataFrame indexed by date with factor columns.
            asset_id: Asset identifier.

        Returns:
            SignalResult with formatted signal DataFrame.
        """
        raw = self._raw_signals(factors_df)

        if raw.empty:
            return SignalResult(
                asset_id=asset_id,
                strategy_id=self.strategy_id,
                signals=_empty_signal_df(),
            )

        # Ensure required columns
        if "signal" not in raw.columns:
            raise ValueError("_raw_signals must return 'signal' column")

        signals = raw[["signal"]].copy()
        signals["score"] = raw["score"] if "score" in raw.columns else None
        meta_col = raw["meta"] if "meta" in raw.columns else None

        # Label actions based on position changes
        prev_signal = signals["signal"].shift(1).fillna(0).astype(int)
        curr_signal = signals["signal"]

        actions = pd.Series("hold", index=signals.index)
        # Entry: from 0 to non-zero
        actions[(prev_signal == 0) & (curr_signal != 0)] = "entry"
        # Exit: from non-zero to 0
        actions[(prev_signal != 0) & (curr_signal == 0)] = "exit"
        # Reversal: from +1 to -1 or vice versa → treat as entry
        actions[
            (prev_signal != 0) & (curr_signal != 0) & (prev_signal != curr_signal)
        ] = "entry"

        signals["action"] = actions
        signals["meta_json"] = (
            meta_col.tolist() if meta_col is not None else [None] * len(signals)
        )

        # Reset index to get date as column
        signals = signals.reset_index()
        if signals.columns[0] != "date":
            signals = signals.rename(columns={signals.columns[0]: "date"})

        n_entry = (signals["action"] == "entry").sum()
        n_exit = (signals["action"] == "exit").sum()
        n_hold = (signals["action"] == "hold").sum()

        logger.info(
            "%s/%s: %d signals (entry=%d, exit=%d, hold=%d)",
            asset_id,
            self.strategy_id,
            len(signals),
            n_entry,
            n_exit,
            n_hold,
        )

        return SignalResult(
            asset_id=asset_id,
            strategy_id=self.strategy_id,
            signals=signals,
            n_entry=int(n_entry),
            n_exit=int(n_exit),
            n_hold=int(n_hold),
        )


def _empty_signal_df() -> pd.DataFrame:
    """Return empty DataFrame with signal columns."""
    return pd.DataFrame(columns=["date", "signal", "score", "action", "meta_json"])

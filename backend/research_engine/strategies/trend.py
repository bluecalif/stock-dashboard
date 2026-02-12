"""Trend strategy: golden/dead cross using SMA20 and SMA60."""

from __future__ import annotations

import logging

import pandas as pd

from research_engine.strategies.base import Strategy

logger = logging.getLogger(__name__)


class TrendStrategy(Strategy):
    """Trend-following strategy based on SMA crossovers.

    Entry: sma_20 crosses above sma_60 (golden cross) → long
    Exit: sma_20 crosses below sma_60 (dead cross) → neutral
    Signal: +1 (long) or 0 (neutral). No short signals.
    """

    strategy_id = "trend"

    def __init__(
        self,
        fast_col: str = "sma_20",
        slow_col: str = "sma_60",
        commission_pct: float = 0.001,
    ):
        super().__init__(commission_pct=commission_pct)
        self.fast_col = fast_col
        self.slow_col = slow_col

    def _raw_signals(self, factors_df: pd.DataFrame) -> pd.DataFrame:
        required = {self.fast_col, self.slow_col}
        missing = required - set(factors_df.columns)
        if missing:
            logger.warning("Missing factors for trend: %s", missing)
            return pd.DataFrame(columns=["signal", "score", "meta"])

        fast = factors_df[self.fast_col]
        slow = factors_df[self.slow_col]

        # Signal: 1 when fast > slow, 0 otherwise
        signal = (fast > slow).astype(int)

        # Score: distance between fast and slow (normalized by slow)
        spread = (fast - slow) / slow
        spread = spread.where(spread.notna(), other=0.0)

        result = pd.DataFrame(
            {
                "signal": signal,
                "score": spread.abs(),
                "meta": [
                    {self.fast_col: float(f), self.slow_col: float(s)}
                    if pd.notna(f) and pd.notna(s)
                    else None
                    for f, s in zip(fast, slow)
                ],
            },
            index=factors_df.index,
        )

        return result

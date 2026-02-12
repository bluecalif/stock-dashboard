"""Mean reversion strategy: enter on z-score band breakout and reversion."""

from __future__ import annotations

import logging

import pandas as pd

from research_engine.strategies.base import Strategy

logger = logging.getLogger(__name__)


class MeanReversionStrategy(Strategy):
    """Mean reversion strategy using price z-score.

    Computes z-score of close price relative to SMA20 / vol_20.
    Entry: z-score crosses back above lower band (oversold recovery) → long
    Exit: z-score reaches 0 (mean) OR falls below stop-loss level
    Signal: +1 (long) or 0 (neutral). No short signals.
    """

    strategy_id = "mean_reversion"

    def __init__(
        self,
        lookback: int = 20,
        entry_z: float = -2.0,
        exit_z: float = 0.0,
        stop_z: float = -3.0,
        commission_pct: float = 0.001,
    ):
        super().__init__(commission_pct=commission_pct)
        self.lookback = lookback
        self.entry_z = entry_z
        self.exit_z = exit_z
        self.stop_z = stop_z

    def _raw_signals(self, factors_df: pd.DataFrame) -> pd.DataFrame:
        # Need close price and SMA for z-score calculation
        if "close" not in factors_df.columns:
            logger.warning("Missing 'close' column for mean_reversion")
            return pd.DataFrame(columns=["signal", "score", "meta"])

        close = factors_df["close"]
        sma = close.rolling(self.lookback).mean()
        std = close.rolling(self.lookback).std()

        # z-score: how far price is from its moving average
        zscore = (close - sma) / std
        zscore = zscore.fillna(0.0)

        # Build signal with state machine
        signal = pd.Series(0, index=factors_df.index, dtype=int)
        in_position = False
        triggered = False  # Was z-score below entry_z?

        for i in range(len(factors_df)):
            z = zscore.iloc[i]

            if not in_position:
                if z <= self.entry_z:
                    triggered = True
                elif triggered and z > self.entry_z:
                    # Crossed back above entry band → enter long
                    signal.iloc[i] = 1
                    in_position = True
                    triggered = False
            else:
                if z >= self.exit_z:
                    # Reached mean → exit
                    signal.iloc[i] = 0
                    in_position = False
                elif z <= self.stop_z:
                    # Stop loss → exit
                    signal.iloc[i] = 0
                    in_position = False
                else:
                    signal.iloc[i] = 1

        result = pd.DataFrame(
            {
                "signal": signal,
                "score": zscore.abs(),
                "meta": [
                    {"zscore": float(z), "sma": float(s)}
                    if pd.notna(z) and pd.notna(s)
                    else None
                    for z, s in zip(zscore, sma)
                ],
            },
            index=factors_df.index,
        )

        return result

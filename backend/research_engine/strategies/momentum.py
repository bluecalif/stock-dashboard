"""Momentum strategy: long when 63-day return is strong and volatility is contained."""

from __future__ import annotations

import logging

import pandas as pd

from research_engine.strategies.base import Strategy

logger = logging.getLogger(__name__)


class MomentumStrategy(Strategy):
    """Momentum strategy.

    Entry: ret_63d > threshold AND vol_20 < vol_cap
    Exit: ret_63d < exit_threshold OR vol_20 > vol_cap
    Signal: +1 (long) or 0 (neutral). No short signals.
    """

    strategy_id = "momentum"

    def __init__(
        self,
        ret_threshold: float = 0.05,
        exit_threshold: float = 0.0,
        vol_cap: float = 0.40,
        commission_pct: float = 0.001,
    ):
        super().__init__(commission_pct=commission_pct)
        self.ret_threshold = ret_threshold
        self.exit_threshold = exit_threshold
        self.vol_cap = vol_cap

    def _raw_signals(self, factors_df: pd.DataFrame) -> pd.DataFrame:
        required = {"ret_63d", "vol_20"}
        missing = required - set(factors_df.columns)
        if missing:
            logger.warning("Missing factors for momentum: %s", missing)
            return pd.DataFrame(columns=["signal", "score", "meta"])

        ret = factors_df["ret_63d"]
        vol = factors_df["vol_20"]

        # Entry condition: strong momentum + contained volatility
        entry_mask = (ret > self.ret_threshold) & (vol < self.vol_cap)
        # Exit condition: weak momentum OR high volatility
        exit_mask = (ret < self.exit_threshold) | (vol >= self.vol_cap)

        # Build signal: iterate to respect entry/exit logic
        signal = pd.Series(0, index=factors_df.index, dtype=int)
        in_position = False

        for i in range(len(factors_df)):
            if not in_position:
                if entry_mask.iloc[i]:
                    signal.iloc[i] = 1
                    in_position = True
            else:
                if exit_mask.iloc[i]:
                    signal.iloc[i] = 0
                    in_position = False
                else:
                    signal.iloc[i] = 1

        result = pd.DataFrame(
            {
                "signal": signal,
                "score": ret.abs(),  # momentum strength as score
                "meta": [
                    {"ret_63d": float(r), "vol_20": float(v)}
                    if pd.notna(r) and pd.notna(v)
                    else None
                    for r, v in zip(ret, vol)
                ],
            },
            index=factors_df.index,
        )

        return result

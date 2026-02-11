"""Factor generation: compute technical indicators from price data.

Factors (15 total):
  Returns:    ret_1d, ret_5d, ret_20d, ret_63d
  Trend:      sma_20, sma_60, sma_120, ema_12, ema_26, macd
  Momentum:   roc, rsi_14
  Volatility: vol_20, atr_14
  Volume:     vol_zscore_20
"""

import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

FACTOR_VERSION = "v1"


# ---------------------------------------------------------------------------
# Returns
# ---------------------------------------------------------------------------

def compute_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Compute return factors: ret_1d, ret_5d, ret_20d, ret_63d."""
    close = df["close"]
    result = pd.DataFrame(index=df.index)
    for period, name in [(1, "ret_1d"), (5, "ret_5d"), (20, "ret_20d"), (63, "ret_63d")]:
        result[name] = close.pct_change(period)
    return result


# ---------------------------------------------------------------------------
# Trend
# ---------------------------------------------------------------------------

def compute_sma(df: pd.DataFrame) -> pd.DataFrame:
    """Compute SMA factors: sma_20, sma_60, sma_120."""
    close = df["close"]
    result = pd.DataFrame(index=df.index)
    for window, name in [(20, "sma_20"), (60, "sma_60"), (120, "sma_120")]:
        result[name] = close.rolling(window).mean()
    return result


def compute_ema(df: pd.DataFrame) -> pd.DataFrame:
    """Compute EMA factors: ema_12, ema_26."""
    close = df["close"]
    result = pd.DataFrame(index=df.index)
    result["ema_12"] = close.ewm(span=12, adjust=False).mean()
    result["ema_26"] = close.ewm(span=26, adjust=False).mean()
    return result


def compute_macd(df: pd.DataFrame) -> pd.DataFrame:
    """Compute MACD: ema_12 - ema_26."""
    close = df["close"]
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    result = pd.DataFrame(index=df.index)
    result["macd"] = ema_12 - ema_26
    return result


# ---------------------------------------------------------------------------
# Momentum
# ---------------------------------------------------------------------------

def compute_roc(df: pd.DataFrame, period: int = 12) -> pd.DataFrame:
    """Compute Rate of Change (ROC)."""
    close = df["close"]
    result = pd.DataFrame(index=df.index)
    result["roc"] = (close / close.shift(period) - 1) * 100
    return result


def compute_rsi(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Compute RSI using Wilder's smoothing method."""
    close = df["close"]
    delta = close.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    # Wilder's smoothing: first value is SMA, then EWM
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    # Handle edge cases: all gains (loss=0) → RSI=100, all losses (gain=0) → RSI=0
    rsi = pd.Series(
        np.where(
            avg_gain.isna(),
            np.nan,
            np.where(
                avg_loss == 0,
                np.where(avg_gain == 0, 50.0, 100.0),
                100 - 100 / (1 + avg_gain / avg_loss),
            ),
        ),
        index=df.index,
    )

    result = pd.DataFrame(index=df.index)
    result["rsi_14"] = rsi
    return result


# ---------------------------------------------------------------------------
# Volatility
# ---------------------------------------------------------------------------

def compute_volatility(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Compute annualized volatility (vol_20)."""
    ret = df["close"].pct_change()
    result = pd.DataFrame(index=df.index)
    result["vol_20"] = ret.rolling(window).std() * np.sqrt(252)
    return result


def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Compute Average True Range (ATR)."""
    high = df["high"]
    low = df["low"]
    prev_close = df["close"].shift(1)

    tr = pd.concat(
        [high - low, (high - prev_close).abs(), (low - prev_close).abs()],
        axis=1,
    ).max(axis=1)

    result = pd.DataFrame(index=df.index)
    result["atr_14"] = tr.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    return result


# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------

def compute_volume_zscore(df: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """Compute volume z-score over rolling window."""
    vol = df["volume"].astype(float)
    mean = vol.rolling(window).mean()
    std = vol.rolling(window).std()
    result = pd.DataFrame(index=df.index)
    result["vol_zscore_20"] = (vol - mean) / std
    result["vol_zscore_20"] = result["vol_zscore_20"].replace([np.inf, -np.inf], np.nan)
    return result


# ---------------------------------------------------------------------------
# All factors
# ---------------------------------------------------------------------------

ALL_FACTOR_FUNCS = [
    compute_returns,
    compute_sma,
    compute_ema,
    compute_macd,
    compute_roc,
    compute_rsi,
    compute_volatility,
    compute_atr,
    compute_volume_zscore,
]

ALL_FACTOR_NAMES = [
    "ret_1d", "ret_5d", "ret_20d", "ret_63d",
    "sma_20", "sma_60", "sma_120",
    "ema_12", "ema_26", "macd",
    "roc", "rsi_14",
    "vol_20", "atr_14",
    "vol_zscore_20",
]


def compute_all_factors(df: pd.DataFrame) -> pd.DataFrame:
    """Compute all 15 factors from a preprocessed OHLCV DataFrame.

    Args:
        df: DataFrame indexed by date with columns: open, high, low, close, volume

    Returns:
        DataFrame indexed by date with all factor columns
    """
    parts = [func(df) for func in ALL_FACTOR_FUNCS]
    result = pd.concat(parts, axis=1)

    logger.info(
        "Computed %d factors, %d rows, NaN counts: %s",
        len(result.columns),
        len(result),
        result.isna().sum().to_dict(),
    )

    return result

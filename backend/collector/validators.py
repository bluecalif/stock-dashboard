"""OHLCV data validation — pure functions, no DB dependency."""

import logging
from dataclasses import dataclass, field

import pandas as pd

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = ["asset_id", "date", "open", "high", "low", "close", "volume"]


@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    flagged_dates: list[str] = field(default_factory=list)
    row_count: int = 0
    error_row_count: int = 0


def _check_date_gaps(df: pd.DataFrame, category: str = "stock") -> list[str]:
    """Detect missing trading dates in the DataFrame.

    Args:
        df: DataFrame with 'date' column (datetime).
        category: Asset category — 'crypto' uses calendar days, others use business days.

    Returns:
        List of warning strings for each missing date.
    """
    if len(df) < 2 or "date" not in df.columns:
        return []

    dates = pd.to_datetime(df["date"]).sort_values()
    freq = "D" if category == "crypto" else "B"
    expected = pd.date_range(start=dates.iloc[0], end=dates.iloc[-1], freq=freq)
    missing = expected.difference(dates)

    if len(missing) == 0:
        return []

    missing_strs = [d.strftime("%Y-%m-%d") for d in missing]
    preview = ", ".join(missing_strs[:5])
    suffix = "..." if len(missing_strs) > 5 else ""
    return [f"date_gap:{len(missing)}days missing ({preview}{suffix})"]


def _check_price_spike(df: pd.DataFrame, threshold: float = 0.3) -> tuple[list[str], list[str]]:
    """Detect daily price changes exceeding threshold.

    Args:
        df: DataFrame with 'close' and 'date' columns.
        threshold: Maximum allowed absolute pct change (0.3 = 30%).

    Returns:
        Tuple of (warning strings, flagged date strings).
    """
    if len(df) < 2 or "close" not in df.columns:
        return [], []

    sorted_df = df.sort_values("date")
    pct = sorted_df["close"].pct_change().abs()
    spike_mask = pct > threshold
    spike_count = spike_mask.sum()

    if spike_count == 0:
        return [], []

    spike_dates = sorted_df.loc[spike_mask, "date"]
    flagged = [pd.Timestamp(d).strftime("%Y-%m-%d") for d in spike_dates]
    warnings = [f"price_spike:{spike_count}rows exceeding {threshold:.0%} threshold"]
    return warnings, flagged


def validate_ohlcv(df: pd.DataFrame, category: str = "stock") -> ValidationResult:
    """Validate OHLCV DataFrame and return ValidationResult.

    Checks:
    - Non-empty DataFrame
    - Required columns present
    - No high < low inversions
    - No negative prices (open/high/low/close)
    - No negative volume
    - No duplicate (asset_id, date) keys
    - Warning for zero volume rows
    """
    errors: list[str] = []
    warnings: list[str] = []
    error_row_count = 0

    # Empty check
    if df is None or len(df) == 0:
        return ValidationResult(
            is_valid=False,
            errors=["empty_dataframe"],
            row_count=0,
            error_row_count=0,
        )

    row_count = len(df)

    # Missing columns
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return ValidationResult(
            is_valid=False,
            errors=[f"missing_columns:{','.join(missing)}"],
            row_count=row_count,
            error_row_count=row_count,
        )

    # High/low inversion
    inversion_mask = df["high"] < df["low"]
    inversion_count = inversion_mask.sum()
    if inversion_count > 0:
        errors.append(f"high_low_inversion:{inversion_count}rows")
        error_row_count += inversion_count

    # Negative prices
    price_cols = ["open", "high", "low", "close"]
    neg_mask = (df[price_cols] < 0).any(axis=1)
    neg_count = neg_mask.sum()
    if neg_count > 0:
        errors.append(f"negative_price:{neg_count}rows")
        error_row_count += neg_count

    # Negative volume
    neg_vol_mask = df["volume"] < 0
    neg_vol_count = neg_vol_mask.sum()
    if neg_vol_count > 0:
        errors.append(f"negative_volume:{neg_vol_count}rows")
        error_row_count += neg_vol_count

    # Duplicate keys
    if "asset_id" in df.columns and "date" in df.columns:
        dup_mask = df.duplicated(subset=["asset_id", "date"], keep=False)
        dup_count = dup_mask.sum()
        if dup_count > 0:
            errors.append(f"duplicate_key:{dup_count}rows")
            error_row_count += dup_count

    # Zero volume warning
    zero_vol_count = (df["volume"] == 0).sum()
    if zero_vol_count > 0:
        warnings.append(f"zero_volume:{zero_vol_count}rows")
        logger.warning("Zero volume detected: %d rows", zero_vol_count)

    # Date gap detection (warning only)
    flagged_dates: list[str] = []
    gap_warnings = _check_date_gaps(df, category)
    if gap_warnings:
        warnings.extend(gap_warnings)
        for w in gap_warnings:
            logger.warning("Date gap detected: %s", w)

    # Price spike detection (warning only)
    spike_warnings, spike_dates = _check_price_spike(df)
    if spike_warnings:
        warnings.extend(spike_warnings)
        flagged_dates.extend(spike_dates)
        for w in spike_warnings:
            logger.warning("Price spike detected: %s", w)

    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        flagged_dates=flagged_dates,
        row_count=row_count,
        error_row_count=int(error_row_count),
    )

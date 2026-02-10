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
    row_count: int = 0
    error_row_count: int = 0


def validate_ohlcv(df: pd.DataFrame) -> ValidationResult:
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

    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        row_count=row_count,
        error_row_count=int(error_row_count),
    )

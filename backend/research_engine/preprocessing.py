"""Preprocessing pipeline: load price data, align calendar, handle missing values, flag outliers."""

import logging

import pandas as pd
from sqlalchemy.orm import Session

from collector.fdr_client import SYMBOL_MAP
from db.models import PriceDaily

logger = logging.getLogger(__name__)

DAILY_CATEGORIES = {"crypto"}


def load_prices(
    session: Session,
    asset_id: str,
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    """Load price_daily from DB for a single asset.

    Returns DataFrame indexed by date with columns: open, high, low, close, volume.
    """
    query = session.query(PriceDaily).filter(PriceDaily.asset_id == asset_id)
    if start:
        query = query.filter(PriceDaily.date >= start)
    if end:
        query = query.filter(PriceDaily.date <= end)
    query = query.order_by(PriceDaily.date)

    rows = query.all()
    if not rows:
        raise ValueError(f"No price data for {asset_id}")

    records = [
        {
            "date": r.date,
            "open": r.open,
            "high": r.high,
            "low": r.low,
            "close": r.close,
            "volume": r.volume,
        }
        for r in rows
    ]

    df = pd.DataFrame(records)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    return df


def get_category(asset_id: str) -> str:
    """Get asset category from SYMBOL_MAP."""
    if asset_id in SYMBOL_MAP:
        return SYMBOL_MAP[asset_id]["category"]
    return "unknown"


def align_calendar(
    df: pd.DataFrame,
    category: str,
    fill_method: str = "ffill",
) -> pd.DataFrame:
    """Align DataFrame to expected trading calendar.

    - crypto: every calendar day
    - others: business days only

    Missing dates are forward-filled. Volume for filled dates is set to 0.
    Returns DataFrame with 'is_filled' boolean column.
    """
    if df.empty:
        df["is_filled"] = pd.Series(dtype=bool)
        return df

    start, end = df.index.min(), df.index.max()

    if category in DAILY_CATEGORIES:
        full_idx = pd.date_range(start, end, freq="D")
    else:
        full_idx = pd.bdate_range(start, end)

    aligned = df.reindex(full_idx)
    aligned.index.name = "date"

    is_filled = aligned["close"].isna()

    if fill_method == "ffill":
        for col in ["open", "high", "low", "close"]:
            if col in aligned.columns:
                aligned[col] = aligned[col].ffill()

    aligned.loc[is_filled, "volume"] = 0
    aligned["is_filled"] = is_filled

    return aligned


def check_missing(
    df: pd.DataFrame,
    threshold: float = 0.05,
) -> tuple[bool, float, int]:
    """Check if missing data ratio exceeds threshold.

    Returns (is_ok, missing_ratio, missing_count).
    """
    if df.empty:
        return False, 1.0, 0

    if "is_filled" in df.columns:
        missing_count = int(df["is_filled"].sum())
    else:
        missing_count = int(df["close"].isna().sum())

    total = len(df)
    ratio = missing_count / total
    is_ok = ratio <= threshold

    if not is_ok:
        logger.warning(
            "Missing ratio %.2f%% exceeds threshold %.2f%% (%d/%d)",
            ratio * 100,
            threshold * 100,
            missing_count,
            total,
        )

    return is_ok, ratio, missing_count


def flag_outliers(
    df: pd.DataFrame,
    z_threshold: float = 4.0,
) -> pd.DataFrame:
    """Flag rows with extreme daily returns based on z-score."""
    df = df.copy()

    ret = df["close"].pct_change()
    std = ret.std()

    if std == 0 or pd.isna(std):
        df["is_outlier"] = False
    else:
        mean = ret.mean()
        z_scores = ((ret - mean) / std).abs()
        df["is_outlier"] = z_scores > z_threshold

    if len(df) > 0:
        df.iloc[0, df.columns.get_loc("is_outlier")] = False

    return df


def preprocess(
    session: Session,
    asset_id: str,
    start: str | None = None,
    end: str | None = None,
    missing_threshold: float = 0.05,
    outlier_z: float = 4.0,
) -> pd.DataFrame:
    """Full pipeline: load → align → check missing → flag outliers.

    Raises ValueError if no data or missing ratio exceeds threshold.
    """
    df = load_prices(session, asset_id, start, end)
    category = get_category(asset_id)

    logger.info(
        "Preprocessing %s (%s): %d rows, %s ~ %s",
        asset_id,
        category,
        len(df),
        df.index.min().date(),
        df.index.max().date(),
    )

    df = align_calendar(df, category)

    is_ok, ratio, missing_count = check_missing(df, missing_threshold)
    if not is_ok:
        raise ValueError(
            f"Missing data for {asset_id}: {ratio:.1%} ({missing_count} rows) "
            f"exceeds threshold {missing_threshold:.1%}"
        )

    df = flag_outliers(df, outlier_z)

    logger.info(
        "Preprocessed %s: %d rows, %d filled, %d outliers",
        asset_id,
        len(df),
        int(df["is_filled"].sum()),
        int(df["is_outlier"].sum()),
    )

    return df


def preprocess_from_df(
    df: pd.DataFrame,
    category: str = "stock",
    missing_threshold: float = 0.05,
    outlier_z: float = 4.0,
) -> pd.DataFrame:
    """Preprocess from an existing DataFrame (no DB access).

    Expects DataFrame indexed by date with: open, high, low, close, volume.
    """
    df = align_calendar(df, category)

    is_ok, ratio, missing_count = check_missing(df, missing_threshold)
    if not is_ok:
        raise ValueError(
            f"Missing data: {ratio:.1%} ({missing_count} rows) "
            f"exceeds threshold {missing_threshold:.1%}"
        )

    df = flag_outliers(df, outlier_z)
    return df

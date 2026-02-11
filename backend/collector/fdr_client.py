"""FDR (FinanceDataReader) wrapper with retry, fallback, and DataFrame standardization."""

import logging
import random
import time
from datetime import datetime, timezone

import pandas as pd

from config.settings import settings

logger = logging.getLogger(__name__)

SYMBOL_MAP: dict[str, dict] = {
    "KS200": {"fdr_symbol": "KS200", "category": "index"},
    "005930": {"fdr_symbol": "005930", "category": "stock"},
    "000660": {"fdr_symbol": "000660", "category": "stock"},
    "SOXL": {"fdr_symbol": "SOXL", "category": "etf"},
    "BTC": {"fdr_symbol": "BTC/KRW", "category": "crypto", "fallback": "BTC/USD"},
    "GC=F": {"fdr_symbol": "GC=F", "category": "commodity"},
    "SI=F": {"fdr_symbol": "SI=F", "category": "commodity"},
}

# Legacy constants kept for backward compat in tests; runtime uses settings
MAX_RETRIES = settings.fdr_max_retries
BASE_DELAY = settings.fdr_base_delay


def _fetch_raw(fdr_symbol: str, start: str, end: str) -> pd.DataFrame:
    """Call FDR and return raw DataFrame."""
    import FinanceDataReader as fdr

    return fdr.DataReader(fdr_symbol, start, end)


def _standardize(df: pd.DataFrame, asset_id: str) -> pd.DataFrame:
    """Standardize FDR DataFrame to project schema."""
    df = df.copy()
    # Reset index first (preserves original index name like "Date")
    df = df.reset_index()
    # Then lowercase all column names
    df.columns = [c.lower() for c in df.columns]
    # Some FDR symbols return unnamed index → "index" column after reset
    if "date" not in df.columns and "index" in df.columns:
        df = df.rename(columns={"index": "date"})

    df["asset_id"] = asset_id
    df["source"] = "fdr"
    df["volume"] = df["volume"].fillna(0).astype(int)
    df["ingested_at"] = datetime.now(timezone.utc)

    cols = ["asset_id", "date", "open", "high", "low", "close", "volume", "source", "ingested_at"]
    return df[cols]


def fetch_ohlcv(asset_id: str, start: str, end: str) -> pd.DataFrame:
    """Fetch OHLCV data from FDR with retry and BTC fallback.

    Args:
        asset_id: Internal asset identifier (e.g. "KS200", "BTC")
        start: Start date string (e.g. "2023-01-01")
        end: End date string (e.g. "2026-02-10")

    Returns:
        Standardized DataFrame with columns:
        asset_id, date, open, high, low, close, volume, source, ingested_at

    Raises:
        ValueError: If asset_id not in SYMBOL_MAP or empty result
        RuntimeError: If all retries exhausted
    """
    if asset_id not in SYMBOL_MAP:
        raise ValueError(f"Unknown asset_id: {asset_id}")

    info = SYMBOL_MAP[asset_id]
    symbols_to_try = [info["fdr_symbol"]]
    if "fallback" in info:
        symbols_to_try.append(info["fallback"])

    max_retries = settings.fdr_max_retries
    base_delay = settings.fdr_base_delay
    last_error: Exception | None = None

    for symbol in symbols_to_try:
        for attempt in range(max_retries):
            try:
                df = _fetch_raw(symbol, start, end)
                if df is None or len(df) == 0:
                    raise ValueError(f"Empty result for {symbol} ({start}~{end})")
                logger.info(
                    "Fetched %d rows for %s (symbol=%s, attempt=%d)",
                    len(df), asset_id, symbol, attempt + 1,
                )
                return _standardize(df, asset_id)
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt) * (1 + random.random() * 0.3)
                    logger.warning(
                        "Retry %d/%d for %s (symbol=%s): %s. Waiting %.1fs",
                        attempt + 1, max_retries, asset_id, symbol, e, delay,
                    )
                    time.sleep(delay)

        if "fallback" in info and symbol == info["fdr_symbol"]:
            logger.warning(
                "Primary symbol %s failed, trying fallback %s",
                symbol, info["fallback"],
            )

    raise RuntimeError(
        f"All retries exhausted for {asset_id}: {last_error}"
    )

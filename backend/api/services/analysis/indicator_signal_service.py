"""Indicator signal service — generate buy/sell signals from factor_daily on-the-fly.

DR.1: Scan factor time-series for transition points (crossovers) rather than
simple threshold checks.  No DB storage — signals are computed on demand.

DI.2: T+3 frequency control — suppress signals that occur within
min_gap_days of the previous signal (any direction).

DI.3: RSI exit signals — signal=2 (buy exit) when RSI rises above 30,
signal=-2 (sell exit) when RSI drops below 70.

Supported indicators:
  - rsi_14:  RSI 30/70 crossover → buy/sell/exit
  - macd:   MACD histogram sign change → buy/sell (golden/dead cross)
  - atr_vol: ATR/Price > 3% or vol_20 > 0.3 → warning (not a trade signal)
"""

from __future__ import annotations

import datetime
import math
from dataclasses import dataclass

from sqlalchemy.orm import Session

from api.repositories import factor_repo, price_repo


@dataclass
class IndicatorSignal:
    """A single indicator-generated signal at a specific date."""

    date: datetime.date
    indicator_id: str   # "rsi_14", "macd", "atr_vol"
    signal: int         # 1 (buy), -1 (sell), 0 (warning), 2 (buy_exit), -2 (sell_exit)
    label: str          # e.g. "RSI 과매도 진입", "MACD 골든크로스"
    value: float        # indicator value at signal date
    entry_price: float  # close price at signal date


# ---------------------------------------------------------------------------
# Factor names used per indicator_id
# ---------------------------------------------------------------------------

_INDICATOR_FACTORS: dict[str, list[str]] = {
    "rsi_14": ["rsi_14"],
    "macd": ["macd", "macd_signal"],
    "atr_vol": ["atr_14", "vol_20"],
}

VALID_INDICATOR_IDS: list[str] = list(_INDICATOR_FACTORS.keys())


# ---------------------------------------------------------------------------
# Internal: build date-keyed lookups
# ---------------------------------------------------------------------------

def _build_factor_series(
    db: Session,
    asset_id: str,
    factor_names: list[str],
    start_date: datetime.date | None,
    end_date: datetime.date | None,
) -> dict[datetime.date, dict[str, float]]:
    """Fetch factor data and organise as {date: {factor_name: value}}."""
    result: dict[datetime.date, dict[str, float]] = {}
    for fname in factor_names:
        rows = factor_repo.get_factors(
            db,
            asset_id=asset_id,
            factor_name=fname,
            start_date=start_date,
            end_date=end_date,
            limit=5000,
        )
        for r in rows:
            if r.value is None or math.isnan(r.value):
                continue
            result.setdefault(r.date, {})[fname] = r.value
    return result


def _build_price_map(
    db: Session,
    asset_id: str,
    start_date: datetime.date | None,
    end_date: datetime.date | None,
) -> dict[datetime.date, float]:
    """Fetch prices and return {date: close}."""
    rows = price_repo.get_prices(
        db,
        asset_id,
        start_date=start_date,
        end_date=end_date,
        limit=5000,
    )
    return {r.date: float(r.close) for r in rows if r.close}


# ---------------------------------------------------------------------------
# Signal generators per indicator
# ---------------------------------------------------------------------------

def _generate_rsi_signals(
    dates: list[datetime.date],
    factors: dict[datetime.date, dict[str, float]],
    prices: dict[datetime.date, float],
) -> list[IndicatorSignal]:
    """RSI 30/70 crossover detection with entry and exit signals.

    Signal values:
      1  = buy  (RSI crosses below 30 — oversold entry)
     -1  = sell (RSI crosses above 70 — overbought entry)
      2  = buy exit  (RSI rises back above 30 — oversold exit)
     -2  = sell exit (RSI drops back below 70 — overbought exit)
    """
    signals: list[IndicatorSignal] = []
    prev_rsi: float | None = None

    for d in dates:
        fvals = factors.get(d)
        close = prices.get(d)
        if fvals is None or close is None or "rsi_14" not in fvals:
            prev_rsi = fvals["rsi_14"] if fvals and "rsi_14" in fvals else None
            continue

        rsi = fvals["rsi_14"]
        if prev_rsi is not None:
            # 과매도 진입: prev >= 30 → current < 30
            if prev_rsi >= 30 and rsi < 30:
                signals.append(IndicatorSignal(
                    date=d, indicator_id="rsi_14", signal=1,
                    label="RSI 과매도 진입", value=rsi, entry_price=close,
                ))
            # 과매수 진입: prev <= 70 → current > 70
            elif prev_rsi <= 70 and rsi > 70:
                signals.append(IndicatorSignal(
                    date=d, indicator_id="rsi_14", signal=-1,
                    label="RSI 과매수 진입", value=rsi, entry_price=close,
                ))
            # 과매도 해제: prev < 30 → current >= 30
            elif prev_rsi < 30 and rsi >= 30:
                signals.append(IndicatorSignal(
                    date=d, indicator_id="rsi_14", signal=2,
                    label="RSI 과매도 해제", value=rsi, entry_price=close,
                ))
            # 과매수 해제: prev > 70 → current <= 70
            elif prev_rsi > 70 and rsi <= 70:
                signals.append(IndicatorSignal(
                    date=d, indicator_id="rsi_14", signal=-2,
                    label="RSI 과매수 해제", value=rsi, entry_price=close,
                ))
        prev_rsi = rsi

    return signals


def _generate_macd_signals(
    dates: list[datetime.date],
    factors: dict[datetime.date, dict[str, float]],
    prices: dict[datetime.date, float],
) -> list[IndicatorSignal]:
    """MACD histogram sign change detection (golden/dead cross)."""
    signals: list[IndicatorSignal] = []
    prev_hist: float | None = None

    for d in dates:
        fvals = factors.get(d)
        close = prices.get(d)
        if fvals is None or close is None:
            continue
        macd_val = fvals.get("macd")
        macd_sig = fvals.get("macd_signal")
        if macd_val is None or macd_sig is None:
            continue

        hist = macd_val - macd_sig

        if prev_hist is not None:
            # 골든크로스: prev <= 0 → current > 0
            if prev_hist <= 0 and hist > 0:
                signals.append(IndicatorSignal(
                    date=d, indicator_id="macd", signal=1,
                    label="MACD 골든크로스", value=hist, entry_price=close,
                ))
            # 데드크로스: prev >= 0 → current < 0
            elif prev_hist >= 0 and hist < 0:
                signals.append(IndicatorSignal(
                    date=d, indicator_id="macd", signal=-1,
                    label="MACD 데드크로스", value=hist, entry_price=close,
                ))
        prev_hist = hist

    return signals


def _generate_atr_vol_signals(
    dates: list[datetime.date],
    factors: dict[datetime.date, dict[str, float]],
    prices: dict[datetime.date, float],
) -> list[IndicatorSignal]:
    """ATR/Price + vol_20 high-volatility zone entry/exit detection."""
    signals: list[IndicatorSignal] = []
    was_high_vol = False

    for d in dates:
        fvals = factors.get(d)
        close = prices.get(d)
        if fvals is None or close is None:
            continue

        atr = fvals.get("atr_14")
        vol = fvals.get("vol_20")
        if atr is None and vol is None:
            continue

        atr_pct = (atr / close) if (atr is not None and close > 0) else 0.0
        vol_val = vol if vol is not None else 0.0
        is_high_vol = atr_pct > 0.03 or vol_val > 0.3

        if is_high_vol and not was_high_vol:
            # 고변동성 구간 진입 — label에 트리거 지표 명시
            triggers = []
            if atr_pct > 0.03:
                triggers.append(f"ATR {atr_pct * 100:.1f}%")
            if vol_val > 0.3:
                triggers.append(f"변동성 {vol_val * 100:.1f}%")
            trigger_text = " + ".join(triggers) if triggers else "고변동성"
            display_val = atr_pct if atr is not None else vol_val
            signals.append(IndicatorSignal(
                date=d, indicator_id="atr_vol", signal=0,
                label=f"고변동성 경고 진입 ({trigger_text})",
                value=display_val, entry_price=close,
            ))
        elif not is_high_vol and was_high_vol:
            # 정상 구간 복귀
            display_val = atr_pct if atr is not None else vol_val
            signals.append(IndicatorSignal(
                date=d, indicator_id="atr_vol", signal=0,
                label="정상 변동성 구간 복귀", value=display_val,
                entry_price=close,
            ))

        was_high_vol = is_high_vol

    return signals


_GENERATORS = {
    "rsi_14": _generate_rsi_signals,
    "macd": _generate_macd_signals,
    "atr_vol": _generate_atr_vol_signals,
}


# ---------------------------------------------------------------------------
# DI.2: Frequency filter
# ---------------------------------------------------------------------------

def _apply_frequency_filter(
    signals: list[IndicatorSignal],
    min_gap_days: int = 3,
) -> list[IndicatorSignal]:
    """Suppress signals that occur within *min_gap_days* of the previous one.

    Direction-agnostic: the gap is measured from the last **any** signal,
    not just same-direction signals.
    """
    if min_gap_days <= 0:
        return signals

    filtered: list[IndicatorSignal] = []
    last_date: datetime.date | None = None

    for sig in signals:
        if last_date is not None and (sig.date - last_date).days < min_gap_days:
            continue
        filtered.append(sig)
        last_date = sig.date

    return filtered


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_indicator_signals(
    db: Session,
    asset_id: str,
    indicator_id: str,
    *,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    min_gap_days: int = 3,
) -> list[IndicatorSignal]:
    """Generate on-the-fly signals for a single indicator.

    Args:
        db: SQLAlchemy session.
        asset_id: Target asset (e.g. "005930").
        indicator_id: One of "rsi_14", "macd", "atr_vol".
        start_date: Optional filter start.
        end_date: Optional filter end.
        min_gap_days: Minimum gap between consecutive signals (any direction).
            0 disables filtering.  Default 3 (DI.2).

    Returns:
        List of IndicatorSignal sorted by date ascending.

    Raises:
        ValueError: If indicator_id is not supported.
    """
    if indicator_id not in _INDICATOR_FACTORS:
        raise ValueError(
            f"Unknown indicator_id '{indicator_id}'. "
            f"Supported: {VALID_INDICATOR_IDS}"
        )

    factor_names = _INDICATOR_FACTORS[indicator_id]
    factors = _build_factor_series(db, asset_id, factor_names, start_date, end_date)
    prices = _build_price_map(db, asset_id, start_date, end_date)

    # Sorted dates for sequential scan
    all_dates = sorted(set(factors.keys()) | set(prices.keys()))

    generator = _GENERATORS[indicator_id]
    raw_signals = generator(all_dates, factors, prices)

    return _apply_frequency_filter(raw_signals, min_gap_days)

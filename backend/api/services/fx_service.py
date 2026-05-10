"""FX service — fx_daily 조회 + forward-fill."""

from __future__ import annotations

from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from research_engine.simulation.fx import load_fx_series


def get_usd_krw(db: Session, start: date, end: date) -> list[dict]:
    """USD/KRW 환율 시계열 (calendar-day forward-fill).

    Returns:
        [{date: str, usd_krw_close: float}, ...]
    """
    s = load_fx_series(db, start, end)
    if s.empty:
        return []
    return [
        {"date": ts.date().isoformat(), "usd_krw_close": float(val)}
        for ts, val in s.items()
        if not pd.isna(val)
    ]

"""USD/KRW 환율 로더 (마스터플랜 §2.3, D-3).

fx_daily 테이블에서 일별 환율 로드 후 calendar day forward-fill.
KR 휴장일(공휴일, 주말) → 직전 거래일 환율 사용.
"""

from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from db.models import FxDaily


def load_fx_series(session: Session, start: date, end: date) -> pd.Series:
    """fx_daily 테이블에서 USD/KRW 환율 시계열 로드.

    Args:
        session: SQLAlchemy session
        start: 조회 시작일 (inclusive)
        end: 조회 종료일 (inclusive)

    Returns:
        DatetimeIndex pd.Series. 결측일(휴장일/주말)은 forward-fill.
        Name: "usd_krw"
    """
    rows = (
        session.query(FxDaily)
        .filter(FxDaily.date >= start, FxDaily.date <= end)
        .order_by(FxDaily.date)
        .all()
    )

    if not rows:
        return pd.Series(dtype=float, name="usd_krw")

    raw = pd.Series(
        {pd.Timestamp(row.date): float(row.usd_krw_close) for row in rows},
        name="usd_krw",
    )

    full_idx = pd.date_range(start=pd.Timestamp(start), end=pd.Timestamp(end), freq="D")
    result = raw.reindex(full_idx).ffill()
    result.name = "usd_krw"
    return result

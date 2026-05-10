"""fx.py unit tests — 마스터플랜 §2.3 / §9.1.

load_fx_series: DB → pd.Series forward-fill 검증.
Mock session으로 DB 없이 순수 로직 테스트.
"""

from datetime import date
from decimal import Decimal

import pandas as pd
import pytest

from research_engine.simulation.fx import load_fx_series

# ── Mock helpers ──────────────────────────────────────────────────────────────


class _FxRow:
    def __init__(self, d: date, rate: float):
        self.date = d
        self.usd_krw_close = Decimal(str(rate))


class _MockQuery:
    def __init__(self, rows):
        self._rows = rows

    def filter(self, *args):
        return self

    def order_by(self, *args):
        return self

    def all(self):
        return self._rows


class _MockSession:
    def __init__(self, rows):
        self._rows = rows

    def query(self, model):
        return _MockQuery(self._rows)


def _make_session(date_rate_pairs: list[tuple[date, float]]) -> _MockSession:
    rows = [_FxRow(d, r) for d, r in date_rate_pairs]
    return _MockSession(rows)


# ── Tests ─────────────────────────────────────────────────────────────────────


def test_basic_range():
    """거래일 2개 사이 calendar days 수 = end - start + 1."""
    session = _make_session([
        (date(2024, 1, 2), 1300.0),  # 화
        (date(2024, 1, 3), 1305.0),  # 수
    ])
    s = load_fx_series(session, date(2024, 1, 2), date(2024, 1, 3))
    assert len(s) == 2
    assert s.iloc[0] == pytest.approx(1300.0)
    assert s.iloc[1] == pytest.approx(1305.0)


def test_forward_fill_weekend():
    """금요일 데이터 → 토·일은 금요일 값으로 forward-fill."""
    session = _make_session([
        (date(2024, 1, 5), 1310.0),  # 금
        (date(2024, 1, 8), 1315.0),  # 월
    ])
    s = load_fx_series(session, date(2024, 1, 5), date(2024, 1, 8))
    assert len(s) == 4  # 금~월 4일
    assert s.loc[pd.Timestamp("2024-01-06")] == pytest.approx(1310.0)  # 토
    assert s.loc[pd.Timestamp("2024-01-07")] == pytest.approx(1310.0)  # 일
    assert s.loc[pd.Timestamp("2024-01-08")] == pytest.approx(1315.0)  # 월


def test_holiday_forward_fill():
    """KR 공휴일(2024-01-01) 값이 직전 거래일(2023-12-29) 값으로 forward-fill."""
    session = _make_session([
        (date(2023, 12, 29), 1290.0),  # 금 (마지막 거래일)
        (date(2024, 1, 2), 1295.0),    # 화 (첫 거래일)
    ])
    s = load_fx_series(session, date(2023, 12, 29), date(2024, 1, 2))
    # 12-29(금), 12-30(토), 12-31(일), 01-01(신정), 01-02(화) = 5일
    assert len(s) == 5
    # 신정(2024-01-01)은 거래일 아님 → 직전 12-29 값
    assert s.loc[pd.Timestamp("2024-01-01")] == pytest.approx(1290.0)
    assert s.loc[pd.Timestamp("2024-01-02")] == pytest.approx(1295.0)


def test_empty_range():
    """DB에 해당 범위 데이터 없으면 빈 Series 반환."""
    session = _make_session([])
    s = load_fx_series(session, date(2024, 1, 1), date(2024, 1, 31))
    assert len(s) == 0
    assert s.name == "usd_krw"


def test_series_name():
    """반환 Series name == 'usd_krw'."""
    session = _make_session([(date(2024, 1, 2), 1300.0)])
    s = load_fx_series(session, date(2024, 1, 2), date(2024, 1, 2))
    assert s.name == "usd_krw"


def test_single_row():
    """단일 행 조회 — 해당일 값 정확히 반환."""
    session = _make_session([(date(2024, 6, 3), 1380.5)])
    s = load_fx_series(session, date(2024, 6, 3), date(2024, 6, 3))
    assert len(s) == 1
    assert s.iloc[0] == pytest.approx(1380.5)


def test_multi_day_ffill_chain():
    """연속 5거래일 결측 → 직전 값으로 모두 forward-fill."""
    session = _make_session([
        (date(2024, 3, 1), 1320.0),
        (date(2024, 3, 11), 1330.0),  # 3-2~3-10 (9일) 결측
    ])
    s = load_fx_series(session, date(2024, 3, 1), date(2024, 3, 11))
    # 3-1 ~ 3-11 = 11일
    assert len(s) == 11
    # 3-2 ~ 3-10 모두 1320.0
    for d in pd.date_range("2024-03-02", "2024-03-10"):
        assert s.loc[d] == pytest.approx(1320.0)
    assert s.loc[pd.Timestamp("2024-03-11")] == pytest.approx(1330.0)

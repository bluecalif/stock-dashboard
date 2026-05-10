"""적립식 Tab A replay 엔진 (마스터플랜 §3.3, §3.8).

D-lock:
  D-3  fx_daily 환율 (매 거래일)
  D-4  배당 = annual_yield / 252 × 보유평가액 (매 거래일)
  D-16 이벤트 순서 = 정기 적립 먼저 → (strategy.step은 P2-4에서)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_type

import pandas as pd
from sqlalchemy.orm import Session

from db.models import AssetMaster, PriceDaily
from research_engine.simulation.fx import load_fx_series
from research_engine.simulation.mdd import mdd_by_calendar_year
from research_engine.simulation.padding import pad_returns, prices_with_padding
from research_engine.simulation.wbi import generate_wbi

# ── 공개 타입 ─────────────────────────────────────────────────────────────────


@dataclass
class EquityPoint:
    date: date_type
    krw_value: float
    local_value: float
    shares: float


@dataclass
class KpiResult:
    final_asset_krw: float
    total_return: float
    annualized_return: float
    yearly_worst_mdd: float
    total_deposit_krw: int


# ── KPI 산출 (마스터플랜 §3.8) ───────────────────────────────────────────────


def compute_kpi(
    curve: list[EquityPoint],
    total_deposit_krw: int,
    period_years: int,
) -> KpiResult:
    if not curve or total_deposit_krw <= 0:
        return KpiResult(0.0, 0.0, 0.0, 0.0, total_deposit_krw)

    final = curve[-1].krw_value
    total_return = (final - total_deposit_krw) / total_deposit_krw
    annualized = (final / total_deposit_krw) ** (1.0 / period_years) - 1

    krw_series = pd.Series(
        [pt.krw_value for pt in curve],
        index=pd.DatetimeIndex([pd.Timestamp(pt.date) for pt in curve]),
    )
    mdd_dict = mdd_by_calendar_year(krw_series)
    worst_mdd = min(mdd_dict.values()) if mdd_dict else 0.0

    return KpiResult(
        final_asset_krw=final,
        total_return=total_return,
        annualized_return=annualized,
        yearly_worst_mdd=worst_mdd,
        total_deposit_krw=total_deposit_krw,
    )


# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────


def _first_trading_days_of_month(index: pd.DatetimeIndex) -> set[pd.Timestamp]:
    """DatetimeIndex에서 각 월의 첫 거래일 집합을 반환."""
    first_days: set[pd.Timestamp] = set()
    prev_month: tuple[int, int] | None = None
    for ts in sorted(index):
        month = (ts.year, ts.month)
        if month != prev_month:
            first_days.add(ts)
            prev_month = month
    return first_days


def _load_price_series(
    session: Session,
    asset_id: str,
    start: date_type,
    end: date_type,
) -> pd.Series:
    rows = (
        session.query(PriceDaily)
        .filter(PriceDaily.asset_id == asset_id, PriceDaily.date >= start, PriceDaily.date <= end)
        .order_by(PriceDaily.date)
        .all()
    )
    if not rows:
        return pd.Series(dtype=float)
    return pd.Series(
        {pd.Timestamp(row.date): float(row.close) for row in rows},
        name="close",
    )


# ── 순수 로직 (테스트 가능) ───────────────────────────────────────────────────


def replay_core(
    prices: pd.Series,
    fx_series: pd.Series | None,
    currency: str,
    annual_yield: float,
    monthly_amount_krw: int,
    period_years: int,
) -> tuple[list[EquityPoint], KpiResult]:
    """적립식 replay 순수 로직 (DB 의존성 없음).

    Args:
        prices: DatetimeIndex pd.Series, 현지통화 종가 (이미 clean)
        fx_series: DatetimeIndex pd.Series, USD/KRW (KRW 자산이면 None)
        currency: "KRW" or "USD"
        annual_yield: 연 배당률 (0.035 = 3.5%)
        monthly_amount_krw: 월 적립금 (원화)
        period_years: 시뮬레이션 기간 (연) — KPI annualized 계산용

    Returns:
        (curve, kpi) tuple
    """
    daily_yield_mult = 1.0 + annual_yield / 252.0
    trading_index = prices.index
    first_days = _first_trading_days_of_month(trading_index)

    shares = 0.0
    total_deposit = 0
    curve: list[EquityPoint] = []

    for ts in trading_index:
        price = float(prices[ts])
        fx_rate: float | None = None
        if currency == "USD" and fx_series is not None and ts in fx_series.index:
            fx_rate = float(fx_series[ts])
        elif currency == "USD" and fx_series is not None:
            # forward-fill: nearest available
            fx_rate = float(fx_series.asof(ts))

        # D-16: 정기 적립 먼저
        if ts in first_days:
            if currency == "USD" and fx_rate:
                shares += (monthly_amount_krw / fx_rate) / price
            else:
                shares += monthly_amount_krw / price
            total_deposit += monthly_amount_krw

        # D-4: 배당 재투자 (매 거래일)
        shares *= daily_yield_mult

        # 평가액 계산
        local_value = shares * price
        krw_value = local_value * fx_rate if (currency == "USD" and fx_rate) else local_value

        curve.append(EquityPoint(
            date=ts.date(),
            krw_value=krw_value,
            local_value=local_value,
            shares=shares,
        ))

    kpi = compute_kpi(curve, total_deposit, period_years)
    return curve, kpi


# ── 공개 인터페이스 ───────────────────────────────────────────────────────────


def replay(
    asset_code: str,
    monthly_amount_krw: int,
    period_years: int,
    session: Session,
) -> tuple[list[EquityPoint], KpiResult]:
    """적립식 Tab A 엔진 공개 인터페이스.

    DB에서 가격/환율 로드 후 replay_core 호출.
    WBI → generate_wbi(), JEPI(allow_padding) → padding.py.

    Args:
        asset_code: "QQQ" / "KS200" / "WBI" / "JEPI" 등
        monthly_amount_krw: 월 적립금 (원화)
        period_years: 3 / 5 / 10
        session: SQLAlchemy session

    Returns:
        (curve, kpi) tuple
    """
    from datetime import date as _date

    from dateutil.relativedelta import relativedelta

    end_date = _date.today()
    start_date = end_date - relativedelta(years=period_years)

    # WBI: DB 조회 없이 GBM synthetic 생성
    if asset_code == "WBI":
        n_days = period_years * 252
        wbi_prices = generate_wbi(n_days, seed=42)
        trading_dates = pd.date_range(
            end=pd.Timestamp(end_date), periods=n_days, freq="B"
        )
        prices = pd.Series(wbi_prices, index=trading_dates, name="close")
        return replay_core(prices, None, "KRW", 0.0, monthly_amount_krw, period_years)

    # 일반 자산: asset_master 조회
    asset = session.query(AssetMaster).filter_by(asset_id=asset_code).first()
    if asset is None:
        raise ValueError(f"asset not found in asset_master: {asset_code}")

    currency: str = asset.currency
    annual_yield = float(asset.annual_yield)
    allow_padding: bool = bool(asset.allow_padding)

    raw_prices = _load_price_series(session, asset_code, start_date, end_date).dropna()
    if raw_prices.empty:
        raise ValueError(f"price_daily에 {asset_code} 데이터 없음 ({start_date} ~ {end_date})")

    # JEPI 등 history 부족 자산: cyclic returns padding
    if allow_padding:
        actual_returns = raw_prices.pct_change().dropna().values
        target_days = period_years * 252
        padded_returns = pad_returns(actual_returns, target_days)
        padding_len = target_days - len(actual_returns)
        first_price = float(raw_prices.iloc[0])
        prices_arr = prices_with_padding(first_price, padded_returns, padding_len)

        actual_dates = raw_prices.index
        if padding_len > 0:
            pad_dates = pd.date_range(
                end=actual_dates[0] - pd.Timedelta(days=1),
                periods=padding_len,
                freq="B",
            )
            full_index = pad_dates.append(actual_dates)
        else:
            full_index = actual_dates
        prices = pd.Series(prices_arr, index=full_index[: len(prices_arr)], name="close")
    else:
        prices = raw_prices

    # USD 자산 환율 로드
    fx_series: pd.Series | None = None
    if currency == "USD":
        fx_series = load_fx_series(
            session,
            prices.index[0].date(),
            prices.index[-1].date(),
        )

    return replay_core(prices, fx_series, currency, annual_yield, monthly_amount_krw, period_years)

"""Simulation service — DB 조회 + simulation 모듈 조율 (마스터플랜 §3)."""

from __future__ import annotations

import logging
from datetime import date as date_type

import pandas as pd
from sqlalchemy.orm import Session

from api.schemas.simulation import (
    EquityPointResponse,
    KpiResponse,
    SimulatePortfolioRequest,
    SimulatePortfolioResponse,
    SimulateReplayRequest,
    SimulateReplayResponse,
    SimulateStrategyRequest,
    SimulateStrategyResponse,
)
from db.models import PriceDaily
from research_engine.simulation.portfolio import PRESETS, Portfolio
from research_engine.simulation.replay import EquityPoint, KpiResult, compute_kpi, replay
from research_engine.simulation.strategy_a import StrategyA
from research_engine.simulation.strategy_b import StrategyB

logger = logging.getLogger(__name__)

# 알려진 자산 통화 (DB currency 컬럼으로 대체 가능하지만 빠른 조회용)
_USD_ASSETS = {"QQQ", "SPY", "SCHD", "JEPI", "TLT", "NVDA", "GOOGL", "TSLA", "SOXL"}
_KRW_ASSETS = {"KS200", "005930", "000660", "BTC", "WBI"}


def _to_equity_response(pt: EquityPoint) -> EquityPointResponse:
    return EquityPointResponse(
        date=pt.date.isoformat(),
        krw_value=pt.krw_value,
        local_value=pt.local_value,
        shares=pt.shares,
    )


def _to_kpi_response(kpi: KpiResult) -> KpiResponse:
    return KpiResponse(
        final_asset_krw=kpi.final_asset_krw,
        total_return=kpi.total_return,
        annualized_return=kpi.annualized_return,
        yearly_worst_mdd=kpi.yearly_worst_mdd,
        total_deposit_krw=kpi.total_deposit_krw,
    )


# ── Tab A ────────────────────────────────────────────────────────────────────


def simulate_replay(db: Session, req: SimulateReplayRequest) -> SimulateReplayResponse:
    """Tab A 적립식 replay."""
    curve, kpi = replay(req.asset_code, req.monthly_amount, req.period_years, db)
    return SimulateReplayResponse(
        asset_code=req.asset_code,
        curve=[_to_equity_response(pt) for pt in curve],
        kpi=_to_kpi_response(kpi),
    )


# ── Tab B ────────────────────────────────────────────────────────────────────


def _load_price_and_fx(
    db: Session, asset_code: str, period_years: int
) -> tuple[pd.Series, pd.Series | None, str, float]:
    """DB에서 가격 + 환율 로드. returns (prices, fx_series, currency, annual_yield)."""
    from dateutil.relativedelta import relativedelta

    from db.models import AssetMaster

    end_date = date_type.today()
    start_date = end_date - relativedelta(years=period_years)

    asset = db.query(AssetMaster).filter_by(asset_id=asset_code).first()
    currency = asset.currency if asset else ("USD" if asset_code in _USD_ASSETS else "KRW")
    annual_yield = float(asset.annual_yield) if asset else 0.0

    rows = (
        db.query(PriceDaily)
        .filter(PriceDaily.asset_id == asset_code, PriceDaily.date >= start_date, PriceDaily.date <= end_date)
        .order_by(PriceDaily.date)
        .all()
    )
    prices = pd.Series(
        {pd.Timestamp(r.date): float(r.close) for r in rows if r.close is not None},
        name="close",
    ).dropna() if rows else pd.Series(dtype=float)

    fx_series: pd.Series | None = None
    if currency == "USD" and not prices.empty:
        from research_engine.simulation.fx import load_fx_series
        fx_series = load_fx_series(db, prices.index[0].date(), prices.index[-1].date())

    return prices, fx_series, currency, annual_yield


def simulate_strategy(db: Session, req: SimulateStrategyRequest) -> SimulateStrategyResponse:
    """Tab B 전략 시뮬레이션 (Strategy A or B)."""
    from research_engine.simulation.replay import _first_trading_days_of_month

    prices, fx_series, currency, annual_yield = _load_price_and_fx(db, req.asset_code, req.period_years)
    if prices.empty:
        raise ValueError(f"가격 데이터 없음: {req.asset_code}")

    daily_yield_mult = 1.0 + annual_yield / 252.0
    trading_index = prices.index
    first_days = _first_trading_days_of_month(trading_index)
    period_start = trading_index[0].date()

    if req.strategy == "A":
        strategy = StrategyA(period_start=period_start)
    else:
        strategy = StrategyB()

    shares = 0.0
    total_deposit = 0
    event_count = 0
    curve: list[EquityPoint] = []
    strategy_cash = 0.0  # Strategy A 보유 현금

    last_trading_days_set: set[pd.Timestamp] = set()
    for year in range(trading_index[0].year, trading_index[-1].year + 1):
        yr_idx = trading_index[trading_index.year == year]
        if len(yr_idx):
            last_trading_days_set.add(yr_idx[-1])

    for i, ts in enumerate(trading_index):
        price = float(prices[ts])
        fx_rate: float | None = None
        if currency == "USD" and fx_series is not None:
            fx_rate = float(fx_series.asof(ts)) if ts in fx_series.index else float(fx_series.asof(ts))

        p60 = float(prices.iloc[i - 60]) if i >= 60 else None
        p20 = float(prices.iloc[i - 20]) if i >= 20 else None
        is_last_of_year = ts in last_trading_days_set

        # D-16: 적립 먼저
        if ts in first_days:
            if req.strategy == "A":
                # StrategyA: 전체 적립
                if currency == "USD" and fx_rate:
                    shares += (req.monthly_amount / fx_rate) / price
                else:
                    shares += req.monthly_amount / price
                total_deposit += req.monthly_amount
            else:
                # StrategyB: deposit() 호출
                sb: StrategyB = strategy  # type: ignore
                bought = sb.deposit(req.monthly_amount, price, fx_rate)
                shares += bought
                total_deposit += req.monthly_amount

        # 배당 재투자
        shares *= daily_yield_mult

        # 전략 step
        if req.strategy == "A":
            sa: StrategyA = strategy  # type: ignore
            result = sa.step(ts.date(), price, p60, p20, shares)
            if result["action"] == "SELL":
                strategy_cash = shares * StrategyA.SELL_PCT * price
                shares *= (1 - StrategyA.SELL_PCT)
                event_count += 1
            elif result["action"] in ("BUY", "FORCE_BUY"):
                cash = result.get("cash_raised", strategy_cash)
                if price > 0:
                    shares += cash / price
                strategy_cash = 0.0
                event_count += 1
        else:
            sb = strategy  # type: ignore
            result = sb.step(ts.date(), price, p20, is_last_of_year, fx_rate)
            if result["action"] is not None:
                shares += result["shares_bought"]
                event_count += 1

        # 평가
        local_value = shares * price
        krw_value = local_value * fx_rate if (currency == "USD" and fx_rate) else local_value
        if currency == "USD" and strategy_cash > 0 and fx_rate:
            krw_value += strategy_cash  # SOLD 상태 현금도 KRW로 반영

        curve.append(EquityPoint(date=ts.date(), krw_value=krw_value, local_value=local_value, shares=shares))

    kpi = compute_kpi(curve, total_deposit, req.period_years)
    return SimulateStrategyResponse(
        asset_code=req.asset_code,
        strategy=req.strategy,
        curve=[_to_equity_response(pt) for pt in curve],
        kpi=_to_kpi_response(kpi),
        event_count=event_count,
    )


# ── Tab C ────────────────────────────────────────────────────────────────────


def simulate_portfolio(db: Session, req: SimulatePortfolioRequest) -> SimulatePortfolioResponse:
    """Tab C 포트폴리오 적립식 시뮬레이션."""
    from dateutil.relativedelta import relativedelta

    from research_engine.simulation.replay import _first_trading_days_of_month

    if req.preset_key not in PRESETS:
        raise ValueError(f"알 수 없는 preset_key: {req.preset_key}. 선택 가능: {list(PRESETS.keys())}")

    preset = PRESETS[req.preset_key]
    portfolio = Portfolio(preset)
    asset_codes = list(preset.weights.keys())

    end_date = date_type.today()
    start_date = end_date - relativedelta(years=req.period_years)

    # 가격 + 환율 로드 (자산별)
    prices_map: dict[str, pd.Series] = {}
    fx_map: dict[str, pd.Series | None] = {}
    from db.models import AssetMaster
    from research_engine.simulation.fx import load_fx_series

    for code in asset_codes:
        rows = (
            db.query(PriceDaily)
            .filter(PriceDaily.asset_id == code, PriceDaily.date >= start_date, PriceDaily.date <= end_date)
            .order_by(PriceDaily.date)
            .all()
        )
        if rows:
            prices_map[code] = pd.Series(
                {pd.Timestamp(r.date): float(r.close) for r in rows}, name="close"
            )
        asset = db.query(AssetMaster).filter_by(asset_id=code).first()
        currency = asset.currency if asset else ("USD" if code in _USD_ASSETS else "KRW")
        if currency == "USD" and code in prices_map and not prices_map[code].empty:
            fx_map[code] = load_fx_series(db, prices_map[code].index[0].date(), prices_map[code].index[-1].date())
        else:
            fx_map[code] = None

    # 공통 trading days: 모든 자산의 합집합 (forward-fill로 결측 처리)
    all_dates = set()
    for s in prices_map.values():
        all_dates.update(s.index.tolist())
    trading_index = pd.DatetimeIndex(sorted(all_dates))

    if len(trading_index) == 0:
        raise ValueError("가격 데이터 없음")

    first_days = _first_trading_days_of_month(trading_index)
    last_trading_days_set: set[pd.Timestamp] = set()
    for year in range(trading_index[0].year, trading_index[-1].year + 1):
        yr_idx = trading_index[trading_index.year == year]
        if len(yr_idx):
            last_trading_days_set.add(yr_idx[-1])

    # annual_yield 조회
    annual_yields: dict[str, float] = {}
    for code in asset_codes:
        asset = db.query(AssetMaster).filter_by(asset_id=code).first()
        annual_yields[code] = float(asset.annual_yield) if asset else 0.0

    total_deposit = 0
    curve: list[EquityPoint] = []

    for ts in trading_index:
        # 현재 가격 (결측이면 이전 값 사용)
        prices_today: dict[str, float] = {}
        fx_today: dict[str, float | None] = {}
        for code in asset_codes:
            if code not in prices_map:
                continue
            s = prices_map[code]
            val = float(s.asof(ts)) if ts not in s.index else float(s[ts])
            if val > 0:
                prices_today[code] = val
            fx_s = fx_map.get(code)
            fx_today[code] = float(fx_s.asof(ts)) if fx_s is not None and not fx_s.empty else None

        if not prices_today:
            continue

        # D-16: 적립
        if ts in first_days:
            portfolio.deposit(req.monthly_amount, prices_today, fx_today)
            total_deposit += req.monthly_amount

        # 배당
        portfolio.apply_dividends(annual_yields, prices_today, fx_today)

        # 연말 리밸런싱
        if ts in last_trading_days_set:
            portfolio.rebalance(prices_today, fx_today)

        krw_value = portfolio.total_krw_value(prices_today, fx_today)
        # local_value = krw (단순화: multi-asset이라 local=KRW)
        curve.append(EquityPoint(date=ts.date(), krw_value=krw_value, local_value=krw_value, shares=0.0))

    kpi = compute_kpi(curve, total_deposit, req.period_years)
    return SimulatePortfolioResponse(
        preset_key=req.preset_key,
        preset_name=preset.name,
        curve=[_to_equity_response(pt) for pt in curve],
        kpi=_to_kpi_response(kpi),
    )

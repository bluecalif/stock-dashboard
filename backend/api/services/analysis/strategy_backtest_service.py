"""Strategy backtest service — on-the-fly backtest using indicator signals.

Converts indicator_signal_service signals into backtest-compatible format
and runs through the research_engine backtest pipeline.

Strategies:
  - momentum (MACD): 골든크로스 매수, 데드크로스 매도
  - contrarian (RSI): 과매도 매수, 과매수/해제 매도
  - risk_aversion (ATR+vol): 기본 투자, 고변동성 시 시장 탈출
"""

from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass

import pandas as pd
from sqlalchemy.orm import Session

from api.services.analysis.indicator_signal_service import (
    IndicatorSignal,
    generate_indicator_signals,
)
from research_engine.backtest import BacktestConfig, BacktestResult, run_backtest
from research_engine.metrics import PerformanceMetrics, compute_metrics
from research_engine.preprocessing import load_prices

logger = logging.getLogger(__name__)

# 전략 → 지표 매핑
STRATEGY_INDICATOR_MAP: dict[str, str] = {
    "momentum": "macd",
    "contrarian": "rsi_14",
    "risk_aversion": "atr_vol",
}

STRATEGY_LABELS: dict[str, str] = {
    "momentum": "모멘텀 (MACD)",
    "contrarian": "역발상 (RSI)",
    "risk_aversion": "위험회피 (ATR+변동성)",
}

# 기간 프리셋 → 일수 매핑
PERIOD_DAYS: dict[str, int] = {
    "6M": 180,
    "1Y": 365,
    "2Y": 730,
    "3Y": 1095,
}


@dataclass
class StrategyBacktestResult:
    """On-the-fly 전략 백테스트 결과."""

    asset_id: str
    strategy_name: str
    strategy_label: str
    period: str
    initial_cash: float
    metrics: PerformanceMetrics
    backtest_result: BacktestResult  # equity_curve, trades, buy_hold_equity
    indicator_signals: list[IndicatorSignal]  # 원본 시그널 (프론트 마커용)
    loss_avoided: float | None  # 위험회피 전략 전용: B&H 대비 손실 회피 금액


def run_strategy_backtest(
    db: Session,
    asset_id: str,
    strategy_name: str,
    *,
    period: str = "2Y",
    initial_cash: float = 100_000_000,
) -> StrategyBacktestResult:
    """지표 시그널 기반 on-the-fly 전략 백테스트 실행.

    Args:
        db: SQLAlchemy session.
        asset_id: 자산 ID (e.g. "005930").
        strategy_name: "momentum", "contrarian", "risk_aversion".
        period: 기간 프리셋 ("6M", "1Y", "2Y", "3Y").
        initial_cash: 초기 투자금 (기본 1억원).

    Returns:
        StrategyBacktestResult with metrics, equity curve, trades, narratives.

    Raises:
        ValueError: 잘못된 strategy_name 또는 데이터 부족.
    """
    if strategy_name not in STRATEGY_INDICATOR_MAP:
        available = list(STRATEGY_INDICATOR_MAP.keys())
        raise ValueError(
            f"Unknown strategy: {strategy_name}. Available: {available}"
        )

    indicator_id = STRATEGY_INDICATOR_MAP[strategy_name]

    # 기간 계산
    days = PERIOD_DAYS.get(period, 730)
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)
    # 시그널 생성에 lookback이 필요하므로 여유분 추가
    lookback_start = start_date - datetime.timedelta(days=200)

    # 1. 가격 데이터 로드
    prices_df = load_prices(db, asset_id, start=str(lookback_start), end=str(end_date))

    # 2. 지표 시그널 생성
    indicator_signals = generate_indicator_signals(
        db, asset_id, indicator_id,
        start_date=lookback_start,
        end_date=end_date,
    )

    # 3. 시그널 → 백테스트 입력 변환
    signals_df = _convert_signals_to_backtest_format(
        indicator_signals, prices_df, strategy_name, start_date, end_date,
    )

    if signals_df.empty:
        raise ValueError(
            f"No signals generated for {asset_id}/{strategy_name} "
            f"in period {start_date} ~ {end_date}"
        )

    # start_date 이후 가격만 사용
    prices_filtered = prices_df[prices_df.index >= pd.Timestamp(start_date)]

    # 4. 백테스트 실행
    config = BacktestConfig(initial_cash=initial_cash)
    bt_result = run_backtest(
        prices=prices_filtered,
        signals=signals_df,
        asset_id=asset_id,
        strategy_id=strategy_name,
        config=config,
    )

    # 5. 성과 지표 계산
    metrics = compute_metrics(bt_result)

    # 6. 위험회피 전략: 손실 회피 금액 계산
    loss_avoided = None
    if strategy_name == "risk_aversion":
        loss_avoided = _compute_loss_avoided(bt_result)

    # 기간 내 시그널만 필터
    period_signals = [
        s for s in indicator_signals
        if start_date <= s.date <= end_date
    ]

    logger.info(
        "Strategy backtest %s/%s (%s): %d trades, return=%.2f%%",
        asset_id, strategy_name, period,
        metrics.num_trades, metrics.total_return * 100,
    )

    return StrategyBacktestResult(
        asset_id=asset_id,
        strategy_name=strategy_name,
        strategy_label=STRATEGY_LABELS[strategy_name],
        period=period,
        initial_cash=initial_cash,
        metrics=metrics,
        backtest_result=bt_result,
        indicator_signals=period_signals,
        loss_avoided=loss_avoided,
    )


def _convert_signals_to_backtest_format(
    signals: list[IndicatorSignal],
    prices_df: pd.DataFrame,
    strategy_name: str,
    start_date: datetime.date,
    end_date: datetime.date,
) -> pd.DataFrame:
    """IndicatorSignal 리스트 → backtest.run_backtest 입력 DataFrame 변환.

    backtest 엔진은 모든 거래일에 signal 값이 필요:
      1 = 매수(보유), 0 = 매도(현금)

    Returns:
        DataFrame with columns: date, signal
    """
    # 거래일 리스트 (start_date 이후)
    all_dates = prices_df.index.date
    trade_dates = [d for d in all_dates if start_date <= d <= end_date]

    if not trade_dates:
        return pd.DataFrame(columns=["date", "signal"])

    if strategy_name == "risk_aversion":
        return _build_risk_aversion_signals(signals, trade_dates)
    else:
        return _build_entry_exit_signals(signals, trade_dates, strategy_name)


def _build_entry_exit_signals(
    signals: list[IndicatorSignal],
    trade_dates: list[datetime.date],
    strategy_name: str,
) -> pd.DataFrame:
    """모멘텀/역발상 전략: 시그널 기반 진입/퇴출 매핑.

    MACD: signal 1→buy(1), -1→exit(0)
    RSI:  signal 1→buy(1), -1→exit(0), 2(매수해제)→exit(0), -2(매도해제)→무시
    """
    # 시그널을 날짜별 매핑
    signal_map: dict[datetime.date, int] = {}
    for s in signals:
        raw = s.signal
        if raw == 1:
            signal_map[s.date] = 1  # 매수
        elif raw == -1:
            signal_map[s.date] = 0  # 매도
        elif raw == 2:
            signal_map[s.date] = 0  # 매수해제 → 매도
        # -2 (매도해제) — long-only이므로 무시

    # 전 거래일에 걸쳐 forward fill
    result_signals = []
    current_state = 0  # 초기 상태: 현금
    for d in trade_dates:
        if d in signal_map:
            current_state = signal_map[d]
        result_signals.append({"date": d, "signal": current_state})

    return pd.DataFrame(result_signals)


def _build_risk_aversion_signals(
    signals: list[IndicatorSignal],
    trade_dates: list[datetime.date],
) -> pd.DataFrame:
    """위험회피 전략: 기본 투자(1), 고변동성 시 탈출(0).

    ATR+vol 시그널은 모두 signal=0이므로 label로 구분:
      "고변동성 경고 진입" → exit(0)
      "정상 변동성 구간 복귀" → re-enter(1)
    """
    signal_map: dict[datetime.date, int] = {}
    for s in signals:
        if "고변동성" in s.label and "진입" in s.label:
            signal_map[s.date] = 0  # 시장 탈출
        elif "복귀" in s.label:
            signal_map[s.date] = 1  # 재진입

    # 기본 상태: 투자 중 (1)
    result_signals = []
    current_state = 1
    for d in trade_dates:
        if d in signal_map:
            current_state = signal_map[d]
        result_signals.append({"date": d, "signal": current_state})

    return pd.DataFrame(result_signals)


def _compute_loss_avoided(bt_result: BacktestResult) -> float:
    """위험회피 전략의 B&H 대비 손실 회피 금액 계산.

    탈출 구간에서 B&H가 하락한 금액 중 전략이 회피한 부분을 누적.
    loss_avoided = sum of max(0, bh_drawdown_during_exit) over exit periods.
    """
    eq = bt_result.equity_curve
    bh = bt_result.buy_hold_equity

    if eq.empty or bh.empty:
        return 0.0

    # 날짜 기준 머지
    merged = eq[["date", "equity"]].merge(
        bh[["date", "equity"]],
        on="date",
        suffixes=("_strategy", "_bh"),
    )

    if merged.empty:
        return 0.0

    # 각 거래의 진입~퇴출 사이 B&H 하락분 합산
    loss_avoided = 0.0
    for trade in bt_result.trades:
        if trade.exit_date is None:
            continue
        # 탈출 시점 ~ 재진입 시점 사이 B&H 변화 확인
        # 이 구간에서 B&H가 하락했다면 그 금액이 회피된 손실
        exit_mask = merged["date"] == pd.Timestamp(trade.exit_date)
        entry_mask = merged["date"] == pd.Timestamp(trade.entry_date)

        exit_rows = merged[exit_mask]
        entry_rows = merged[entry_mask]

        if exit_rows.empty or entry_rows.empty:
            continue

        bh_at_entry = entry_rows["equity_bh"].iloc[0]
        bh_at_exit = exit_rows["equity_bh"].iloc[0]
        bh_change = bh_at_exit - bh_at_entry

        # B&H가 하락한 경우만 손실 회피로 계산
        if bh_change < 0:
            loss_avoided += abs(bh_change)

    return round(loss_avoided, 0)

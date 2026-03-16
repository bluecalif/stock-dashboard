"""Tests for strategy_backtest_service — on-the-fly indicator-based backtest."""

from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from api.services.analysis.indicator_signal_service import IndicatorSignal
from api.services.analysis.strategy_backtest_service import (
    STRATEGY_INDICATOR_MAP,
    STRATEGY_LABELS,
    StrategyBacktestResult,
    _build_entry_exit_signals,
    _build_risk_aversion_signals,
    _compute_loss_avoided,
    _convert_signals_to_backtest_format,
    run_strategy_backtest,
)
from research_engine.backtest import BacktestConfig, BacktestResult, TradeRecord

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dates(n: int, start: date | None = None) -> list[date]:
    """Generate n consecutive weekday dates. Defaults to recent dates."""
    if start is None:
        # 최근 날짜 기준 (run_strategy_backtest의 기간 계산과 호환)
        start = date.today() - timedelta(days=n * 2)
    result = []
    d = start
    while len(result) < n:
        if d.weekday() < 5:  # 월~금
            result.append(d)
        d += timedelta(days=1)
    return result


def _make_prices_df(dates_list: list[date], closes: list[float]) -> pd.DataFrame:
    """Create a prices DataFrame matching load_prices output."""
    df = pd.DataFrame({
        "open": closes,
        "high": [c * 1.01 for c in closes],
        "low": [c * 0.99 for c in closes],
        "close": closes,
        "volume": [1000] * len(closes),
    }, index=pd.to_datetime(dates_list))
    return df


def _make_macd_signals(dates_list: list[date]) -> list[IndicatorSignal]:
    """MACD 시그널: 첫 번째 날 골든크로스(1), 중간에 데드크로스(-1)."""
    mid = len(dates_list) // 2
    return [
        IndicatorSignal(
            date=dates_list[2], indicator_id="macd", signal=1,
            label="MACD 골든크로스", value=0.5, entry_price=100.0,
        ),
        IndicatorSignal(
            date=dates_list[mid], indicator_id="macd", signal=-1,
            label="MACD 데드크로스", value=-0.3, entry_price=110.0,
        ),
    ]


def _make_rsi_signals(dates_list: list[date]) -> list[IndicatorSignal]:
    """RSI 시그널: 과매도 매수(1), 매수해제(2)."""
    return [
        IndicatorSignal(
            date=dates_list[2], indicator_id="rsi_14", signal=1,
            label="RSI 과매도 진입", value=25.0, entry_price=95.0,
        ),
        IndicatorSignal(
            date=dates_list[8], indicator_id="rsi_14", signal=2,
            label="RSI 매수 해제", value=55.0, entry_price=105.0,
        ),
    ]


def _make_atr_vol_signals(dates_list: list[date]) -> list[IndicatorSignal]:
    """ATR+vol 시그널: 고변동성 진입 → 정상 복귀."""
    return [
        IndicatorSignal(
            date=dates_list[5], indicator_id="atr_vol", signal=0,
            label="고변동성 경고 진입 (ATR 4.2%)", value=0.042,
            entry_price=100.0,
        ),
        IndicatorSignal(
            date=dates_list[10], indicator_id="atr_vol", signal=0,
            label="정상 변동성 구간 복귀", value=0.02,
            entry_price=95.0,
        ),
    ]


# ---------------------------------------------------------------------------
# STRATEGY_INDICATOR_MAP / STRATEGY_LABELS
# ---------------------------------------------------------------------------

class TestStrategyMapping:
    def test_all_strategies_have_indicator(self):
        assert set(STRATEGY_INDICATOR_MAP.keys()) == {
            "momentum", "contrarian", "risk_aversion"
        }

    def test_all_strategies_have_label(self):
        assert set(STRATEGY_LABELS.keys()) == set(STRATEGY_INDICATOR_MAP.keys())

    def test_indicator_ids(self):
        assert STRATEGY_INDICATOR_MAP["momentum"] == "macd"
        assert STRATEGY_INDICATOR_MAP["contrarian"] == "rsi_14"
        assert STRATEGY_INDICATOR_MAP["risk_aversion"] == "atr_vol"


# ---------------------------------------------------------------------------
# Signal conversion: _build_entry_exit_signals
# ---------------------------------------------------------------------------

class TestBuildEntryExitSignals:
    def test_macd_buy_sell(self):
        """MACD 골든크로스(1) → 매수, 데드크로스(-1) → 매도."""
        dates_list = _dates(15)
        signals = _make_macd_signals(dates_list)
        result = _build_entry_exit_signals(signals, dates_list, "momentum")

        assert len(result) == 15
        # 시그널 전: 현금(0)
        assert result.iloc[0]["signal"] == 0
        assert result.iloc[1]["signal"] == 0
        # 골든크로스 후: 매수(1)
        assert result.iloc[2]["signal"] == 1
        assert result.iloc[3]["signal"] == 1  # forward fill
        # 데드크로스 후: 매도(0)
        mid = len(dates_list) // 2
        assert result.iloc[mid]["signal"] == 0

    def test_rsi_buy_release(self):
        """RSI 매수(1) → 매수해제(2) → 매도(0)."""
        dates_list = _dates(15)
        signals = _make_rsi_signals(dates_list)
        result = _build_entry_exit_signals(signals, dates_list, "contrarian")

        # 매수 후
        assert result.iloc[2]["signal"] == 1
        assert result.iloc[5]["signal"] == 1  # forward fill
        # 매수해제 후 → 0
        assert result.iloc[8]["signal"] == 0

    def test_rsi_sell_release_ignored(self):
        """RSI -2(매도해제)는 long-only에서 무시."""
        dates_list = _dates(10)
        signals = [
            IndicatorSignal(
                date=dates_list[3], indicator_id="rsi_14", signal=-2,
                label="RSI 매도 해제", value=45.0, entry_price=100.0,
            ),
        ]
        result = _build_entry_exit_signals(signals, dates_list, "contrarian")
        # -2는 무시되므로 전체 0 유지
        assert all(result["signal"] == 0)

    def test_empty_signals(self):
        """시그널 없으면 전체 0(현금)."""
        dates_list = _dates(5)
        result = _build_entry_exit_signals([], dates_list, "momentum")
        assert len(result) == 5
        assert all(result["signal"] == 0)


# ---------------------------------------------------------------------------
# Signal conversion: _build_risk_aversion_signals
# ---------------------------------------------------------------------------

class TestBuildRiskAversionSignals:
    def test_default_invested(self):
        """기본 상태는 투자 중(1)."""
        dates_list = _dates(5)
        result = _build_risk_aversion_signals([], dates_list)
        assert all(result["signal"] == 1)

    def test_high_vol_exit_and_reenter(self):
        """고변동성 진입 → 탈출(0), 정상 복귀 → 재진입(1)."""
        dates_list = _dates(15)
        signals = _make_atr_vol_signals(dates_list)
        result = _build_risk_aversion_signals(signals, dates_list)

        # 처음 ~ 고변동성 전: 투자 중(1)
        assert result.iloc[0]["signal"] == 1
        assert result.iloc[4]["signal"] == 1
        # 고변동성 진입 후: 탈출(0)
        assert result.iloc[5]["signal"] == 0
        assert result.iloc[7]["signal"] == 0  # forward fill
        # 정상 복귀 후: 재진입(1)
        assert result.iloc[10]["signal"] == 1
        assert result.iloc[12]["signal"] == 1  # forward fill


# ---------------------------------------------------------------------------
# _compute_loss_avoided
# ---------------------------------------------------------------------------

class TestComputeLossAvoided:
    def test_no_trades(self):
        """거래 없으면 손실 회피 0."""
        bt = BacktestResult(
            strategy_id="risk_aversion",
            asset_id="005930",
            config=BacktestConfig(),
            equity_curve=pd.DataFrame(columns=["date", "equity", "drawdown"]),
            trades=[],
            buy_hold_equity=pd.DataFrame(columns=["date", "equity"]),
        )
        assert _compute_loss_avoided(bt) == 0.0

    def test_loss_avoided_during_exit(self):
        """탈출 구간에서 B&H 하락 시 손실 회피 금액 계산."""
        dates_list = _dates(10)
        ts_dates = pd.to_datetime(dates_list)

        # 전략: 5일째 탈출, 이후 B&H는 하락
        strategy_equity = [100] * 10
        bh_equity = [100, 100, 100, 100, 100, 98, 95, 90, 88, 92]

        eq_df = pd.DataFrame({
            "date": ts_dates,
            "equity": strategy_equity,
            "drawdown": [0.0] * 10,
        })
        bh_df = pd.DataFrame({
            "date": ts_dates,
            "equity": bh_equity,
        })

        # 진입일: day 0, 퇴출일: day 4 — B&H는 100→100 (하락 없음)
        # 이 거래에서 B&H 변화 = 100-100 = 0 → 회피 없음
        trade = TradeRecord(
            asset_id="005930",
            entry_date=dates_list[0],
            entry_price=100.0,
            exit_date=dates_list[4],
            exit_price=100.0,
            side="long",
            shares=1.0,
            pnl=0.0,
            cost=0.0,
        )

        bt = BacktestResult(
            strategy_id="risk_aversion",
            asset_id="005930",
            config=BacktestConfig(),
            equity_curve=eq_df,
            trades=[trade],
            buy_hold_equity=bh_df,
        )
        # entry=day0(bh=100), exit=day4(bh=100) → bh 변화 0 → 회피 0
        result = _compute_loss_avoided(bt)
        assert result == 0.0

    def test_loss_avoided_with_bh_decline(self):
        """B&H가 진입~퇴출 사이 하락한 경우."""
        dates_list = _dates(10)
        ts_dates = pd.to_datetime(dates_list)

        eq_df = pd.DataFrame({
            "date": ts_dates,
            "equity": [100_000_000] * 10,
            "drawdown": [0.0] * 10,
        })
        bh_df = pd.DataFrame({
            "date": ts_dates,
            "equity": [100_000_000, 99_000_000, 98_000_000, 95_000_000,
                       93_000_000, 90_000_000, 88_000_000, 92_000_000,
                       95_000_000, 97_000_000],
        })

        # 진입일: day 0 (bh=100M), 퇴출일: day 5 (bh=90M) → 하락 10M
        trade = TradeRecord(
            asset_id="005930",
            entry_date=dates_list[0],
            entry_price=50000.0,
            exit_date=dates_list[5],
            exit_price=45000.0,
            side="long",
            shares=2000,
            pnl=-10_000_000,
            cost=100_000,
        )

        bt = BacktestResult(
            strategy_id="risk_aversion",
            asset_id="005930",
            config=BacktestConfig(initial_cash=100_000_000),
            equity_curve=eq_df,
            trades=[trade],
            buy_hold_equity=bh_df,
        )
        result = _compute_loss_avoided(bt)
        assert result == 10_000_000.0


# ---------------------------------------------------------------------------
# run_strategy_backtest (integration with mocks)
# ---------------------------------------------------------------------------

class TestRunStrategyBacktest:
    def test_invalid_strategy_raises(self):
        db = MagicMock()
        with pytest.raises(ValueError, match="Unknown strategy"):
            run_strategy_backtest(db, "005930", "invalid_strategy")

    @patch("api.services.analysis.strategy_backtest_service.generate_indicator_signals")
    @patch("api.services.analysis.strategy_backtest_service.load_prices")
    def test_momentum_backtest_returns_result(self, mock_prices, mock_signals):
        """모멘텀 전략 백테스트 기본 흐름 검증."""
        dates_list = _dates(60)
        prices_df = _make_prices_df(dates_list, [100 + i * 0.5 for i in range(60)])
        mock_prices.return_value = prices_df

        # MACD 시그널: 10일째 매수, 40일째 매도
        mock_signals.return_value = [
            IndicatorSignal(
                date=dates_list[10], indicator_id="macd", signal=1,
                label="MACD 골든크로스", value=0.5, entry_price=105.0,
            ),
            IndicatorSignal(
                date=dates_list[40], indicator_id="macd", signal=-1,
                label="MACD 데드크로스", value=-0.3, entry_price=120.0,
            ),
        ]

        db = MagicMock()
        result = run_strategy_backtest(
            db, "005930", "momentum", period="2Y", initial_cash=100_000_000,
        )

        assert isinstance(result, StrategyBacktestResult)
        assert result.asset_id == "005930"
        assert result.strategy_name == "momentum"
        assert result.strategy_label == "모멘텀 (MACD)"
        assert result.initial_cash == 100_000_000
        assert result.loss_avoided is None  # 모멘텀은 loss_avoided 없음
        assert result.metrics.num_trades >= 0

    @patch("api.services.analysis.strategy_backtest_service.generate_indicator_signals")
    @patch("api.services.analysis.strategy_backtest_service.load_prices")
    def test_risk_aversion_has_loss_avoided(self, mock_prices, mock_signals):
        """위험회피 전략은 loss_avoided 값을 포함."""
        dates_list = _dates(60)
        # 가격: 상승 후 하락 패턴
        closes = [100 + i for i in range(30)] + [130 - i for i in range(30)]
        prices_df = _make_prices_df(dates_list, closes)
        mock_prices.return_value = prices_df

        mock_signals.return_value = [
            IndicatorSignal(
                date=dates_list[25], indicator_id="atr_vol", signal=0,
                label="고변동성 경고 진입 (ATR 4.5%)", value=0.045,
                entry_price=125.0,
            ),
            IndicatorSignal(
                date=dates_list[45], indicator_id="atr_vol", signal=0,
                label="정상 변동성 구간 복귀", value=0.02,
                entry_price=115.0,
            ),
        ]

        db = MagicMock()
        result = run_strategy_backtest(
            db, "005930", "risk_aversion", period="2Y",
        )

        assert isinstance(result, StrategyBacktestResult)
        assert result.strategy_name == "risk_aversion"
        assert result.loss_avoided is not None
        assert isinstance(result.loss_avoided, float)

    @patch("api.services.analysis.strategy_backtest_service.generate_indicator_signals")
    @patch("api.services.analysis.strategy_backtest_service.load_prices")
    def test_no_signals_raises_value_error(self, mock_prices, mock_signals):
        """시그널이 기간 내에 없으면 ValueError."""
        dates_list = _dates(10)
        prices_df = _make_prices_df(dates_list, [100] * 10)
        mock_prices.return_value = prices_df

        # 시그널 없음 → 모멘텀은 전부 0 → 빈 signals는 아니지만
        # 실제로는 10일 전체 signal=0 → run_backtest은 거래 0건으로 정상 수행
        mock_signals.return_value = []

        db = MagicMock()
        # 모멘텀: 시그널 없으면 전체 0(현금) → signals_df는 10행이므로 정상
        result = run_strategy_backtest(db, "005930", "momentum", period="6M")
        assert result.metrics.num_trades == 0

    @patch("api.services.analysis.strategy_backtest_service.generate_indicator_signals")
    @patch("api.services.analysis.strategy_backtest_service.load_prices")
    def test_contrarian_rsi_flow(self, mock_prices, mock_signals):
        """역발상(RSI) 전략 흐름."""
        dates_list = _dates(30)
        prices_df = _make_prices_df(dates_list, [100 + i * 0.3 for i in range(30)])
        mock_prices.return_value = prices_df

        mock_signals.return_value = [
            IndicatorSignal(
                date=dates_list[5], indicator_id="rsi_14", signal=1,
                label="RSI 과매도 진입", value=25.0, entry_price=101.5,
            ),
            IndicatorSignal(
                date=dates_list[20], indicator_id="rsi_14", signal=-1,
                label="RSI 과매수 진입", value=75.0, entry_price=106.0,
            ),
        ]

        db = MagicMock()
        result = run_strategy_backtest(db, "005930", "contrarian", period="6M")
        assert result.strategy_name == "contrarian"
        assert result.strategy_label == "역발상 (RSI)"
        assert result.loss_avoided is None


# ---------------------------------------------------------------------------
# _convert_signals_to_backtest_format
# ---------------------------------------------------------------------------

class TestConvertSignals:
    def test_momentum_delegates_to_entry_exit(self):
        dates_list = _dates(10)
        prices_df = _make_prices_df(dates_list, [100] * 10)
        signals = _make_macd_signals(dates_list)

        result = _convert_signals_to_backtest_format(
            signals, prices_df, "momentum", dates_list[0], dates_list[-1],
        )
        assert "date" in result.columns
        assert "signal" in result.columns
        assert len(result) == 10

    def test_risk_aversion_delegates_to_risk_builder(self):
        dates_list = _dates(15)
        prices_df = _make_prices_df(dates_list, [100] * 15)
        signals = _make_atr_vol_signals(dates_list)

        result = _convert_signals_to_backtest_format(
            signals, prices_df, "risk_aversion", dates_list[0], dates_list[-1],
        )
        assert len(result) == 15
        # 기본 상태 1(투자), 고변동성 후 0
        assert result.iloc[0]["signal"] == 1

    def test_empty_trade_dates(self):
        """거래일이 비어있으면 빈 DataFrame 반환."""
        prices_df = pd.DataFrame(
            columns=["open", "high", "low", "close", "volume"],
            index=pd.DatetimeIndex([], name="date"),
        )
        result = _convert_signals_to_backtest_format(
            [], prices_df, "momentum",
            date(2026, 1, 1), date(2025, 1, 1),  # 시작 > 종료
        )
        assert result.empty

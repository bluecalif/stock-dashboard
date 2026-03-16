"""Tests for storytelling_service — trade narratives and strategy summaries."""

from datetime import date

from api.services.analysis.annual_performance_service import AnnualPerformance
from api.services.analysis.storytelling_service import (
    TradeNarrative,
    _calc_holding_days,
    _calc_pnl_pct,
    generate_strategy_summary,
    generate_trade_narratives,
    trade_narratives_to_dicts,
)
from research_engine.backtest import TradeRecord

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _trade(
    entry: date = date(2025, 3, 1),
    exit_d: date | None = date(2025, 4, 1),
    entry_price: float = 50000,
    exit_price: float | None = 55000,
    pnl: float | None = 500_000,
    shares: float = 100,
) -> TradeRecord:
    return TradeRecord(
        asset_id="005930",
        entry_date=entry,
        entry_price=entry_price,
        exit_date=exit_d,
        exit_price=exit_price,
        side="long",
        shares=shares,
        pnl=pnl,
        cost=1000,
    )


# ---------------------------------------------------------------------------
# _calc_pnl_pct
# ---------------------------------------------------------------------------

class TestCalcPnlPct:
    def test_positive_pnl(self):
        t = _trade(pnl=500_000, entry_price=50000, shares=100)
        result = _calc_pnl_pct(t)
        assert result is not None
        assert abs(result - 0.1) < 0.001  # 500K / (50K * 100) = 0.1

    def test_negative_pnl(self):
        t = _trade(pnl=-200_000, entry_price=50000, shares=100)
        result = _calc_pnl_pct(t)
        assert result is not None
        assert result < 0

    def test_none_pnl(self):
        t = _trade(pnl=None)
        assert _calc_pnl_pct(t) is None

    def test_zero_entry_price(self):
        t = _trade(entry_price=0)
        assert _calc_pnl_pct(t) is None


# ---------------------------------------------------------------------------
# _calc_holding_days
# ---------------------------------------------------------------------------

class TestCalcHoldingDays:
    def test_normal(self):
        t = _trade(entry=date(2025, 3, 1), exit_d=date(2025, 4, 1))
        assert _calc_holding_days(t) == 31

    def test_open_position(self):
        t = _trade(exit_d=None)
        assert _calc_holding_days(t) == 0


# ---------------------------------------------------------------------------
# generate_trade_narratives
# ---------------------------------------------------------------------------

class TestGenerateTradeNarratives:
    def test_empty_trades(self):
        assert generate_trade_narratives([], "momentum") == []

    def test_single_trade(self):
        trades = [_trade()]
        result = generate_trade_narratives(trades, "momentum")
        assert len(result) == 1
        assert isinstance(result[0], TradeNarrative)
        # 단일 거래: best이자 worst가 아님 (같은 거래 → best만)
        assert result[0].is_best is True
        assert result[0].is_worst is False

    def test_best_worst_identification(self):
        """PnL 기준 Best/Worst 식별."""
        trades = [
            _trade(pnl=1_000_000, entry=date(2025, 1, 1), exit_d=date(2025, 2, 1)),
            _trade(pnl=-500_000, entry=date(2025, 3, 1), exit_d=date(2025, 4, 1)),
            _trade(pnl=200_000, entry=date(2025, 5, 1), exit_d=date(2025, 6, 1)),
        ]
        result = generate_trade_narratives(trades, "momentum")
        assert len(result) == 3

        best = [n for n in result if n.is_best]
        worst = [n for n in result if n.is_worst]
        assert len(best) == 1
        assert len(worst) == 1
        assert best[0].pnl == 1_000_000
        assert worst[0].pnl == -500_000

    def test_open_position_narrative(self):
        """미청산 포지션은 '보유 중' 내러티브."""
        trades = [_trade(exit_d=None, exit_price=None, pnl=None)]
        result = generate_trade_narratives(trades, "momentum")
        assert "보유 중" in result[0].narrative

    def test_risk_aversion_narrative(self):
        """위험회피 전략 특수 내러티브."""
        trades = [
            _trade(pnl=-100_000),
            _trade(pnl=300_000, entry=date(2025, 5, 1), exit_d=date(2025, 6, 1)),
        ]
        result = generate_trade_narratives(
            trades, "risk_aversion", loss_avoided=500_000,
        )
        # 손실 거래: "손실을 제한" 포함
        loss_narrative = next(n for n in result if n.pnl == -100_000)
        assert "손실을 제한" in loss_narrative.narrative

        # 수익 거래: "안전하게 재진입" 포함
        profit_narrative = next(n for n in result if n.pnl == 300_000)
        assert "재진입" in profit_narrative.narrative

    def test_large_move_narrative(self):
        """대폭 변동 (>10%) 내러티브."""
        trades = [_trade(pnl=600_000, entry_price=50000, shares=100)]
        # pnl_pct = 600K / (50K * 100) = 12%
        result = generate_trade_narratives(trades, "momentum")
        assert "대폭" in result[0].narrative

    def test_long_holding_narrative(self):
        """장기 보유 (>60일) 내러티브."""
        trades = [_trade(
            entry=date(2025, 1, 1), exit_d=date(2025, 4, 1),
        )]
        result = generate_trade_narratives(trades, "momentum")
        assert "장기 보유" in result[0].narrative


# ---------------------------------------------------------------------------
# generate_strategy_summary
# ---------------------------------------------------------------------------

class TestGenerateStrategySummary:
    def test_basic_summary(self):
        result = generate_strategy_summary(
            "momentum", total_return=0.15, num_trades=10, win_rate=0.6,
            annual_performances=[],
        )
        assert "모멘텀" in result
        assert "10회" in result
        assert "+15.0%" in result
        assert "60%" in result

    def test_risk_aversion_loss_avoided(self):
        result = generate_strategy_summary(
            "risk_aversion", total_return=0.05, num_trades=5, win_rate=0.4,
            annual_performances=[], loss_avoided=5_000_000,
        )
        assert "₩5,000,000" in result
        assert "손실을 회피" in result

    def test_annual_performance_summary(self):
        perfs = [
            AnnualPerformance(2023, 0.1, 10_000_000, -0.05, 3, 0.67,
                              True, False, 250),
            AnnualPerformance(2024, -0.05, -5_000_000, -0.1, 4, 0.25,
                              False, False, 250),
        ]
        result = generate_strategy_summary(
            "contrarian", total_return=0.05, num_trades=7, win_rate=0.5,
            annual_performances=perfs,
        )
        assert "2023" in result
        assert "적합" in result
        assert "2024" in result
        assert "부적합" in result

    def test_no_trades(self):
        result = generate_strategy_summary(
            "momentum", total_return=0.0, num_trades=0, win_rate=0.0,
            annual_performances=[],
        )
        assert "0회" in result
        # 승률 부분은 생략됨
        assert "승률" not in result


# ---------------------------------------------------------------------------
# trade_narratives_to_dicts
# ---------------------------------------------------------------------------

class TestTradeNarrativesToDicts:
    def test_serialization(self):
        narrative = TradeNarrative(
            entry_date=date(2025, 3, 1),
            exit_date=date(2025, 4, 1),
            entry_price=50000,
            exit_price=55000,
            pnl=500_000,
            pnl_pct=0.1,
            holding_days=31,
            narrative="테스트 내러티브",
            is_best=True,
            is_worst=False,
        )
        result = trade_narratives_to_dicts([narrative])
        assert len(result) == 1
        d = result[0]
        assert d["entry_date"] == "2025-03-01"
        assert d["exit_date"] == "2025-04-01"
        assert d["pnl"] == 500_000
        assert d["is_best"] is True
        assert d["narrative"] == "테스트 내러티브"

    def test_open_position(self):
        narrative = TradeNarrative(
            entry_date=date(2025, 3, 1),
            exit_date=None,
            entry_price=50000,
            exit_price=None,
            pnl=None,
            pnl_pct=None,
            holding_days=0,
            narrative="보유 중",
            is_best=False,
            is_worst=False,
        )
        result = trade_narratives_to_dicts([narrative])
        assert result[0]["exit_date"] is None
        assert result[0]["pnl"] is None

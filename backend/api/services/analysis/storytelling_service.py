"""Event storytelling service — generate trade narratives and strategy summaries.

Identifies best/worst trades and generates human-readable narratives
for each trade based on PnL, holding period, and strategy context.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from api.services.analysis.annual_performance_service import AnnualPerformance
from research_engine.backtest import TradeRecord

logger = logging.getLogger(__name__)

# 내러티브 생성 기준값
LONG_HOLDING_DAYS = 60  # 장기보유 기준
LARGE_MOVE_PCT = 0.10  # 대폭변동 기준 (10%)

# 전략별 한국어 라벨
STRATEGY_NAME_KR: dict[str, str] = {
    "momentum": "모멘텀",
    "contrarian": "역발상",
    "risk_aversion": "위험회피",
}


@dataclass
class TradeNarrative:
    """거래별 상세 내러티브."""

    entry_date: date
    exit_date: date | None
    entry_price: float
    exit_price: float | None
    pnl: float | None
    pnl_pct: float | None  # 수익률 (소수)
    holding_days: int
    narrative: str  # 한국어 내러티브 텍스트
    is_best: bool
    is_worst: bool


def generate_trade_narratives(
    trades: list[TradeRecord],
    strategy_name: str,
    *,
    loss_avoided: float | None = None,
) -> list[TradeNarrative]:
    """거래 목록에서 내러티브를 생성하고 Best/Worst를 식별.

    Args:
        trades: BacktestResult.trades 리스트.
        strategy_name: "momentum", "contrarian", "risk_aversion".
        loss_avoided: 위험회피 전략의 B&H 대비 손실 회피 금액.

    Returns:
        TradeNarrative 리스트 (시간순).
    """
    if not trades:
        return []

    # 청산된 거래만 PnL 기준 Best/Worst 판별
    closed = [t for t in trades if t.exit_date is not None and t.pnl is not None]
    best_trade: TradeRecord | None = None
    worst_trade: TradeRecord | None = None

    if closed:
        best_trade = max(closed, key=lambda t: t.pnl)
        worst_trade = min(closed, key=lambda t: t.pnl)
        # 같은 거래일 경우 best만 표시
        if best_trade is worst_trade:
            worst_trade = None

    narratives: list[TradeNarrative] = []
    strategy_kr = STRATEGY_NAME_KR.get(strategy_name, strategy_name)

    for trade in trades:
        is_best = trade is best_trade
        is_worst = trade is worst_trade

        pnl_pct = _calc_pnl_pct(trade)
        holding_days = _calc_holding_days(trade)
        narrative = _build_narrative(
            trade, strategy_name, strategy_kr,
            pnl_pct, holding_days,
            is_best, is_worst, loss_avoided,
        )

        narratives.append(TradeNarrative(
            entry_date=trade.entry_date,
            exit_date=trade.exit_date,
            entry_price=trade.entry_price,
            exit_price=trade.exit_price,
            pnl=trade.pnl,
            pnl_pct=round(pnl_pct, 6) if pnl_pct is not None else None,
            holding_days=holding_days,
            narrative=narrative,
            is_best=is_best,
            is_worst=is_worst,
        ))

    return narratives


def generate_strategy_summary(
    strategy_name: str,
    total_return: float,
    num_trades: int,
    win_rate: float,
    annual_performances: list[AnnualPerformance],
    *,
    loss_avoided: float | None = None,
) -> str:
    """전략 전체 요약 텍스트 생성.

    Args:
        strategy_name: 전략 이름.
        total_return: 누적 수익률 (소수).
        num_trades: 총 거래 횟수.
        win_rate: 승률 (0~1).
        annual_performances: 연간 성과 리스트.
        loss_avoided: 위험회피 전략 손실 회피 금액.

    Returns:
        한국어 요약 텍스트.
    """
    strategy_kr = STRATEGY_NAME_KR.get(strategy_name, strategy_name)
    return_pct_str = f"{total_return * 100:+.1f}%"

    parts: list[str] = []

    # 기본 요약
    parts.append(
        f"{strategy_kr} 전략은 총 {num_trades}회 거래하여 "
        f"누적 수익률 {return_pct_str}을 기록했습니다."
    )

    # 승률
    if num_trades > 0:
        parts.append(f"승률은 {win_rate * 100:.0f}%입니다.")

    # 위험회피 전략 특수: 손실 회피 금액
    if strategy_name == "risk_aversion" and loss_avoided is not None and loss_avoided > 0:
        avoided_str = f"₩{loss_avoided:,.0f}"
        parts.append(
            f"변동성 급등 시 시장 탈출로 Buy & Hold 대비 약 {avoided_str}의 "
            f"손실을 회피했습니다."
        )

    # 연간 성과 요약
    if annual_performances:
        favorable_years = [p for p in annual_performances if p.is_favorable]
        unfavorable_years = [p for p in annual_performances if not p.is_favorable]

        if favorable_years:
            years_str = ", ".join(str(p.year) for p in favorable_years)
            parts.append(f"적합 구간: {years_str}년.")

        if unfavorable_years:
            years_str = ", ".join(str(p.year) for p in unfavorable_years)
            parts.append(f"부적합 구간: {years_str}년.")

    return " ".join(parts)


def trade_narratives_to_dicts(narratives: list[TradeNarrative]) -> list[dict]:
    """TradeNarrative 리스트 → JSON-friendly dict 리스트."""
    return [
        {
            "entry_date": str(n.entry_date),
            "exit_date": str(n.exit_date) if n.exit_date else None,
            "entry_price": n.entry_price,
            "exit_price": n.exit_price,
            "pnl": round(n.pnl, 0) if n.pnl is not None else None,
            "pnl_pct": n.pnl_pct,
            "holding_days": n.holding_days,
            "narrative": n.narrative,
            "is_best": n.is_best,
            "is_worst": n.is_worst,
        }
        for n in narratives
    ]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _calc_pnl_pct(trade: TradeRecord) -> float | None:
    """거래 수익률 계산."""
    if trade.pnl is None or trade.entry_price <= 0 or trade.shares <= 0:
        return None
    cost = trade.entry_price * trade.shares
    return trade.pnl / cost


def _calc_holding_days(trade: TradeRecord) -> int:
    """보유 일수 계산."""
    if trade.exit_date is None:
        return 0
    return (trade.exit_date - trade.entry_date).days


def _build_narrative(
    trade: TradeRecord,
    strategy_name: str,
    strategy_kr: str,
    pnl_pct: float | None,
    holding_days: int,
    is_best: bool,
    is_worst: bool,
    loss_avoided: float | None,
) -> str:
    """거래별 내러티브 텍스트 생성."""
    parts: list[str] = []

    # 미청산 포지션
    if trade.exit_date is None:
        parts.append(
            f"{trade.entry_date} 진입 (₩{trade.entry_price:,.0f}), 현재 보유 중."
        )
        return " ".join(parts)

    # 기본 정보
    pnl_str = f"₩{trade.pnl:+,.0f}" if trade.pnl is not None else "미확정"
    entry_str = f"₩{trade.entry_price:,.0f}"
    exit_str = f"₩{trade.exit_price:,.0f}" if trade.exit_price else "미확정"

    parts.append(
        f"{trade.entry_date} → {trade.exit_date} "
        f"({holding_days}일 보유). "
        f"진입 {entry_str}, 청산 {exit_str}. "
        f"손익 {pnl_str}."
    )

    # 수익률 표시
    if pnl_pct is not None:
        parts.append(f"수익률 {pnl_pct * 100:+.1f}%.")

    # Best/Worst 라벨
    if is_best:
        parts.append("★ 최고 수익 거래.")
    if is_worst:
        parts.append("▼ 최대 손실 거래.")

    # 장기보유
    if holding_days > LONG_HOLDING_DAYS:
        parts.append(f"장기 보유 ({holding_days}일).")

    # 대폭 변동
    if pnl_pct is not None and abs(pnl_pct) > LARGE_MOVE_PCT:
        direction = "상승" if pnl_pct > 0 else "하락"
        parts.append(f"대폭 {direction} ({pnl_pct * 100:+.1f}%).")

    # 위험회피 전략 특수 내러티브
    if strategy_name == "risk_aversion":
        if trade.pnl is not None and trade.pnl < 0:
            parts.append("변동성 급등 구간에서 손실을 제한했습니다.")
        elif trade.pnl is not None and trade.pnl >= 0:
            parts.append("시장 탈출 후 안전하게 재진입했습니다.")

    return " ".join(parts)

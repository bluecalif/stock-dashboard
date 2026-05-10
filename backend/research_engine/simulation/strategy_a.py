"""전략 A — 고가 매도 후 저가 재매수 (마스터플랜 §3.4).

D-lock:
  D-6  트리거 = 현지통화 가격 기준
  D-7  강제 재매수 = 매도일 + 365일
  D-8  lock_until_year = 재매수 시점 연도 (매도 시점 X)
  D-9  grace period = 12개월
  D-16 이벤트 순서 = 정기 적립 먼저 → strategy.step()
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Literal

from dateutil.relativedelta import relativedelta

STATE_NEUTRAL: Literal["NEUTRAL"] = "NEUTRAL"
STATE_SOLD: Literal["SOLD"] = "SOLD"


class StrategyA:
    """고가 매도(30%) + 저가/강제 재매수 전략.

    Usage:
        sa = StrategyA(period_start=date(2015, 1, 2))
        for trading_day in days:
            # D-16: 적립 먼저 완료 후 step() 호출
            result = sa.step(today, price_today, price_60d_ago, price_20d_ago, portfolio)
            if result["action"] == "SELL":
                portfolio["shares"] *= (1 - StrategyA.SELL_PCT)
                sa.cash_held = result["cash_raised"]
            elif result["action"] in ("BUY", "FORCE_BUY"):
                portfolio["shares"] += sa.cash_held / price_today
                sa.cash_held = 0.0
    """

    LOOKBACK_SELL = 60   # 급등 판단 lookback (거래일)
    LOOKBACK_BUY = 20    # 급락 판단 lookback (거래일)
    RATIO_SELL = 1.20    # 급등 트리거 비율 (D-6)
    RATIO_BUY = 0.90     # 급락 트리거 비율
    SELL_PCT = 0.30      # 매도 비율 (30%)
    FORCE_REBUY_DAYS = 365  # 강제 재매수 일수 (D-7)
    GRACE_MONTHS = 12    # grace period (D-9)

    def __init__(self, period_start: date):
        self.state: str = STATE_NEUTRAL
        self.lock_until_year: int | None = None
        self.sell_date: date | None = None
        self.cash_held: float = 0.0
        self.grace_end: date = period_start + relativedelta(months=self.GRACE_MONTHS)

    def step(
        self,
        today: date,
        price_today: float,
        price_60d_ago: float | None,
        price_20d_ago: float | None,
        shares: float,
    ) -> dict:
        """한 거래일 전략 처리.

        Args:
            today: 현재 거래일
            price_today: 현지통화 종가 (D-6)
            price_60d_ago: 60거래일 전 현지통화 종가 (None이면 lookback 부족)
            price_20d_ago: 20거래일 전 현지통화 종가 (None이면 lookback 부족)
            shares: 현재 보유 주식 수 (적립 후 배당 적용 완료 상태)

        Returns:
            {"action": "SELL"|"BUY"|"FORCE_BUY"|None, "cash_raised": float}
        """
        result = {"action": None, "cash_raised": 0.0}

        # D-9: grace period — 첫 12개월 매도 트리거 무시
        if today < self.grace_end:
            return result

        if self.state == STATE_NEUTRAL:
            # lock_until_year: 해당 연도는 매도 트리거 무시 (D-8)
            if self.lock_until_year is not None and today.year <= self.lock_until_year:
                return result

            # 급등 트리거 (D-6: 현지통화, lookback 60거래일)
            if price_60d_ago is not None and price_60d_ago > 0:
                ratio = price_today / price_60d_ago
                if ratio >= self.RATIO_SELL:
                    cash_raised = shares * self.SELL_PCT * price_today
                    self.cash_held = cash_raised
                    self.state = STATE_SOLD
                    self.sell_date = today
                    result["action"] = "SELL"
                    result["cash_raised"] = cash_raised

        elif self.state == STATE_SOLD:
            # 강제 재매수 체크 (D-7: 매도일 + 365일)
            forced = self.sell_date is not None and (today - self.sell_date).days >= self.FORCE_REBUY_DAYS

            # 급락 트리거 (20거래일 전 대비 10% 하락)
            crash = (
                price_20d_ago is not None
                and price_20d_ago > 0
                and price_today / price_20d_ago <= self.RATIO_BUY
            )

            if forced or crash:
                action = "FORCE_BUY" if forced else "BUY"
                # D-8: lock_until_year = 재매수 시점 연도
                self.lock_until_year = today.year
                self.state = STATE_NEUTRAL
                self.sell_date = None
                result["action"] = action
                result["cash_raised"] = self.cash_held
                self.cash_held = 0.0

        return result

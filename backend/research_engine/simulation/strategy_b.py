"""전략 B — 70% 정기 + 30% 대기 (마스터플랜 §3.5).

매월 적립금 70% 즉시 매수 + 30% reserve pool 보관.
reserve: 20거래일 전 대비 10% 하락 시 전액 매수, 또는 연말 강제 매수.
"""

from __future__ import annotations

from datetime import date


class StrategyB:
    """70% 정기 + 30% 대기 전략.

    Usage:
        sb = StrategyB()
        for trading_day in days:
            # 월 첫 거래일
            if is_first_day_of_month(today):
                shares += sb.deposit(monthly_krw, price_today, fx_rate)
            # 매 거래일
            result = sb.step(today, price_today, price_20d_ago, trading_days_this_year, price)
            if result["action"] == "BUY":
                shares += result["shares_bought"]
    """

    REGULAR_PCT = 0.70   # 즉시 매수 비율
    RESERVE_PCT = 0.30   # reserve 비율
    RATIO_BUY = 0.90     # 급락 트리거 (20거래일 전 대비)

    def __init__(self) -> None:
        self.reserve_krw: float = 0.0

    def deposit(
        self,
        monthly_krw: int,
        price: float,
        fx_rate: float | None = None,
    ) -> float:
        """월 적립금 처리. 70% 즉시 매수 → shares 반환, 30% reserve 축적.

        Args:
            monthly_krw: 월 적립금 (KRW)
            price: 현지통화 종가
            fx_rate: USD/KRW (KRW 자산이면 None)

        Returns:
            즉시 매수로 획득한 shares 수
        """
        regular = monthly_krw * self.REGULAR_PCT
        reserved = monthly_krw * self.RESERVE_PCT
        self.reserve_krw += reserved

        if fx_rate is not None:
            return (regular / fx_rate) / price
        return regular / price

    def step(
        self,
        today: date,
        price_today: float,
        price_20d_ago: float | None,
        is_last_trading_day_of_year: bool,
        fx_rate: float | None = None,
    ) -> dict:
        """매 거래일 reserve 소진 조건 체크.

        Args:
            today: 현재 거래일
            price_today: 현지통화 종가
            price_20d_ago: 20거래일 전 현지통화 종가 (None이면 lookback 부족)
            is_last_trading_day_of_year: 연도 마지막 거래일 여부
            fx_rate: USD/KRW (KRW 자산이면 None)

        Returns:
            {"action": "BUY"|"FORCE_BUY"|None, "shares_bought": float}
        """
        result = {"action": None, "shares_bought": 0.0}

        if self.reserve_krw <= 0:
            return result

        crash = (
            price_20d_ago is not None
            and price_20d_ago > 0
            and price_today / price_20d_ago <= self.RATIO_BUY
        )
        forced = is_last_trading_day_of_year

        if crash or forced:
            action = "FORCE_BUY" if forced else "BUY"
            if fx_rate is not None:
                shares_bought = (self.reserve_krw / fx_rate) / price_today
            else:
                shares_bought = self.reserve_krw / price_today
            self.reserve_krw = 0.0
            result["action"] = action
            result["shares_bought"] = shares_bought

        return result

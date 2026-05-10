"""포트폴리오 적립식 (Tab C, 마스터플랜 §3.6).

기본 비중: 60% 주식/ETF + TLT 20% + BTC 20%.
매월 적립금: 목표 비중대로 즉시 분배.
연간 리밸런싱: 매년 마지막 거래일, 보유분 포함 실제 재조정.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PortfolioPreset:
    name: str
    weights: dict[str, float]  # {asset_code: 비중 (합 = 1.0)}


# §3.6 lock — 4개 preset (§10.5)
PRESETS: dict[str, PortfolioPreset] = {
    "QQQ_TLT_BTC": PortfolioPreset(
        "QQQ/TLT/BTC 60/20/20",
        {"QQQ": 0.60, "TLT": 0.20, "BTC": 0.20},
    ),
    "KS200_TLT_BTC": PortfolioPreset(
        "KS200/TLT/BTC 60/20/20",
        {"KS200": 0.60, "TLT": 0.20, "BTC": 0.20},
    ),
    "SEC_SKH_TLT_BTC": PortfolioPreset(
        "삼성전자+SK하이닉스/TLT/BTC 60/20/20",
        {"005930": 0.30, "000660": 0.30, "TLT": 0.20, "BTC": 0.20},
    ),
    "TECH_TLT_BTC": PortfolioPreset(
        "NVDA+GOOGL+TSLA/TLT/BTC 60/20/20",
        {"NVDA": 0.20, "GOOGL": 0.20, "TSLA": 0.20, "TLT": 0.20, "BTC": 0.20},
    ),
}


class Portfolio:
    """고정 비중 포트폴리오 + 연 1회 리밸런싱.

    Usage:
        port = Portfolio(PRESETS["QQQ_TLT_BTC"])
        for trading_day in days:
            if is_first_day_of_month:
                port.deposit(monthly_krw, prices_today, fx_rates_today)
            port.apply_dividends(annual_yields, prices_today, fx_rates_today)
            if is_last_trading_day_of_year:
                port.rebalance(prices_today, fx_rates_today)
            krw_value = port.total_krw_value(prices_today, fx_rates_today)
    """

    def __init__(self, preset: PortfolioPreset) -> None:
        self.preset = preset
        # {asset_code: fractional shares}
        self.holdings: dict[str, float] = {code: 0.0 for code in preset.weights}

    def _krw_value_of(
        self,
        code: str,
        shares: float,
        price: float,
        fx_rate: float | None,
    ) -> float:
        return shares * price * (fx_rate if fx_rate is not None else 1.0)

    def total_krw_value(
        self,
        prices: dict[str, float],
        fx_rates: dict[str, float | None],
    ) -> float:
        """포트폴리오 총 KRW 평가액."""
        return sum(
            self._krw_value_of(code, shares, prices[code], fx_rates.get(code))
            for code, shares in self.holdings.items()
            if code in prices
        )

    def deposit(
        self,
        monthly_krw: int,
        prices: dict[str, float],
        fx_rates: dict[str, float | None],
    ) -> None:
        """월 적립금을 목표 비중대로 즉시 분배."""
        for code, weight in self.preset.weights.items():
            if code not in prices:
                continue
            alloc_krw = monthly_krw * weight
            price = prices[code]
            fx = fx_rates.get(code)
            if fx is not None:
                self.holdings[code] += (alloc_krw / fx) / price
            else:
                self.holdings[code] += alloc_krw / price

    def apply_dividends(
        self,
        annual_yields: dict[str, float],
        prices: dict[str, float],
        fx_rates: dict[str, float | None],
    ) -> None:
        """매 거래일 각 자산 배당 재투자 (D-4)."""
        for code in self.holdings:
            yield_rate = annual_yields.get(code, 0.0)
            if yield_rate > 0:
                self.holdings[code] *= (1.0 + yield_rate / 252.0)

    def rebalance(
        self,
        prices: dict[str, float],
        fx_rates: dict[str, float | None],
    ) -> dict[str, float]:
        """연 마지막 거래일 비중 재조정.

        현재 총 KRW 가치를 목표 비중대로 재배분.

        Returns:
            리밸런싱 후 실제 비중 {asset_code: 실제 비중}
        """
        total = self.total_krw_value(prices, fx_rates)
        if total <= 0:
            return {}

        for code, weight in self.preset.weights.items():
            if code not in prices:
                continue
            target_krw = total * weight
            price = prices[code]
            fx = fx_rates.get(code)
            if fx is not None:
                self.holdings[code] = (target_krw / fx) / price
            else:
                self.holdings[code] = target_krw / price

        # 실제 비중 반환
        actual_weights: dict[str, float] = {}
        for code, shares in self.holdings.items():
            if code not in prices:
                continue
            val = self._krw_value_of(code, shares, prices[code], fx_rates.get(code))
            actual_weights[code] = val / total if total > 0 else 0.0
        return actual_weights

    def current_weights(
        self,
        prices: dict[str, float],
        fx_rates: dict[str, float | None],
    ) -> dict[str, float]:
        """현재 실제 비중."""
        total = self.total_krw_value(prices, fx_rates)
        if total <= 0:
            return {code: 0.0 for code in self.holdings}
        result = {}
        for code, shares in self.holdings.items():
            if code not in prices:
                continue
            val = self._krw_value_of(code, shares, prices[code], fx_rates.get(code))
            result[code] = val / total
        return result

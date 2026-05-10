"""캘린더 연도 기준 MDD 계산 (마스터플랜 §3.7, Q5-15).

연도별 적립식 누적 자산가치 곡선에서 (고점→저점) drawdown의 최악값을 반환.
"""

import numpy as np
import pandas as pd


def mdd_by_calendar_year(series: pd.Series) -> dict[int, float]:
    """연도별 MDD 계산.

    Args:
        series: DatetimeIndex pd.Series, values = KRW 평가액 (양수)

    Returns:
        {연도: MDD(음수 or 0.0)} dict.
        연도 내 최대 고점 대비 저점 낙폭 비율. 상승만 한 경우 0.0.
    """
    result: dict[int, float] = {}

    for year, group in series.groupby(series.index.year):
        prices = group.values.astype(float)
        if len(prices) == 0:
            continue
        running_max = np.maximum.accumulate(prices)
        safe_max = np.where(running_max > 0, running_max, np.nan)
        drawdown = (prices - running_max) / safe_max
        result[int(year)] = float(np.nanmin(drawdown))

    return result

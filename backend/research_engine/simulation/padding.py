"""History padding 알고리즘 (마스터플랜 §2.6, D-2).

10년 시뮬레이션 요구 시 실제 history가 부족한 자산(JEPI 등)에 적용.
- 가격 직접 복제 X — 일별 수익률(returns)을 cyclic 복제 후 prepend
- 시작 가격은 actual 첫날 가격에서 reverse-cumprod로 역산
- 변동성·추세 패턴 보존
"""

import numpy as np


def pad_returns(actual_returns: np.ndarray, target_days: int) -> np.ndarray:
    """actual_returns를 cyclic 복제해 target_days 길이로 맞춘다.

    actual_returns가 target_days 이상이면 그대로 반환 (no padding).
    부족한 앞부분(padding)을 actual을 반복해 채운다.

    Args:
        actual_returns: 실제 일별 수익률 배열 (float, length N)
        target_days: 목표 길이

    Returns:
        length == target_days인 수익률 배열. 앞부분이 padding, 뒷부분이 actual.
    """
    n = len(actual_returns)
    if n >= target_days:
        return actual_returns[:target_days]

    needed = target_days - n
    padding: list[float] = []
    while len(padding) < needed:
        take = min(needed - len(padding), n)
        padding.extend(actual_returns[:take].tolist())

    return np.concatenate([np.array(padding), actual_returns])


def prices_with_padding(
    actual_first_price: float,
    padded_returns: np.ndarray,
    padding_len: int,
) -> np.ndarray:
    """padded_returns로부터 가격 시계열을 구성한다.

    prices[padding_len] == actual_first_price (가격 연속성 기준점).

    actual 구간 (indices padding_len .. end):
        prices[padding_len] = actual_first_price
        prices[padding_len + i] = actual_first_price * prod(1 + r[j], j=0..i-1)

    padding 구간 (indices 0 .. padding_len-1): reverse-cumprod 역산
        prices[padding_len - 1] = actual_first_price / (1 + p[-1])
        prices[padding_len - k] = actual_first_price / prod(1 + p[-1..-k])

    Args:
        actual_first_price: actual 데이터 첫날 실제 가격
        padded_returns: pad_returns() 결과 길이 T (padding M개 + actual N개)
        padding_len: 앞쪽 padding 길이 M

    Returns:
        length == len(padded_returns)인 가격 시계열.
        prices[padding_len] == actual_first_price 보장.
    """
    total = len(padded_returns)
    prices = np.empty(total)

    # actual 구간
    # prices[M]   = P0
    # prices[M+k] = P0 * prod(1 + actual_r[0..k-2])  for k ≥ 1
    prices[padding_len] = actual_first_price
    if padding_len < total - 1:
        actual_r = padded_returns[padding_len:]  # length N (actual returns 전체)
        cumprod = np.cumprod(1.0 + actual_r)     # length N
        prices[padding_len + 1 :] = actual_first_price * cumprod[:-1]

    # padding 구간: actual_first_price에서 역산
    if padding_len > 0:
        pad_r = padded_returns[:padding_len]  # shape (M,)
        # prices[padding_len - 1] = actual_first_price / (1 + pad_r[M-1])
        # prices[padding_len - 2] = prices[padding_len-1] / (1 + pad_r[M-2])
        # → prices[padding_len - k] = actual_first_price / cumprod(1 + pad_r[M-1..M-k])
        rev_factors = np.cumprod(1.0 + pad_r[::-1])  # shape (M,)
        prices[:padding_len] = (actual_first_price / rev_factors)[::-1]

    return prices

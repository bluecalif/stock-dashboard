"""WBI (Warren Buffett Index) synthetic 생성기 (마스터플랜 §2.5, D-5).

워런 버핏의 연 20% 복리 수익률을 가정한 가상 벤치마크.

GBM(Geometric Brownian Motion)으로 합성 벤치마크 생성:
- 통화: KRW (환율 영향 없음)
- 연 수익률: 20% (drift 보정으로 정확히 보존)
- 일별 변동성: σ = 1%/일
- 시드: 42 (결정적 reproducibility — np.random.default_rng 사용)
"""

import numpy as np


def generate_wbi(
    n_days: int,
    seed: int = 42,
    annual_return: float = 0.20,
    sigma: float = 0.01,
    initial_price: float = 100.0,
) -> np.ndarray:
    """GBM 기반 WBI synthetic 가격 시계열 생성.

    Args:
        n_days: 생성할 거래일 수 (10년 ≈ 2520)
        seed: numpy 시드 (42 고정 — D-5)
        annual_return: 목표 연 수익률 (0.20 = 20%)
        sigma: 일별 변동성 (0.01 = 1%/일)
        initial_price: 기준 가격 (KRW, 임의값)

    Returns:
        shape (n_days,) 가격 배열. prices[0] = initial_price * (1 + r[0]).
    """
    rng = np.random.default_rng(seed)
    # 순수 노이즈 (zero-mean)
    noise = rng.normal(loc=0.0, scale=sigma, size=n_days)

    # 목표 log-return: 정확히 연 20% CAGR 달성
    target_log = n_days * (np.log(1.0 + annual_return) / 252.0)
    current_log = np.sum(np.log1p(noise))
    drift_per_day = (target_log - current_log) / n_days

    returns = noise + drift_per_day
    prices = initial_price * np.cumprod(1.0 + returns)
    return prices

"""wbi.py unit tests — 마스터플랜 §2.5 / §9.1, D-5.

WBI (Warren Buffett Index) synthetic GBM 검증.
단일 경로(seed 42)는 GBM 분산으로 20%와 편차 정상.
→ 이론적 drift 파라미터 + 100-seed 앙상블 평균으로 검증.
"""

import numpy as np

from research_engine.simulation.wbi import generate_wbi

FIXTURE_PATH = "research_engine/simulation/fixtures/wbi_seed42_10y.npz"
N_DAYS = 2520  # 10년


def test_reproducibility():
    """시드 42 두 번 호출 결과 완전 동일 (D-5 reproducibility)."""
    a = generate_wbi(N_DAYS, seed=42)
    b = generate_wbi(N_DAYS, seed=42)
    assert np.array_equal(a, b), "시드 42 결과가 재현되지 않음"


def test_length():
    """출력 길이 == n_days."""
    prices = generate_wbi(N_DAYS, seed=42)
    assert len(prices) == N_DAYS


def test_all_positive():
    """모든 가격이 양수."""
    prices = generate_wbi(N_DAYS, seed=42)
    assert (prices > 0).all()


def test_daily_sigma():
    """일별 수익률 σ ≈ 1%/일 (±0.2% 허용)."""
    prices = generate_wbi(N_DAYS, seed=42)
    daily_returns = np.diff(prices) / prices[:-1]
    sigma = daily_returns.std()
    assert abs(sigma - 0.01) < 0.002, f"sigma={sigma:.4f}, expected 0.01 ±0.002"


def test_log_drift():
    """log-drift = mu_adj = mu - 0.5*sigma^2 (이론값과 ±0.001 이내).

    GBM에서 E[log(P_t/P_0)] = n * mu_adj.
    단일 경로의 arithmetic annual return은 분산으로 20%와 크게 편차 가능.
    이론적 drift 파라미터 직접 검증이 더 정확.
    """
    prices = generate_wbi(N_DAYS, seed=42)
    log_returns = np.log(prices[1:] / prices[:-1])
    mean_log_r = log_returns.mean()

    mu = (1.20) ** (1 / 252) - 1
    sigma = 0.01
    mu_adj_theory = mu - 0.5 * sigma ** 2

    assert abs(mean_log_r - mu_adj_theory) < 0.001, (
        f"mean log return={mean_log_r:.6f}, theory={mu_adj_theory:.6f}"
    )


def test_ensemble_annual_return():
    """100-seed 앙상블 평균 연환산 수익률 ≈ 20% (±3% 허용, CLT 기반).

    단일 경로(seed 42)의 실현값이 아닌
    기댓값(E[연환산])이 20%임을 확인.
    """
    annuals = []
    for seed in range(100):
        prices = generate_wbi(N_DAYS, seed=seed)
        ann = (prices[-1] / 100.0) ** (252 / N_DAYS) - 1
        annuals.append(ann)

    mean_annual = np.mean(annuals)
    assert abs(mean_annual - 0.20) < 0.03, (
        f"100-seed mean annual={mean_annual:.2%}, expected 20% ±3%"
    )


def test_different_seeds_differ():
    """다른 시드는 다른 경로를 생성."""
    p42 = generate_wbi(N_DAYS, seed=42)
    p43 = generate_wbi(N_DAYS, seed=43)
    assert not np.array_equal(p42, p43)


def test_fixture_loadable():
    """사전 계산된 fixture .npz가 정상 로드 가능."""
    data = np.load(FIXTURE_PATH)
    assert "prices" in data, "prices 키 없음"
    assert len(data["prices"]) == N_DAYS, f"fixture 길이={len(data['prices'])}, expected {N_DAYS}"
    np.testing.assert_array_equal(data["prices"], generate_wbi(N_DAYS, seed=42))

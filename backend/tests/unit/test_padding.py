"""padding.py unit tests — 마스터플랜 §2.6 / §9.1."""

import numpy as np
import pytest

from research_engine.simulation.padding import pad_returns, prices_with_padding

FIXTURE_PATH = "research_engine/simulation/fixtures/jepi_5y_returns.npy"
TARGET = 2520  # 10년 거래일


@pytest.fixture(scope="module")
def jepi_returns():
    return np.load(FIXTURE_PATH)


# ── pad_returns ────────────────────────────────────────────────────────────────


def test_no_padding_when_sufficient():
    """actual이 target_days 이상이면 앞부분 슬라이스."""
    r = np.random.default_rng(0).normal(0, 0.01, TARGET + 100)
    result = pad_returns(r, TARGET)
    assert len(result) == TARGET
    np.testing.assert_array_equal(result, r[:TARGET])


def test_jepi_5y_to_10y_length(jepi_returns):
    """JEPI 5년(1259 returns) → 10년(2520) padding 후 길이 정확."""
    result = pad_returns(jepi_returns, TARGET)
    assert len(result) == TARGET


def test_mean_return_preserved(jepi_returns):
    """padding 후 일별 수익률 평균이 actual과 ±0.1% 이내."""
    padded = pad_returns(jepi_returns, TARGET)
    actual_mean = jepi_returns.mean()
    padded_mean = padded.mean()
    diff_pct = abs(padded_mean - actual_mean)
    assert diff_pct < 0.001, f"mean diff={diff_pct:.6f} > 0.001"


def test_partial_cycle():
    """cyclic 부분 절단 — target이 actual의 비정수배여도 정확히 target_days."""
    actual = np.ones(1000) * 0.001
    result = pad_returns(actual, 2520)
    assert len(result) == 2520
    assert result[:1520].tolist() == [0.001] * 1520  # padding 부분


def test_exact_fit():
    """actual 길이 == target_days → 그대로 반환."""
    actual = np.ones(TARGET) * 0.001
    result = pad_returns(actual, TARGET)
    assert len(result) == TARGET
    np.testing.assert_array_equal(result, actual)


# ── prices_with_padding ────────────────────────────────────────────────────────


def test_price_continuity_at_junction(jepi_returns):
    """prices[padding_len] == actual_first_price (가격 점프 없음)."""
    padded_returns = pad_returns(jepi_returns, TARGET)
    padding_len = TARGET - len(jepi_returns)
    actual_first_price = 50.0  # 임의 기준가

    prices = prices_with_padding(actual_first_price, padded_returns, padding_len)

    assert len(prices) == TARGET
    np.testing.assert_allclose(
        prices[padding_len], actual_first_price, rtol=1e-9,
        err_msg="가격 연속성 실패: prices[padding_len] != actual_first_price"
    )


def test_actual_prices_match_cumprod(jepi_returns):
    """actual 구간 prices가 cumprod 기반 가격과 일치."""
    padded_returns = pad_returns(jepi_returns, TARGET)
    padding_len = TARGET - len(jepi_returns)
    p0 = 100.0

    prices = prices_with_padding(p0, padded_returns, padding_len)

    # actual 구간: prices[padding_len+1] = p0 * (1 + actual_returns[0])
    actual_r = padded_returns[padding_len:]
    expected = p0 * np.cumprod(1.0 + actual_r)
    np.testing.assert_allclose(
        prices[padding_len + 1:], expected[:-1] if len(expected) > 1 else np.array([]),
        rtol=1e-9
    )


def test_padding_prices_positive():
    """padding 구간 가격이 모두 양수."""
    actual = np.array([0.001] * 500)
    padded = pad_returns(actual, 1000)
    prices = prices_with_padding(50.0, padded, 500)
    assert (prices > 0).all(), "음수 가격 존재"

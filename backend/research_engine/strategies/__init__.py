"""Strategy engine for signal generation."""

from research_engine.strategies.base import Strategy
from research_engine.strategies.mean_reversion import MeanReversionStrategy
from research_engine.strategies.momentum import MomentumStrategy
from research_engine.strategies.trend import TrendStrategy

STRATEGY_REGISTRY: dict[str, type[Strategy]] = {
    "momentum": MomentumStrategy,
    "trend": TrendStrategy,
    "mean_reversion": MeanReversionStrategy,
}


def get_strategy(name: str, **kwargs) -> Strategy:
    """Get strategy instance by name.

    Args:
        name: Strategy name (momentum, trend, mean_reversion).
        **kwargs: Strategy-specific parameters.

    Returns:
        Strategy instance.

    Raises:
        KeyError: If strategy name is not found.
    """
    if name not in STRATEGY_REGISTRY:
        raise KeyError(
            f"Unknown strategy: {name}. "
            f"Available: {list(STRATEGY_REGISTRY.keys())}"
        )
    return STRATEGY_REGISTRY[name](**kwargs)

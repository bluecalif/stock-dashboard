# Silver gen simulation engine (마스터플랜 §3)
from research_engine.simulation.padding import pad_returns, prices_with_padding
from research_engine.simulation.wbi import generate_wbi
from research_engine.simulation.fx import load_fx_series
from research_engine.simulation.mdd import mdd_by_calendar_year

__all__ = [
    # Phase 1
    "pad_returns",
    "prices_with_padding",
    "generate_wbi",
    # Phase 2 utility
    "load_fx_series",
    "mdd_by_calendar_year",
    # Phase 2 엔진 (구현 예정)
    # "replay",        # replay.py
    # "StrategyA",     # strategy_a.py
    # "StrategyB",     # strategy_b.py
    # "Portfolio",     # portfolio.py
]

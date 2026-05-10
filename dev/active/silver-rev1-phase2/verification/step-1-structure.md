# P2-1 Verification — simulation/ 디렉터리 구조 + __init__.py

> Date: 2026-05-10
> Status: PASSED

---

## G1.1 — 디렉터리 구조 확인

**명령**: `ls backend/research_engine/simulation/`

**Evidence**:

```
backend\research_engine\simulation\__init__.py
backend\research_engine\simulation\padding.py
backend\research_engine\simulation\wbi.py
backend\research_engine\simulation\fx.py          ← P2-2 신규
backend\research_engine\simulation\mdd.py         ← P2-2 신규
backend\research_engine\simulation\fixtures\
    jepi_5y_returns.npy
    wbi_seed42_10y.npz
```

**결과**: ✅ PASS — `__init__.py`, `padding.py`, `wbi.py`, `fixtures/` 모두 존재. Phase 2 신규 `fx.py`, `mdd.py` 추가 확인.

---

## G1.2 — `__init__.py` exports 확인

**명령**: `cat backend/research_engine/simulation/__init__.py`

**Evidence**:

```python
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
```

**결과**: ✅ PASS — Phase 1 exports (`pad_returns`, `generate_wbi`) 확인. Phase 2 utility (`load_fx_series`, `mdd_by_calendar_year`) exports 추가. 미구현 모듈은 주석으로 설계 명확화.

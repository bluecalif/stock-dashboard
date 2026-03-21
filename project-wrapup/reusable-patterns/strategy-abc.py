"""
## 용도
전략 엔진 Abstract Base Class.
_raw_signals()만 구현하면 signal 생성 + action labeling + 메타데이터 자동 처리.

## 사용법
1. Strategy ABC 상속 → _raw_signals() 구현
2. generate_signals(factors_df, asset_id) 호출
3. SignalResult.signals DataFrame에 date, signal, score, action, meta_json 포함

## 출처
stock-dashboard/backend/research_engine/strategies/base.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

import pandas as pd

DEFAULT_COMMISSION_PCT = 0.001


@dataclass
class SignalResult:
    asset_id: str
    strategy_id: str
    signals: pd.DataFrame  # columns: date, signal, score, action, meta_json
    n_entry: int = 0
    n_exit: int = 0
    n_hold: int = 0


class Strategy(ABC):
    strategy_id: str  # 서브클래스에서 설정

    def __init__(self, commission_pct: float = DEFAULT_COMMISSION_PCT):
        self.commission_pct = commission_pct

    @abstractmethod
    def _raw_signals(self, factors_df: pd.DataFrame) -> pd.DataFrame:
        """Returns DataFrame with: signal (int), score (float), meta (dict)"""
        ...

    def generate_signals(self, factors_df: pd.DataFrame, asset_id: str) -> SignalResult:
        raw = self._raw_signals(factors_df)

        signals = raw[["signal"]].copy()
        signals["score"] = raw.get("score")
        meta_col = raw.get("meta")

        # Action labeling: prev → curr 변화 기반
        prev = signals["signal"].shift(1).fillna(0).astype(int)
        curr = signals["signal"]

        actions = pd.Series("hold", index=signals.index)
        actions[(prev == 0) & (curr != 0)] = "entry"
        actions[(prev != 0) & (curr == 0)] = "exit"
        actions[(prev != 0) & (curr != 0) & (prev != curr)] = "entry"

        signals["action"] = actions
        signals["meta_json"] = meta_col.tolist() if meta_col is not None else [None] * len(signals)
        signals = signals.reset_index()

        return SignalResult(
            asset_id=asset_id,
            strategy_id=self.strategy_id,
            signals=signals,
            n_entry=int((signals["action"] == "entry").sum()),
            n_exit=int((signals["action"] == "exit").sum()),
            n_hold=int((signals["action"] == "hold").sum()),
        )


# --- 사용 예시 ---
# class MomentumStrategy(Strategy):
#     strategy_id = "momentum"
#
#     def _raw_signals(self, factors_df):
#         signal = (factors_df["ret_63d"] > 0.05).astype(int)
#         return pd.DataFrame({"signal": signal, "score": factors_df["ret_63d"]})

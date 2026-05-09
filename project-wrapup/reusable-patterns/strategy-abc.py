"""
## 용도
전략 엔진 Abstract Base Class. _raw_signals()만 구현하면
signal→action labeling, 메타데이터 직렬화, 결과 카운트를 자동 처리.
수정 필요 (전략 로직/팩터명 교체).

## 언제 쓰는가
시계열 데이터에 대해 여러 전략(모멘텀, 추세, 평균회귀 등)을 통일된 인터페이스로 관리할 때.
백테스트 엔진에 다양한 전략을 플러그인처럼 추가하고 싶을 때.

## 전제조건
- 팩터 DataFrame (factors_df) — 날짜 인덱스, 팩터 컬럼 포함
- 팩터 DF에 원시 OHLCV 컬럼도 포함 필요 시 별도 합침 (T-008)

## 의존성
- pandas: DataFrame 처리
- abc: ABC, abstractmethod

## 통합 포인트
- research_engine/strategies/ 디렉토리에 base.py로 배치
- 개별 전략(momentum.py, trend.py 등)이 Strategy 상속
- STRATEGY_REGISTRY dict로 전략 등록 → 백테스트 엔진에서 이름으로 조회
- signal_store.py에서 SignalResult.signals를 signal_daily 테이블에 저장

## 주의사항
- _raw_signals()는 반드시 signal(int), score(float) 컬럼 반환
- factors_df에 필요한 팩터가 없으면 KeyError — 팩터 의존성을 전략별로 문서화
- NaN 값이 포함될 수 있음 — DB 적재 전 방어 필요 (T-006)

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

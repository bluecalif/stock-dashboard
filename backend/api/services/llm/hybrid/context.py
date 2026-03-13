"""Page context — current page info passed from frontend."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PageContext:
    """Current page context sent from frontend with each chat message."""

    page_id: str  # "correlation" | "indicators" | "strategy" | "prices" | "home"
    asset_ids: list[str] = field(default_factory=list)
    params: dict = field(default_factory=dict)
    # params examples:
    #   correlation: {"window": 60, "selected_pair": ["KS200", "005930"]}
    #   indicators: {"selected_factor": "rsi_14", "asset_id": "KS200"}
    #   strategy: {"strategy_ids": ["momentum", "trend"], "period": "1Y"}

    @classmethod
    def from_dict(cls, data: dict | None) -> PageContext:
        if not data:
            return cls(page_id="home")
        return cls(
            page_id=data.get("page_id", "home"),
            asset_ids=data.get("asset_ids", []),
            params=data.get("params", {}),
        )

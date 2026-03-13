"""UI actions — commands sent to frontend via SSE."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class UIAction:
    """An action to send to frontend via SSE ui_action event."""

    action: str  # "navigate" | "update_chart" | "set_filter" | "highlight_pair"
    payload: dict

    def to_dict(self) -> dict:
        return {"action": self.action, "payload": self.payload}


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

def navigate(path: str) -> UIAction:
    """Navigate to a page."""
    return UIAction(action="navigate", payload={"path": path})


def update_chart(chart_id: str, **kwargs) -> UIAction:
    """Update a chart with new parameters."""
    return UIAction(action="update_chart", payload={"chart_id": chart_id, **kwargs})


def set_filter(key: str, value: str | list) -> UIAction:
    """Set a filter/selection on the current page."""
    return UIAction(action="set_filter", payload={"key": key, "value": value})


def highlight_pair(asset_a: str, asset_b: str) -> UIAction:
    """Highlight a specific asset pair on correlation page."""
    return UIAction(
        action="highlight_pair",
        payload={"asset_a": asset_a, "asset_b": asset_b},
    )

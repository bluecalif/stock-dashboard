"""DataFetcher — programmatic tool invocation based on ClassificationResult.

Maps tool names to actual LangChain tool functions and invokes them
with parameters from the classification result.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from api.repositories import asset_repo
from api.services.llm.tools import (
    analyze_correlation_tool,
    analyze_indicators,
    backtest_strategy,
    get_correlation,
    get_factors,
    get_prices,
    get_signals,
    get_spread,
    list_backtests,
)
from db.session import SessionLocal

from .schemas import ClassificationResult

logger = logging.getLogger(__name__)

# Tool name → LangChain tool function
_TOOL_MAP = {
    "get_prices": get_prices,
    "get_factors": get_factors,
    "get_correlation": get_correlation,
    "get_signals": get_signals,
    "list_backtests": list_backtests,
    "analyze_correlation_tool": analyze_correlation_tool,
    "get_spread": get_spread,
    "analyze_indicators": analyze_indicators,
    "backtest_strategy": backtest_strategy,
}


async def fetch_data(classification: ClassificationResult) -> dict[str, Any]:
    """Invoke required tools and return aggregated results.

    Each tool is called with parameters from the classification.
    Individual tool failures are logged and skipped (partial results).
    Always includes name_map for asset display names.
    """
    results: dict[str, Any] = {}

    for tool_name in classification.required_tools:
        tool_fn = _TOOL_MAP.get(tool_name)
        if tool_fn is None:
            logger.warning("Unknown tool: %s — skipping", tool_name)
            continue

        try:
            args = _build_tool_args(tool_name, classification)
            raw = tool_fn.invoke(args)
            # Tools return JSON strings — parse them
            results[tool_name] = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            logger.exception("Tool %s failed — skipping", tool_name)
            results[tool_name] = {"error": f"{tool_name} 호출 실패"}

    # Always include name_map
    results["name_map"] = _get_name_map(classification.asset_ids)

    return results


def _build_tool_args(
    tool_name: str,
    classification: ClassificationResult,
) -> dict[str, Any]:
    """Build tool-specific arguments from classification result."""
    params = classification.params
    asset_ids = classification.asset_ids

    # Default asset_id: first in list or KS200
    default_asset = asset_ids[0] if asset_ids else "KS200"
    days = params.get("days", 60)

    match tool_name:
        case "get_prices":
            return {"asset_id": default_asset, "days": params.get("days", 30)}

        case "get_factors":
            return {
                "asset_id": default_asset,
                "factor_name": params.get("factor_name"),
                "days": params.get("days", 30),
            }

        case "get_correlation":
            return {"asset_ids": asset_ids or None, "days": days}

        case "get_signals":
            return {
                "asset_id": default_asset,
                "strategy_id": params.get("strategy_id"),
                "days": params.get("days", 30),
            }

        case "list_backtests":
            return {
                "strategy_id": params.get("strategy_name"),
                "asset_id": default_asset if asset_ids else None,
            }

        case "analyze_correlation_tool":
            return {
                "asset_ids": asset_ids or None,
                "days": days,
                "threshold": params.get("threshold", 0.7),
                "target_id": params.get("target_id", default_asset),
            }

        case "get_spread":
            a = asset_ids[0] if len(asset_ids) >= 1 else "KS200"
            b = asset_ids[1] if len(asset_ids) >= 2 else "005930"
            return {"asset_a": a, "asset_b": b, "days": days}

        case "analyze_indicators":
            return {
                "asset_id": default_asset,
                "forward_days": params.get("forward_days", 5),
            }

        case "backtest_strategy":
            return {
                "asset_id": default_asset,
                "strategy_name": params.get("strategy_name", "momentum"),
                "period": params.get("period", "2Y"),
            }

        case _:
            return {}


def _get_name_map(asset_ids: list[str]) -> dict[str, str]:
    """Get asset_id → display_name mapping for all active assets."""
    db = SessionLocal()
    try:
        assets = asset_repo.get_all(db, is_active=True)
        return {a.asset_id: a.name for a in assets}
    except Exception:
        logger.exception("Failed to get name_map")
        return {}
    finally:
        db.close()

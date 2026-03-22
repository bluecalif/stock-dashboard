"""DataFetcher — programmatic tool invocation based on ClassificationResult.

Maps tool names to actual LangChain tool functions and invokes them
with parameters from the classification result.
"""

from __future__ import annotations

import asyncio
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
from .tool_cache import get_cached, set_cached

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
    """Invoke required tools in parallel and return aggregated results.

    Each tool is called with parameters from the classification.
    Tools run concurrently via run_in_executor (each tool creates its own DB session).
    Individual tool failures are logged and skipped (partial results).
    Always includes name_map for asset display names.
    """
    loop = asyncio.get_event_loop()

    async def _invoke(tool_name: str) -> tuple[str, Any]:
        tool_fn = _TOOL_MAP.get(tool_name)
        if tool_fn is None:
            logger.warning("Unknown tool: %s — skipping", tool_name)
            return tool_name, None

        args = _build_tool_args(tool_name, classification)

        # 캐시 확인
        cached = get_cached(tool_name, args)
        if cached is not None:
            logger.info("Tool %s cache HIT", tool_name)
            return tool_name, cached

        logger.info(
            "Invoking tool %s with args: %s",
            tool_name,
            json.dumps(args, ensure_ascii=False, default=str),
        )
        raw = await loop.run_in_executor(None, tool_fn.invoke, args)
        parsed = json.loads(raw) if isinstance(raw, str) else raw
        logger.info("Tool %s succeeded: %d chars", tool_name, len(str(raw)))
        if isinstance(parsed, dict) and "indicator_accuracy" in parsed:
            logger.info(
                "indicator_accuracy found in %s: %d entries",
                tool_name,
                len(parsed["indicator_accuracy"]),
            )

        # 캐시 저장
        set_cached(tool_name, args, parsed)
        return tool_name, parsed

    results: dict[str, Any] = {}
    tasks = [_invoke(t) for t in classification.required_tools]
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)

    for i, outcome in enumerate(outcomes):
        tool_name = classification.required_tools[i]
        if isinstance(outcome, Exception):
            logger.exception(
                "Tool %s failed — %s: %s",
                tool_name,
                type(outcome).__name__,
                outcome,
            )
            err = f"{type(outcome).__name__}: {outcome}"
            results[tool_name] = {"error": f"{tool_name} 호출 실패: {err}"}
        else:
            name, parsed = outcome
            if parsed is not None:
                results[name] = parsed

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
            # asset_ids가 2개 미만이면 None → 전체 활성 자산 사용
            corr_ids = asset_ids if len(asset_ids) >= 2 else None
            return {"asset_ids": corr_ids, "days": days}

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
            # asset_ids가 2개 미만이면 None → 전체 활성 자산 사용
            corr_ids = asset_ids if len(asset_ids) >= 2 else None
            return {
                "asset_ids": corr_ids,
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

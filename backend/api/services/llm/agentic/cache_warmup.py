"""Cache warmup — 서버 시작 시 주요 tool 결과를 백그라운드로 프리페치.

Cold 12s 문제를 우회: 미리 캐시에 넣어두면 첫 요청부터 warm (1.3s).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time

from api.services.llm.tools import (
    analyze_indicators,
    get_correlation,
    get_factors,
    get_prices,
    get_signals,
)

from .tool_cache import set_cached

logger = logging.getLogger(__name__)

# 7개 주요 자산
_ASSETS = ["KS200", "005930", "000660", "SOXL", "BTC/KRW", "GC=F", "SI=F"]

# 프리페치 대상: (tool_fn, args_builder)
# Classifier가 가장 자주 요청하는 tool + 기본 파라미터 조합
_WARMUP_SPECS: list[tuple[str, object, dict]] = []


def _build_warmup_specs() -> list[tuple[str, object, dict]]:
    """프리페치할 (tool_name, tool_fn, args) 목록 생성."""
    specs: list[tuple[str, object, dict]] = []

    for asset in _ASSETS:
        # get_prices — 기본 30일
        specs.append(("get_prices", get_prices, {"asset_id": asset, "days": 30}))
        # get_factors — 기본 30일, factor_name=None
        specs.append((
            "get_factors",
            get_factors,
            {"asset_id": asset, "factor_name": None, "days": 30},
        ))
        # get_signals — 기본 30일
        specs.append((
            "get_signals",
            get_signals,
            {"asset_id": asset, "strategy_id": None, "days": 30},
        ))
        # analyze_indicators — 기본 forward_days=5
        specs.append((
            "analyze_indicators",
            analyze_indicators,
            {"asset_id": asset, "forward_days": 5},
        ))

    # get_correlation — 전체 자산, 60일
    specs.append((
        "get_correlation",
        get_correlation,
        {"asset_ids": None, "days": 60},
    ))

    return specs


async def warmup_cache() -> None:
    """주요 tool 결과를 병렬로 프리페치하여 캐시에 저장.

    서버 시작 시 백그라운드로 실행. 개별 실패는 무시 (partial warmup).
    """
    specs = _build_warmup_specs()
    logger.info("Cache warmup 시작: %d개 tool 호출 예정", len(specs))
    start = time.perf_counter()

    loop = asyncio.get_event_loop()

    async def _invoke_and_cache(
        tool_name: str, tool_fn: object, args: dict,
    ) -> bool:
        try:
            raw = await loop.run_in_executor(None, tool_fn.invoke, args)
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            set_cached(tool_name, args, parsed)
            return True
        except Exception:
            logger.warning(
                "Warmup 실패: %s(%s)", tool_name, args.get("asset_id", ""),
                exc_info=True,
            )
            return False

    results = await asyncio.gather(
        *[_invoke_and_cache(name, fn, args) for name, fn, args in specs],
    )

    ok = sum(1 for r in results if r)
    elapsed = time.perf_counter() - start
    logger.info(
        "Cache warmup 완료: %d/%d 성공, %.1fs 소요",
        ok, len(specs), elapsed,
    )

"""In-memory tool result cache — 일봉 데이터용 당일 캐시.

키: (tool_name, args_hash, date.today())
자정에 date가 바뀌면 자동 무효화.
최대 100 엔트리, 초과 시 가장 오래된 항목 삭제.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import OrderedDict
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)

_MAX_ENTRIES = 100
_cache: OrderedDict[str, Any] = OrderedDict()


def _make_key(tool_name: str, args: dict) -> str:
    """캐시 키 생성 (tool + args + 오늘 날짜)."""
    key_data = json.dumps(
        {"tool": tool_name, "args": args, "d": date.today().isoformat()},
        sort_keys=True,
        default=str,
    )
    return hashlib.md5(key_data.encode()).hexdigest()


def get_cached(tool_name: str, args: dict) -> Any | None:
    """캐시에서 결과 조회. 없으면 None."""
    key = _make_key(tool_name, args)
    result = _cache.get(key)
    if result is not None:
        _cache.move_to_end(key)
        logger.debug("Cache HIT: %s", tool_name)
    return result


def set_cached(tool_name: str, args: dict, result: Any) -> None:
    """캐시에 결과 저장."""
    key = _make_key(tool_name, args)
    _cache[key] = result
    _cache.move_to_end(key)
    while len(_cache) > _MAX_ENTRIES:
        _cache.popitem(last=False)

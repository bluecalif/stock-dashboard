"""공통 스키마: Pagination, ErrorResponse."""

from __future__ import annotations

from fastapi import Query
from pydantic import BaseModel


class PaginationParams:
    """Query-parameter 의존성으로 사용."""

    def __init__(
        self,
        limit: int = Query(default=500, ge=1, le=5000, description="조회 건수"),
        offset: int = Query(default=0, ge=0, description="시작 오프셋"),
    ) -> None:
        self.limit = limit
        self.offset = offset


class ErrorResponse(BaseModel):
    detail: str
    error_code: str

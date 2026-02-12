"""자산 스키마."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    asset_id: str
    name: str
    category: str
    is_active: bool

"""Seed asset_master with 7 assets. Idempotent — safe to re-run."""

import sys
from pathlib import Path

# Ensure backend/ is on sys.path when running as script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from config.settings import settings
from db.models import AssetMaster

ASSETS = [
    {
        "asset_id": "KS200",
        "name": "KOSPI200",
        "category": "index",
        "source_priority": ["fdr"],
        "is_active": True,
    },
    {
        "asset_id": "005930",
        "name": "삼성전자",
        "category": "stock",
        "source_priority": ["fdr", "hantoo"],
        "is_active": True,
    },
    {
        "asset_id": "000660",
        "name": "SK하이닉스",
        "category": "stock",
        "source_priority": ["fdr", "hantoo"],
        "is_active": True,
    },
    {
        "asset_id": "SOXL",
        "name": "SOXL ETF",
        "category": "etf",
        "source_priority": ["fdr"],
        "is_active": True,
    },
    {
        "asset_id": "BTC",
        "name": "Bitcoin",
        "category": "crypto",
        "source_priority": ["fdr"],
        "is_active": True,
    },
    {
        "asset_id": "GC=F",
        "name": "Gold Futures",
        "category": "commodity",
        "source_priority": ["fdr"],
        "is_active": True,
    },
    {
        "asset_id": "SI=F",
        "name": "Silver Futures",
        "category": "commodity",
        "source_priority": ["fdr"],
        "is_active": True,
    },
]


def seed(engine) -> int:
    """Insert or update 7 assets. Returns count of upserted rows."""
    count = 0
    with Session(engine) as session:
        for data in ASSETS:
            existing = session.get(AssetMaster, data["asset_id"])
            if existing:
                existing.name = data["name"]
                existing.category = data["category"]
                existing.source_priority = data["source_priority"]
                existing.is_active = data["is_active"]
            else:
                session.add(AssetMaster(**data))
            count += 1
        session.commit()
    return count


if __name__ == "__main__":
    engine = create_engine(settings.database_url, echo=False)
    n = seed(engine)
    print(f"Seeded {n} assets into asset_master.")

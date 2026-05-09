"""Silver gen asset_master 시드 스크립트 (마스터플랜 §2.1 / §2.4 / §2.7).

기존 Bronze 7종 컬럼 갱신 + Silver 신규 8종 INSERT.
WBI는 synthetic이라 row 미생성 (Phase 2 fixture 처리).
총 15행 (Bronze 7 + Silver 8). ON CONFLICT DO UPDATE → idempotent.
"""

from decimal import Decimal

from sqlalchemy.dialects.postgresql import insert

from db.models import AssetMaster
from db.session import SessionLocal

# ---------------------------------------------------------------------------
# asset_master 시드 데이터 (마스터플랜 §2.1 / §2.4)
# ---------------------------------------------------------------------------
ASSETS = [
    # ── Bronze gen 기존 7종 (currency / annual_yield / display_name 갱신) ──
    {
        "asset_id": "KS200",
        "name": "KOSPI 200",
        "category": "index",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "KRW",
        "annual_yield": Decimal("0.0150"),   # 1.5%
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "KOSPI200",
    },
    {
        "asset_id": "005930",
        "name": "Samsung Electronics",
        "category": "stock",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "KRW",
        "annual_yield": Decimal("0.0250"),   # 2.5%
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "삼성전자",
    },
    {
        "asset_id": "000660",
        "name": "SK Hynix",
        "category": "stock",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "KRW",
        "annual_yield": Decimal("0.0100"),   # 1.0%
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "SK하이닉스",
    },
    {
        "asset_id": "SOXL",
        "name": "Direxion Daily Semiconductor Bull 3X",
        "category": "etf",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "USD",
        "annual_yield": Decimal("0.0000"),
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "SOXL",
    },
    {
        "asset_id": "BTC",
        "name": "Bitcoin KRW",
        "category": "crypto",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "KRW",
        "annual_yield": Decimal("0.0000"),
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "비트코인",
    },
    {
        "asset_id": "GC=F",
        "name": "Gold Futures",
        "category": "commodity",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "USD",
        "annual_yield": Decimal("0.0000"),
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "금",
    },
    {
        "asset_id": "SI=F",
        "name": "Silver Futures",
        "category": "commodity",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "USD",
        "annual_yield": Decimal("0.0000"),
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "은",
    },
    # ── Silver gen 신규 8종 ──
    {
        "asset_id": "QQQ",
        "name": "Invesco QQQ Trust",
        "category": "etf",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "USD",
        "annual_yield": Decimal("0.0060"),   # 0.6%
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "QQQ",
    },
    {
        "asset_id": "SPY",
        "name": "SPDR S&P 500 ETF Trust",
        "category": "etf",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "USD",
        "annual_yield": Decimal("0.0130"),   # 1.3%
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "SPY",
    },
    {
        "asset_id": "SCHD",
        "name": "Schwab US Dividend Equity ETF",
        "category": "etf",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "USD",
        "annual_yield": Decimal("0.0350"),   # 3.5%
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "SCHD",
    },
    {
        "asset_id": "JEPI",
        "name": "JPMorgan Equity Premium Income ETF",
        "category": "etf",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "USD",
        "annual_yield": Decimal("0.0800"),   # 8.0%
        "history_start_date": "2020-05-20",  # 실제 상장일 → allow_padding=True
        "allow_padding": True,
        "display_name": "JEPI",
    },
    {
        "asset_id": "TLT",
        "name": "iShares 20+ Year Treasury Bond ETF",
        "category": "etf",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "USD",
        "annual_yield": Decimal("0.0380"),   # 3.8%
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "TLT",
    },
    {
        "asset_id": "NVDA",
        "name": "NVIDIA Corporation",
        "category": "stock",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "USD",
        "annual_yield": Decimal("0.0000"),
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "엔비디아",
    },
    {
        "asset_id": "GOOGL",
        "name": "Alphabet Inc.",
        "category": "stock",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "USD",
        "annual_yield": Decimal("0.0000"),
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "구글",
    },
    {
        "asset_id": "TSLA",
        "name": "Tesla Inc.",
        "category": "stock",
        "source_priority": {"fdr": 1},
        "is_active": True,
        "currency": "USD",
        "annual_yield": Decimal("0.0000"),
        "history_start_date": None,
        "allow_padding": False,
        "display_name": "테슬라",
    },
]

UPDATE_COLS = [
    "name", "category", "source_priority", "is_active",
    "currency", "annual_yield", "history_start_date", "allow_padding", "display_name",
]


def seed(session) -> int:
    stmt = insert(AssetMaster).values(ASSETS)
    stmt = stmt.on_conflict_do_update(
        index_elements=["asset_id"],
        set_={col: stmt.excluded[col] for col in UPDATE_COLS},
    )
    session.execute(stmt)
    return len(ASSETS)


if __name__ == "__main__":
    with SessionLocal() as session:
        count = seed(session)
        session.commit()
    print(f"seed 완료: {count}행 upserted")

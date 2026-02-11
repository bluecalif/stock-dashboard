"""asset_master 시드 스크립트 — 7개 자산 초기 데이터 삽입."""

from sqlalchemy import select

from config.settings import settings
from db.models import AssetMaster
from db.session import SessionLocal

ASSETS = [
    {
        "asset_id": "KS200",
        "name": "KOSPI200",
        "category": "index",
        "source_priority": {"1": "fdr"},
    },
    {
        "asset_id": "005930",
        "name": "삼성전자",
        "category": "stock",
        "source_priority": {"1": "fdr", "2": "hantoo"},
    },
    {
        "asset_id": "000660",
        "name": "SK하이닉스",
        "category": "stock",
        "source_priority": {"1": "fdr", "2": "hantoo"},
    },
    {
        "asset_id": "SOXL",
        "name": "SOXL",
        "category": "etf",
        "source_priority": {"1": "fdr"},
    },
    {
        "asset_id": "BTC",
        "name": "비트코인",
        "category": "crypto",
        "source_priority": {"1": "fdr"},
    },
    {
        "asset_id": "GC=F",
        "name": "금",
        "category": "commodity",
        "source_priority": {"1": "fdr"},
    },
    {
        "asset_id": "SI=F",
        "name": "은",
        "category": "commodity",
        "source_priority": {"1": "fdr"},
    },
]


def seed() -> None:
    if not settings.database_url:
        print("ERROR: DATABASE_URL이 설정되지 않았습니다.")
        return

    if SessionLocal is None:
        print("ERROR: DB 세션을 생성할 수 없습니다.")
        return

    session = SessionLocal()
    inserted = 0
    skipped = 0

    try:
        for asset_data in ASSETS:
            exists = session.execute(
                select(AssetMaster).where(
                    AssetMaster.asset_id == asset_data["asset_id"]
                )
            ).scalar_one_or_none()

            if exists:
                skipped += 1
                print(f"  SKIP: {asset_data['asset_id']} ({asset_data['name']})")
            else:
                session.add(AssetMaster(**asset_data))
                inserted += 1
                print(f"  INSERT: {asset_data['asset_id']} ({asset_data['name']})")

        session.commit()
        print(f"\n완료: inserted={inserted}, skipped={skipped}")
    except Exception as e:
        session.rollback()
        print(f"\nERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed()

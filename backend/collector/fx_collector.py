"""USD/KRW 일별 환율 수집기 (Silver gen, 마스터플랜 §2.3 / §5.2).

FDR 'USD/KRW' 일봉을 수집해 fx_daily 테이블에 UPSERT.
충돌 키: date (PK). 동일 구간 재실행 시 usd_krw_close만 덮어씀 (idempotent).
"""

import argparse
import logging
from datetime import datetime, timezone
from decimal import Decimal

import pandas as pd
from sqlalchemy.dialects.postgresql import insert

from collector.alerting import send_discord_alert
from collector.fdr_client import _fetch_raw
from config.settings import settings
from db.models import FxDaily
from db.session import SessionLocal

logger = logging.getLogger(__name__)


def collect_usd_krw(start: str, end: str) -> pd.DataFrame:
    """FDR 'USD/KRW' 일봉 조회 → (date, usd_krw_close) DataFrame 반환."""
    df = _fetch_raw("USD/KRW", start, end)
    if df.empty:
        return pd.DataFrame(columns=["date", "usd_krw_close"])

    df = df.reset_index()
    df.columns = [c.lower() for c in df.columns]

    date_col = "date" if "date" in df.columns else df.columns[0]
    df = df.rename(columns={date_col: "date"})
    df = df[["date", "close"]].rename(columns={"close": "usd_krw_close"})
    df = df.dropna(subset=["usd_krw_close"])
    df["date"] = pd.to_datetime(df["date"]).dt.date
    df["usd_krw_close"] = df["usd_krw_close"].apply(lambda x: Decimal(str(round(float(x), 4))))
    return df.reset_index(drop=True)


def upsert_fx_daily(session, df: pd.DataFrame, chunk_size: int = 1000) -> int:
    """fx_daily ON CONFLICT(date) DO UPDATE — idempotent UPSERT."""
    if df.empty:
        return 0

    records = df.to_dict(orient="records")
    total = 0

    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        stmt = insert(FxDaily).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=["date"],
            set_={"usd_krw_close": stmt.excluded.usd_krw_close},
        )
        session.execute(stmt)
        total += len(chunk)

    session.flush()
    return total


def run(start: str, end: str) -> dict:
    """수집 + UPSERT 실행. 결과 dict 반환."""
    started = datetime.now(timezone.utc)
    try:
        df = collect_usd_krw(start, end)
        row_count = len(df)

        if row_count == 0:
            logger.warning("fx_collector: USD/KRW 데이터 없음 (%s ~ %s)", start, end)
            return {"status": "empty", "rows": 0, "start": start, "end": end}

        with SessionLocal() as session:
            upserted = upsert_fx_daily(session, df)
            session.commit()

        elapsed = (datetime.now(timezone.utc) - started).total_seconds()
        logger.info("fx_collector: %d row upserted (%.1fs)", upserted, elapsed)
        return {"status": "success", "rows": upserted, "start": start, "end": end}

    except Exception as exc:
        logger.exception("fx_collector 실패: %s", exc)
        send_discord_alert(
            settings.discord_webhook_url,
            f"[fx_collector] USD/KRW 수집 실패 ({start}~{end}): {exc}",
        )
        return {"status": "error", "error": str(exc), "rows": 0}


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    parser = argparse.ArgumentParser(description="USD/KRW 일봉 수집")
    parser.add_argument("--start", required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()

    result = run(args.start, args.end)
    print(result)

import uuid

from sqlalchemy import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.types import JSON


class Base(DeclarativeBase):
    pass


class AssetMaster(Base):
    __tablename__ = "asset_master"

    asset_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(20), nullable=False)
    source_priority: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class PriceDaily(Base):
    __tablename__ = "price_daily"

    asset_id: Mapped[str] = mapped_column(
        String(20), primary_key=True
    )
    date: Mapped["Date"] = mapped_column(Date, primary_key=True)
    source: Mapped[str] = mapped_column(String(20), primary_key=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[int] = mapped_column(BigInteger, nullable=False)
    ingested_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_price_daily_asset_date", "asset_id", date.desc()),
        Index("ix_price_daily_date", "date"),
    )


class FactorDaily(Base):
    __tablename__ = "factor_daily"

    asset_id: Mapped[str] = mapped_column(
        String(20), primary_key=True
    )
    date: Mapped["Date"] = mapped_column(Date, primary_key=True)
    factor_name: Mapped[str] = mapped_column(String(50), primary_key=True)
    version: Mapped[str] = mapped_column(String(10), primary_key=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)

    __table_args__ = (
        Index("ix_factor_daily_asset_date", "asset_id", date.desc()),
    )


class SignalDaily(Base):
    __tablename__ = "signal_daily"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_id: Mapped[str] = mapped_column(String(20), nullable=False)
    date: Mapped["Date"] = mapped_column(Date, nullable=False)
    strategy_id: Mapped[str] = mapped_column(String(50), nullable=False)
    signal: Mapped[int] = mapped_column(Integer, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    action: Mapped[str | None] = mapped_column(String(10), nullable=True)
    meta_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    __table_args__ = (
        Index("ix_signal_daily_asset_date_strategy", "asset_id", "date", "strategy_id"),
    )


class BacktestRun(Base):
    __tablename__ = "backtest_run"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    strategy_id: Mapped[str] = mapped_column(String(50), nullable=False)
    config_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    started_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped["DateTime | None"] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)


class BacktestEquityCurve(Base):
    __tablename__ = "backtest_equity_curve"

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True
    )
    date: Mapped["Date"] = mapped_column(Date, primary_key=True)
    equity: Mapped[float] = mapped_column(Float, nullable=False)
    drawdown: Mapped[float] = mapped_column(Float, nullable=False)


class BacktestTradeLog(Base):
    __tablename__ = "backtest_trade_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False
    )
    asset_id: Mapped[str] = mapped_column(String(20), nullable=False)
    entry_date: Mapped["Date"] = mapped_column(Date, nullable=False)
    exit_date: Mapped["Date | None"] = mapped_column(Date, nullable=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)
    pnl: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost: Mapped[float | None] = mapped_column(Float, nullable=True)


class JobRun(Base):
    __tablename__ = "job_run"

    job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    job_name: Mapped[str] = mapped_column(String(100), nullable=False)
    started_at: Mapped["DateTime"] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ended_at: Mapped["DateTime | None"] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

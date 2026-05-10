"""drop_backtest_tables

Revision ID: c9b884d01cb4
Revises: d8334483342c
Create Date: 2026-05-10 20:40:09.607014

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c9b884d01cb4'
down_revision: Union[str, Sequence[str], None] = 'd8334483342c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop backtest tables (Silver gen cut-over — D-15/Q8-26)."""
    # FK 의존성 순서: trade_log → equity_curve → run
    op.drop_table("backtest_trade_log")
    op.drop_table("backtest_equity_curve")
    op.drop_table("backtest_run")


def downgrade() -> None:
    """Recreate backtest tables (rollback용 — v-bronze-final 기준)."""
    op.create_table(
        "backtest_run",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("asset_id", sa.Integer(), nullable=False),
        sa.Column("strategy_name", sa.String(length=64), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "backtest_equity_curve",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("portfolio_value", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.ForeignKeyConstraint(["run_id"], ["backtest_run.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "backtest_trade_log",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("run_id", sa.Integer(), nullable=False),
        sa.Column("trade_date", sa.Date(), nullable=False),
        sa.Column("action", sa.String(length=16), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column("price", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["backtest_run.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

"""silver_rev1_schema_changes

Silver gen Phase 1 — 마스터플랜 §5.1
- asset_master: currency / annual_yield / history_start_date /
  allow_padding / display_name 5컬럼 추가
- fx_daily 테이블 신규 (USD/KRW 일봉)

Revision ID: d8334483342c
Revises: c4d2e5f6a789
Create Date: 2026-05-09 20:34:57.954563

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'd8334483342c'
down_revision: Union[str, Sequence[str], None] = 'c4d2e5f6a789'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # fx_daily 신규 테이블 (마스터플랜 §2.3 / §5.1)
    op.create_table(
        'fx_daily',
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('usd_krw_close', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('date'),
    )

    # asset_master 컬럼 추가 (모두 DEFAULT 또는 nullable → Bronze 영향 0)
    op.add_column(
        'asset_master',
        sa.Column('currency', sa.String(length=8), server_default='KRW', nullable=False),
    )
    op.add_column(
        'asset_master',
        sa.Column(
            'annual_yield',
            sa.Numeric(precision=6, scale=4),
            server_default='0',
            nullable=False,
        ),
    )
    op.add_column(
        'asset_master',
        sa.Column('history_start_date', sa.Date(), nullable=True),
    )
    op.add_column(
        'asset_master',
        sa.Column(
            'allow_padding',
            sa.Boolean(),
            server_default=sa.text('false'),
            nullable=False,
        ),
    )
    op.add_column(
        'asset_master',
        sa.Column('display_name', sa.String(length=64), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('asset_master', 'display_name')
    op.drop_column('asset_master', 'allow_padding')
    op.drop_column('asset_master', 'history_start_date')
    op.drop_column('asset_master', 'annual_yield')
    op.drop_column('asset_master', 'currency')
    op.drop_table('fx_daily')

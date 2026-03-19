"""Add user_profiles and user_activity tables

Revision ID: b3f1a2c4e567
Revises: dceace17d73e
Create Date: 2026-03-19 17:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b3f1a2c4e567'
down_revision: Union[str, Sequence[str], None] = 'dceace17d73e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('user_profiles',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('experience_level', sa.String(length=20), nullable=True),
        sa.Column('decision_style', sa.String(length=20), nullable=True),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=True),
        sa.Column('ice_breaking_raw', sa.JSON(), nullable=True),
        sa.Column('preferred_depth', sa.String(length=20), nullable=True),
        sa.Column('top_assets', sa.JSON(), nullable=True),
        sa.Column('top_categories', sa.JSON(), nullable=True),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('user_activity',
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('activity_data', sa.JSON(), nullable=True),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('user_activity')
    op.drop_table('user_profiles')

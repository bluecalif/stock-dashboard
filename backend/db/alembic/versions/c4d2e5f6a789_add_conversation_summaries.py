"""Add conversation_summaries table

Revision ID: c4d2e5f6a789
Revises: b3f1a2c4e567
Create Date: 2026-03-19 18:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c4d2e5f6a789'
down_revision: Union[str, Sequence[str], None] = 'b3f1a2c4e567'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('conversation_summaries',
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('summary_data', sa.JSON(), nullable=False),
        sa.Column(
            'updated_at', sa.DateTime(timezone=True),
            server_default=sa.text('now()'), nullable=False,
        ),
        sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('session_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('conversation_summaries')

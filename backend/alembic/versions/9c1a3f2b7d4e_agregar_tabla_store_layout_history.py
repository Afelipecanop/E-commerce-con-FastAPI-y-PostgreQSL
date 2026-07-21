"""agregar tabla store_layout_history

Revision ID: 9c1a3f2b7d4e
Revises: 7ea90d93ebc9
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9c1a3f2b7d4e'
down_revision: Union[str, Sequence[str], None] = '7ea90d93ebc9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('store_layout_history',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('page_slug', sa.String(), nullable=False),
    sa.Column('blocks', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_store_layout_history_page_slug', 'store_layout_history', ['page_slug'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_store_layout_history_page_slug', table_name='store_layout_history')
    op.drop_table('store_layout_history')

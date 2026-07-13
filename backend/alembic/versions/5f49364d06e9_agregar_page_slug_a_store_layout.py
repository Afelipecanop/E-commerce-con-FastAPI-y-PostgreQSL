"""agregar page_slug a store_layout

Revision ID: 5f49364d06e9
Revises: 302a69224730
Create Date: 2026-07-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5f49364d06e9'
down_revision: Union[str, Sequence[str], None] = '302a69224730'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'store_layout',
        sa.Column('page_slug', sa.String(), nullable=False, server_default='home')
    )
    op.create_index('ix_store_layout_page_slug', 'store_layout', ['page_slug'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_store_layout_page_slug', table_name='store_layout')
    op.drop_column('store_layout', 'page_slug')

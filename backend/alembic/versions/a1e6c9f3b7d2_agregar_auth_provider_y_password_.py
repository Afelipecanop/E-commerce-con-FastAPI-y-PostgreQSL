"""agregar auth_provider y permitir password nulo en users

Revision ID: a1e6c9f3b7d2
Revises: 9c1a3f2b7d4e
Create Date: 2026-07-22 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1e6c9f3b7d2'
down_revision: Union[str, Sequence[str], None] = '9c1a3f2b7d4e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'users',
        sa.Column('auth_provider', sa.String(), nullable=False, server_default='local'),
    )
    op.alter_column(
        'users', 'hashed_password',
        existing_type=sa.String(),
        nullable=True,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column(
        'users', 'hashed_password',
        existing_type=sa.String(),
        nullable=False,
    )
    op.drop_column('users', 'auth_provider')

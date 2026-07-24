"""add image_id to product_variants

Revision ID: f2a9d5e7c1b8
Revises: e8c1b4d6a2f3
Create Date: 2026-07-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f2a9d5e7c1b8'
down_revision: Union[str, Sequence[str], None] = 'e8c1b4d6a2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "product_variants",
        sa.Column("image_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_images.id", ondelete="SET NULL"), nullable=True),
    )
    op.create_index("ix_product_variants_image_id", "product_variants", ["image_id"])


def downgrade() -> None:
    op.drop_index("ix_product_variants_image_id", table_name="product_variants")
    op.drop_column("product_variants", "image_id")

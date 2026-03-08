"""add_weakness_soft_delete

Revision ID: 67d6bdcfe8ca
Revises: 5e39f059aa41
Create Date: 2026-03-06 11:31:27.002670

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '67d6bdcfe8ca'
down_revision: Union[str, None] = '5e39f059aa41'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('weakness_tags', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('weakness_tags', sa.Column('deleted_by', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('weakness_tags', 'deleted_by')
    op.drop_column('weakness_tags', 'deleted_at')

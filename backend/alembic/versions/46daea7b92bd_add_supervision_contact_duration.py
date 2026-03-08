"""add_supervision_contact_duration

Revision ID: 46daea7b92bd
Revises: 263a04943e30
Create Date: 2026-03-06 10:59:19.599025

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46daea7b92bd'
down_revision: Union[str, None] = '263a04943e30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('supervision_logs', sa.Column('contact_duration', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('supervision_logs', 'contact_duration')

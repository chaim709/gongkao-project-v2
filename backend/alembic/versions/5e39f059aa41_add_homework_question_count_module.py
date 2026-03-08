"""add_homework_question_count_module

Revision ID: 5e39f059aa41
Revises: 46daea7b92bd
Create Date: 2026-03-06 11:16:21.229740

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5e39f059aa41'
down_revision: Union[str, None] = '46daea7b92bd'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('homework', sa.Column('question_count', sa.Integer(), nullable=True))
    op.add_column('homework', sa.Column('module', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('homework', 'module')
    op.drop_column('homework', 'question_count')

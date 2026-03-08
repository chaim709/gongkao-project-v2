"""add_student_parent_phone_class_name

Revision ID: 263a04943e30
Revises: 43a92ad4e32f
Create Date: 2026-03-06 10:52:34.824724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '263a04943e30'
down_revision: Union[str, None] = '43a92ad4e32f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('students', sa.Column('parent_phone', sa.String(length=20), nullable=True))
    op.add_column('students', sa.Column('class_name', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('students', 'class_name')
    op.drop_column('students', 'parent_phone')

"""create_positions_table_actual

Revision ID: 9ef290043290
Revises: a55fcd886533
Create Date: 2026-03-06 10:31:05.392109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ef290043290'
down_revision: Union[str, None] = 'a55fcd886533'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('positions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('department', sa.String(length=200), nullable=True),
        sa.Column('location', sa.String(length=100), nullable=True),
        sa.Column('education', sa.String(length=50), nullable=True),
        sa.Column('major', sa.String(length=200), nullable=True),
        sa.Column('degree', sa.String(length=50), nullable=True),
        sa.Column('political_status', sa.String(length=50), nullable=True),
        sa.Column('work_experience', sa.String(length=100), nullable=True),
        sa.Column('other_requirements', sa.Text(), nullable=True),
        sa.Column('recruitment_count', sa.Integer(), server_default='1'),
        sa.Column('exam_type', sa.String(length=50), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), server_default='active'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_positions_id', 'positions', ['id'])
    op.create_index('ix_position_exam_location', 'positions', ['exam_type', 'location'])
    op.create_index('ix_position_education_major', 'positions', ['education', 'major'])


def downgrade() -> None:
    op.drop_index('ix_position_education_major', table_name='positions')
    op.drop_index('ix_position_exam_location', table_name='positions')
    op.drop_index('ix_positions_id', table_name='positions')
    op.drop_table('positions')

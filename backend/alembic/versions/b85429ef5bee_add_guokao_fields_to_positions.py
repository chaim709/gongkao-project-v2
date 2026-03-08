"""add guokao fields to positions

Revision ID: b85429ef5bee
Revises: h1i2j3k4l5m6
Create Date: 2026-03-08 23:03:13.626021

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b85429ef5bee'
down_revision: Union[str, None] = 'h1i2j3k4l5m6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('positions', sa.Column('province', sa.String(length=50), nullable=True))
    op.add_column('positions', sa.Column('hiring_unit', sa.String(length=200), nullable=True))
    op.add_column('positions', sa.Column('institution_level', sa.String(length=100), nullable=True))
    op.add_column('positions', sa.Column('position_attribute', sa.String(length=100), nullable=True))
    op.add_column('positions', sa.Column('position_distribution', sa.String(length=100), nullable=True))
    op.add_column('positions', sa.Column('interview_ratio', sa.String(length=50), nullable=True))
    op.add_column('positions', sa.Column('settlement_location', sa.String(length=200), nullable=True))
    op.add_column('positions', sa.Column('grassroots_project', sa.String(length=200), nullable=True))
    op.create_index('ix_position_province_year', 'positions', ['province', 'year'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_position_province_year', table_name='positions')
    op.drop_column('positions', 'grassroots_project')
    op.drop_column('positions', 'settlement_location')
    op.drop_column('positions', 'interview_ratio')
    op.drop_column('positions', 'position_distribution')
    op.drop_column('positions', 'position_attribute')
    op.drop_column('positions', 'institution_level')
    op.drop_column('positions', 'hiring_unit')
    op.drop_column('positions', 'province')

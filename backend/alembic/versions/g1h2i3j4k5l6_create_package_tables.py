"""create package tables

Revision ID: g1h2i3j4k5l6
Revises: a1b2c3d4e5f6
Create Date: 2026-03-06 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'g1h2i3j4k5l6'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 套餐表
    op.create_table(
        'packages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('original_price', sa.Numeric(10, 2)),
        sa.Column('validity_days', sa.Integer(), server_default='365'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', sa.Integer()),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_packages_id', 'packages', ['id'])

    # 套餐项目表
    op.create_table(
        'package_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(length=50), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['package_id'], ['packages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_package_items_id', 'package_items', ['id'])
    op.create_index('ix_package_items_package_id', 'package_items', ['package_id'])


def downgrade() -> None:
    op.drop_index('ix_package_items_package_id', 'package_items')
    op.drop_index('ix_package_items_id', 'package_items')
    op.drop_table('package_items')

    op.drop_index('ix_packages_id', 'packages')
    op.drop_table('packages')

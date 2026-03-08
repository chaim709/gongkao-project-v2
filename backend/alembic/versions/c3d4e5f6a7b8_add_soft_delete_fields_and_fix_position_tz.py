"""add soft delete fields to multiple models and fix position timezone

Revision ID: c3d4e5f6a7b8
Revises: 8a5820c6b78a
Create Date: 2026-03-09 07:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = '8a5820c6b78a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. positions: 添加软删除字段 + 修复时间字段为 timezone-aware
    op.add_column('positions', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('positions', sa.Column('deleted_by', sa.Integer(), nullable=True))
    op.alter_column('positions', 'created_at',
                     type_=sa.DateTime(timezone=True),
                     existing_type=sa.DateTime(),
                     existing_nullable=True)
    op.alter_column('positions', 'updated_at',
                     type_=sa.DateTime(timezone=True),
                     existing_type=sa.DateTime(),
                     existing_nullable=True)

    # 2. checkins: 添加软删除字段
    op.add_column('checkins', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('checkins', sa.Column('deleted_by', sa.Integer(), nullable=True))

    # 3. notifications: 添加软删除字段
    op.add_column('notifications', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # 4. position_favorites: 添加软删除字段
    op.add_column('position_favorites', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # 5. student_answers: 添加软删除字段
    op.add_column('student_answers', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # 6. exam_scores: 添加软删除字段
    op.add_column('exam_scores', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # 7. workbook_items: 添加软删除字段
    op.add_column('workbook_items', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # 8. subjects: 添加软删除字段
    op.add_column('subjects', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # 9. class_types: 添加软删除字段
    op.add_column('class_types', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # 10. exam_papers: 添加 deleted_by（已有 deleted_at）
    op.add_column('exam_papers', sa.Column('deleted_by', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('exam_papers', 'deleted_by')
    op.drop_column('class_types', 'deleted_at')
    op.drop_column('subjects', 'deleted_at')
    op.drop_column('workbook_items', 'deleted_at')
    op.drop_column('exam_scores', 'deleted_at')
    op.drop_column('student_answers', 'deleted_at')
    op.drop_column('position_favorites', 'deleted_at')
    op.drop_column('notifications', 'deleted_at')
    op.drop_column('checkins', 'deleted_by')
    op.drop_column('checkins', 'deleted_at')

    # 恢复 positions 时间字段为无时区
    op.alter_column('positions', 'updated_at',
                     type_=sa.DateTime(),
                     existing_type=sa.DateTime(timezone=True),
                     existing_nullable=True)
    op.alter_column('positions', 'created_at',
                     type_=sa.DateTime(),
                     existing_type=sa.DateTime(timezone=True),
                     existing_nullable=True)
    op.drop_column('positions', 'deleted_by')
    op.drop_column('positions', 'deleted_at')

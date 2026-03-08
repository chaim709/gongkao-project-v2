"""add recruitment_info and crawler_config tables

Revision ID: 8a5820c6b78a
Revises: b85429ef5bee
Create Date: 2026-03-09 04:06:07.058532

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8a5820c6b78a'
down_revision: Union[str, None] = 'b85429ef5bee'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 创建爬虫配置表
    op.create_table('crawler_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('target_url', sa.String(length=500), nullable=True),
        sa.Column('interval_minutes', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('session_valid', sa.Boolean(), nullable=True),
        sa.Column('last_crawl_at', sa.DateTime(), nullable=True),
        sa.Column('last_crawl_status', sa.String(length=20), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('total_crawled', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # 创建招考信息表
    op.create_table('recruitment_infos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_id', sa.String(length=200), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('exam_type', sa.String(length=50), nullable=True),
        sa.Column('area', sa.String(length=200), nullable=True),
        sa.Column('province', sa.String(length=50), nullable=True),
        sa.Column('city', sa.String(length=50), nullable=True),
        sa.Column('district', sa.String(length=100), nullable=True),
        sa.Column('publish_date', sa.DateTime(), nullable=True),
        sa.Column('registration_start', sa.DateTime(), nullable=True),
        sa.Column('registration_end', sa.DateTime(), nullable=True),
        sa.Column('exam_date', sa.DateTime(), nullable=True),
        sa.Column('recruitment_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('attachments', sa.Text(), nullable=True),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('source_site', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_recruitment_exam_province', 'recruitment_infos', ['exam_type', 'province'], unique=False)
    op.create_index(op.f('ix_recruitment_infos_city'), 'recruitment_infos', ['city'], unique=False)
    op.create_index(op.f('ix_recruitment_infos_exam_type'), 'recruitment_infos', ['exam_type'], unique=False)
    op.create_index(op.f('ix_recruitment_infos_id'), 'recruitment_infos', ['id'], unique=False)
    op.create_index(op.f('ix_recruitment_infos_province'), 'recruitment_infos', ['province'], unique=False)
    op.create_index(op.f('ix_recruitment_infos_source_id'), 'recruitment_infos', ['source_id'], unique=True)
    op.create_index('ix_recruitment_province_city', 'recruitment_infos', ['province', 'city'], unique=False)
    op.create_index('ix_recruitment_publish_date', 'recruitment_infos', ['publish_date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_recruitment_publish_date', table_name='recruitment_infos')
    op.drop_index('ix_recruitment_province_city', table_name='recruitment_infos')
    op.drop_index(op.f('ix_recruitment_infos_source_id'), table_name='recruitment_infos')
    op.drop_index(op.f('ix_recruitment_infos_province'), table_name='recruitment_infos')
    op.drop_index(op.f('ix_recruitment_infos_id'), table_name='recruitment_infos')
    op.drop_index(op.f('ix_recruitment_infos_exam_type'), table_name='recruitment_infos')
    op.drop_index(op.f('ix_recruitment_infos_city'), table_name='recruitment_infos')
    op.drop_index('ix_recruitment_exam_province', table_name='recruitment_infos')
    op.drop_table('recruitment_infos')
    op.drop_table('crawler_configs')

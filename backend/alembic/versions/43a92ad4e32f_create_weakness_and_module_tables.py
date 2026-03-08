"""create_weakness_and_module_tables

Revision ID: 43a92ad4e32f
Revises: 9ef290043290
Create Date: 2026-03-06 10:43:19.842494

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '43a92ad4e32f'
down_revision: Union[str, None] = '9ef290043290'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# 预设知识点分类
PRESET_MODULES = [
    # 行测 - 国省考/通用
    ("常识判断", "科技常识", "通用"),
    ("常识判断", "法律常识", "通用"),
    ("常识判断", "政治常识", "通用"),
    ("常识判断", "历史人文", "通用"),
    ("常识判断", "地理常识", "通用"),
    ("言语理解", "逻辑填空", "通用"),
    ("言语理解", "片段阅读", "通用"),
    ("言语理解", "语句表达", "通用"),
    ("数量关系", "数学运算", "通用"),
    ("数量关系", "数字推理", "通用"),
    ("判断推理", "逻辑判断", "通用"),
    ("判断推理", "图形推理", "通用"),
    ("判断推理", "定义判断", "通用"),
    ("判断推理", "类比推理", "通用"),
    ("资料分析", "文字类", "通用"),
    ("资料分析", "表格类", "通用"),
    ("资料分析", "图表类", "通用"),
    # 申论
    ("申论", "概括归纳", "国省考"),
    ("申论", "综合分析", "国省考"),
    ("申论", "提出��策", "国省考"),
    ("申论", "贯彻执行", "国省考"),
    ("申论", "大作文", "国省考"),
    # 事业编特有
    ("综合知识", "政治理论", "事业编"),
    ("综合知识", "法律法规", "事业编"),
    ("综合知识", "公文写作", "事业编"),
    ("综合知识", "经济常识", "事业编"),
    ("职业能力", "数量关系", "事业编"),
    ("职业能力", "言语理解", "事业编"),
    ("职业能力", "判断推理", "事业编"),
    ("职业能力", "资料分析", "事业编"),
]


def upgrade() -> None:
    # 知识点分类表
    op.create_table('module_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('level1', sa.String(length=50), nullable=False),
        sa.Column('level2', sa.String(length=100), nullable=True),
        sa.Column('exam_type', sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_module_categories_id', 'module_categories', ['id'])
    op.create_index('ix_module_exam_level1', 'module_categories', ['exam_type', 'level1'])

    # 薄弱项标签表
    op.create_table('weakness_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('module_id', sa.Integer(), nullable=True),
        sa.Column('module_name', sa.String(length=50), nullable=False),
        sa.Column('sub_module_name', sa.String(length=100), nullable=True),
        sa.Column('level', sa.String(length=10), server_default='yellow'),
        sa.Column('accuracy_rate', sa.DECIMAL(precision=5, scale=2), nullable=True),
        sa.Column('practice_count', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['module_id'], ['module_categories.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_weakness_tags_id', 'weakness_tags', ['id'])
    op.create_index('ix_weakness_tags_student_id', 'weakness_tags', ['student_id'])
    op.create_index('ix_weakness_student_module', 'weakness_tags', ['student_id', 'module_name'])

    # 预设知识点数据
    module_table = sa.table('module_categories',
        sa.column('level1', sa.String),
        sa.column('level2', sa.String),
        sa.column('exam_type', sa.String),
    )
    op.bulk_insert(module_table, [
        {"level1": l1, "level2": l2, "exam_type": et}
        for l1, l2, et in PRESET_MODULES
    ])


def downgrade() -> None:
    op.drop_index('ix_weakness_student_module', table_name='weakness_tags')
    op.drop_index('ix_weakness_tags_student_id', table_name='weakness_tags')
    op.drop_index('ix_weakness_tags_id', table_name='weakness_tags')
    op.drop_table('weakness_tags')
    op.drop_index('ix_module_exam_level1', table_name='module_categories')
    op.drop_index('ix_module_categories_id', table_name='module_categories')
    op.drop_table('module_categories')

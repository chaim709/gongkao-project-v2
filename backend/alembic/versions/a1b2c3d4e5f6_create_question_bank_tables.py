"""create question bank tables

Revision ID: a1b2c3d4e5f6
Revises: f9a3b4c5d6e7
Create Date: 2026-03-06 13:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'f9a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 题目表
    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('stem', sa.Text(), nullable=False),
        sa.Column('option_a', sa.Text()),
        sa.Column('option_b', sa.Text()),
        sa.Column('option_c', sa.Text()),
        sa.Column('option_d', sa.Text()),
        sa.Column('answer', sa.String(length=10), nullable=False),
        sa.Column('analysis', sa.Text()),
        sa.Column('category', sa.String(length=50)),
        sa.Column('subcategory', sa.String(length=50)),
        sa.Column('knowledge_point', sa.String(length=100)),
        sa.Column('difficulty', sa.String(length=20)),
        sa.Column('source', sa.String(length=100)),
        sa.Column('year', sa.Integer()),
        sa.Column('is_image_question', sa.Boolean(), server_default='false'),
        sa.Column('image_path', sa.String(length=500)),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', sa.Integer()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_questions_id', 'questions', ['id'])
    op.create_index('ix_questions_category', 'questions', ['category'])

    # 作业本表
    op.create_table(
        'workbooks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('question_count', sa.Integer(), server_default='0'),
        sa.Column('total_score', sa.Integer(), server_default='0'),
        sa.Column('time_limit', sa.Integer()),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', sa.Integer()),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workbooks_id', 'workbooks', ['id'])

    # 作业本题目关联表
    op.create_table(
        'workbook_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('workbook_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('question_order', sa.Integer(), nullable=False),
        sa.Column('score', sa.Integer(), server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['workbook_id'], ['workbooks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workbook_items_id', 'workbook_items', ['id'])
    op.create_index('ix_workbook_items_workbook_id', 'workbook_items', ['workbook_id'])


def downgrade() -> None:
    op.drop_index('ix_workbook_items_workbook_id', 'workbook_items')
    op.drop_index('ix_workbook_items_id', 'workbook_items')
    op.drop_table('workbook_items')

    op.drop_index('ix_workbooks_id', 'workbooks')
    op.drop_table('workbooks')

    op.drop_index('ix_questions_category', 'questions')
    op.drop_index('ix_questions_id', 'questions')
    op.drop_table('questions')

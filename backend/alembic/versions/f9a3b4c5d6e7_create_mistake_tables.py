"""create mistake tables

Revision ID: f9a3b4c5d6e7
Revises: e8f2a3b4c5d6
Create Date: 2026-03-06 12:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'f9a3b4c5d6e7'
down_revision: Union[str, None] = 'e8f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 错题表
    op.create_table(
        'mistakes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer()),
        sa.Column('workbook_id', sa.Integer()),
        sa.Column('submission_id', sa.Integer()),
        sa.Column('question_order', sa.Integer()),
        sa.Column('wrong_answer', sa.String(length=10)),
        sa.Column('review_count', sa.Integer(), server_default='0'),
        sa.Column('last_review_at', sa.DateTime(timezone=True)),
        sa.Column('mastered', sa.Boolean(), server_default='false'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', sa.Integer()),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mistakes_id', 'mistakes', ['id'])
    op.create_index('ix_mistakes_student_id', 'mistakes', ['student_id'])

    # 错题复习表
    op.create_table(
        'mistake_reviews',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('mistake_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('review_date', sa.Date(), nullable=False),
        sa.Column('is_correct', sa.Boolean(), server_default='false'),
        sa.Column('time_spent', sa.Integer()),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['mistake_id'], ['mistakes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mistake_reviews_id', 'mistake_reviews', ['id'])
    op.create_index('ix_mistake_reviews_mistake_id', 'mistake_reviews', ['mistake_id'])


def downgrade() -> None:
    op.drop_index('ix_mistake_reviews_mistake_id', 'mistake_reviews')
    op.drop_index('ix_mistake_reviews_id', 'mistake_reviews')
    op.drop_table('mistake_reviews')

    op.drop_index('ix_mistakes_student_id', 'mistakes')
    op.drop_index('ix_mistakes_id', 'mistakes')
    op.drop_table('mistakes')

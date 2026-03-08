"""create_study_plan_tables

Revision ID: cd81c6323021
Revises: 67d6bdcfe8ca
Create Date: 2026-03-06 12:00:29.931755

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cd81c6323021'
down_revision: Union[str, None] = '67d6bdcfe8ca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 学习计划表
    op.create_table(
        'study_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('phase', sa.String(length=20)),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date()),
        sa.Column('status', sa.String(length=20), server_default='active'),
        sa.Column('ai_suggestion', sa.Text()),
        sa.Column('notes', sa.Text()),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', sa.Integer()),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_study_plans_id', 'study_plans', ['id'])
    op.create_index('ix_study_plans_student_id', 'study_plans', ['student_id'])
    op.create_index('ix_plan_student_status', 'study_plans', ['student_id', 'status'])

    # 计划模板表
    op.create_table(
        'plan_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('phase', sa.String(length=20)),
        sa.Column('duration_days', sa.Integer()),
        sa.Column('description', sa.Text()),
        sa.Column('template_data', sa.Text()),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', sa.Integer()),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_plan_templates_id', 'plan_templates', ['id'])

    # 计划任务表
    op.create_table(
        'plan_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('task_type', sa.String(length=20)),
        sa.Column('target_value', sa.Integer()),
        sa.Column('actual_value', sa.Integer(), server_default='0'),
        sa.Column('due_date', sa.Date()),
        sa.Column('status', sa.String(length=20), server_default='pending'),
        sa.Column('priority', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', sa.Integer()),
        sa.ForeignKeyConstraint(['plan_id'], ['study_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_plan_tasks_id', 'plan_tasks', ['id'])
    op.create_index('ix_plan_tasks_plan_id', 'plan_tasks', ['plan_id'])
    op.create_index('ix_task_plan_status', 'plan_tasks', ['plan_id', 'status'])

    # 计划目标表
    op.create_table(
        'plan_goals',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('goal_type', sa.String(length=50), nullable=False),
        sa.Column('target_value', sa.Integer(), nullable=False),
        sa.Column('current_value', sa.Integer(), server_default='0'),
        sa.Column('status', sa.String(length=20), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['plan_id'], ['study_plans.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_plan_goals_id', 'plan_goals', ['id'])
    op.create_index('ix_plan_goals_plan_id', 'plan_goals', ['plan_id'])

    # 计划进度表
    op.create_table(
        'plan_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer()),
        sa.Column('progress_date', sa.Date(), nullable=False),
        sa.Column('progress_value', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['plan_id'], ['study_plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['plan_tasks.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_plan_progress_id', 'plan_progress', ['id'])
    op.create_index('ix_plan_progress_plan_id', 'plan_progress', ['plan_id'])
    op.create_index('ix_plan_progress_task_id', 'plan_progress', ['task_id'])
    op.create_index('ix_progress_plan_date', 'plan_progress', ['plan_id', 'progress_date'])


def downgrade() -> None:
    op.drop_index('ix_progress_plan_date', 'plan_progress')
    op.drop_index('ix_plan_progress_task_id', 'plan_progress')
    op.drop_index('ix_plan_progress_plan_id', 'plan_progress')
    op.drop_index('ix_plan_progress_id', 'plan_progress')
    op.drop_table('plan_progress')

    op.drop_index('ix_plan_goals_plan_id', 'plan_goals')
    op.drop_index('ix_plan_goals_id', 'plan_goals')
    op.drop_table('plan_goals')

    op.drop_index('ix_task_plan_status', 'plan_tasks')
    op.drop_index('ix_plan_tasks_plan_id', 'plan_tasks')
    op.drop_index('ix_plan_tasks_id', 'plan_tasks')
    op.drop_table('plan_tasks')

    op.drop_index('ix_plan_templates_id', 'plan_templates')
    op.drop_table('plan_templates')

    op.drop_index('ix_plan_student_status', 'study_plans')
    op.drop_index('ix_study_plans_student_id', 'study_plans')
    op.drop_index('ix_study_plans_id', 'study_plans')
    op.drop_table('study_plans')

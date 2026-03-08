"""create course recording tables

Revision ID: e8f2a3b4c5d6
Revises: cd81c6323021
Create Date: 2026-03-06 12:22:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e8f2a3b4c5d6'
down_revision: Union[str, None] = 'cd81c6323021'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 教师表
    op.create_table(
        'teachers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('phone', sa.String(length=20)),
        sa.Column('wechat', sa.String(length=50)),
        sa.Column('subject_ids', sa.String(length=200)),
        sa.Column('title', sa.String(length=50)),
        sa.Column('bio', sa.Text()),
        sa.Column('status', sa.String(length=20), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', sa.Integer()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_teachers_id', 'teachers', ['id'])

    # 科目表
    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('code', sa.String(length=20)),
        sa.Column('category', sa.String(length=50)),
        sa.Column('description', sa.Text()),
        sa.Column('sort_order', sa.Integer(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_subjects_id', 'subjects', ['id'])

    # 班型表
    op.create_table(
        'class_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('duration_days', sa.Integer()),
        sa.Column('price', sa.Integer()),
        sa.Column('status', sa.String(length=20), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_class_types_id', 'class_types', ['id'])

    # 班次表
    op.create_table(
        'class_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('class_type_id', sa.Integer()),
        sa.Column('start_date', sa.Date()),
        sa.Column('end_date', sa.Date()),
        sa.Column('teacher_id', sa.Integer()),
        sa.Column('student_count', sa.Integer(), server_default='0'),
        sa.Column('status', sa.String(length=20), server_default='active'),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', sa.Integer()),
        sa.ForeignKeyConstraint(['class_type_id'], ['class_types.id']),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_class_batches_id', 'class_batches', ['id'])

    # 课程表
    op.create_table(
        'schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('subject_id', sa.Integer()),
        sa.Column('teacher_id', sa.Integer()),
        sa.Column('schedule_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time()),
        sa.Column('end_time', sa.Time()),
        sa.Column('classroom', sa.String(length=50)),
        sa.Column('status', sa.String(length=20), server_default='scheduled'),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', sa.Integer()),
        sa.ForeignKeyConstraint(['batch_id'], ['class_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id']),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_schedules_id', 'schedules', ['id'])
    op.create_index('ix_schedules_batch_id', 'schedules', ['batch_id'])

    # 课程录播表
    op.create_table(
        'course_recordings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer()),
        sa.Column('schedule_id', sa.Integer()),
        sa.Column('recording_date', sa.Date(), nullable=False),
        sa.Column('period', sa.String(length=20)),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('recording_url', sa.String(length=500)),
        sa.Column('subject_id', sa.Integer()),
        sa.Column('teacher_id', sa.Integer()),
        sa.Column('duration_minutes', sa.Integer()),
        sa.Column('remark', sa.Text()),
        sa.Column('created_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.Column('updated_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('deleted_by', sa.Integer()),
        sa.ForeignKeyConstraint(['batch_id'], ['class_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id']),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id']),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_course_recordings_id', 'course_recordings', ['id'])
    op.create_index('ix_course_recordings_batch_id', 'course_recordings', ['batch_id'])

    # 课表变更日志
    op.create_table(
        'schedule_change_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('change_type', sa.String(length=50), nullable=False),
        sa.Column('old_value', sa.Text()),
        sa.Column('new_value', sa.Text()),
        sa.Column('reason', sa.Text()),
        sa.Column('changed_by', sa.Integer()),
        sa.Column('created_at', sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(['schedule_id'], ['schedules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_schedule_change_logs_id', 'schedule_change_logs', ['id'])


def downgrade() -> None:
    op.drop_index('ix_schedule_change_logs_id', 'schedule_change_logs')
    op.drop_table('schedule_change_logs')

    op.drop_index('ix_course_recordings_batch_id', 'course_recordings')
    op.drop_index('ix_course_recordings_id', 'course_recordings')
    op.drop_table('course_recordings')

    op.drop_index('ix_schedules_batch_id', 'schedules')
    op.drop_index('ix_schedules_id', 'schedules')
    op.drop_table('schedules')

    op.drop_index('ix_class_batches_id', 'class_batches')
    op.drop_table('class_batches')

    op.drop_index('ix_class_types_id', 'class_types')
    op.drop_table('class_types')

    op.drop_index('ix_subjects_id', 'subjects')
    op.drop_table('subjects')

    op.drop_index('ix_teachers_id', 'teachers')
    op.drop_table('teachers')

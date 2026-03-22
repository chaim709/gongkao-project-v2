from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from app.config import settings
from app.database import Base

# 导入所有模型以便 autogenerate 检测
from app.models.user import User  # noqa: F401
from app.models.student import Student  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.supervision_log import SupervisionLog  # noqa: F401
from app.models.course import Course  # noqa: F401
from app.models.homework import Homework, HomeworkSubmission  # noqa: F401
from app.models.checkin import Checkin  # noqa: F401
from app.models.study_plan import StudyPlan, PlanTemplate, PlanTask, PlanGoal, PlanProgress  # noqa: F401
from app.models.calendar_event import CalendarEvent  # noqa: F401
from app.models.notification import Notification  # noqa: F401
from app.models.course_recording import ClassBatch, CourseRecording  # noqa: F401
from app.models.question import Question, Workbook, WorkbookItem  # noqa: F401
from app.models.mistake import Mistake, MistakeReview  # noqa: F401
from app.models.package import Package, PackageItem  # noqa: F401
from app.models.attendance import Attendance  # noqa: F401
from app.models.position import Position  # noqa: F401
from app.models.favorite import PositionFavorite  # noqa: F401
from app.models.exam_paper import ExamPaper  # noqa: F401
from app.models.student_answer import StudentAnswer, ExamScore  # noqa: F401
from app.models.weakness import ModuleCategory, WeaknessTag  # noqa: F401
from app.models.finance import FinanceRecord  # noqa: F401
from app.models.recruitment_info import RecruitmentInfo, CrawlerConfig  # noqa: F401
from app.models.system_setting import SystemSetting  # noqa: F401

config = context.config

# 使用同步 URL 进行迁移
sync_url = (
    settings.DATABASE_URL.replace("+asyncpg", "")
    if "+asyncpg" in settings.DATABASE_URL
    else settings.DATABASE_URL
)
config.set_main_option("sqlalchemy.url", sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

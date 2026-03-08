#!/bin/sh
set -e

echo "Initializing database tables..."
python -c "
import asyncio
from app.database import engine, Base
from app.models.user import User
from app.models.student import Student
from app.models.audit_log import AuditLog
from app.models.supervision_log import SupervisionLog
from app.models.course import Course
from app.models.homework import Homework, HomeworkSubmission
from app.models.checkin import Checkin
from app.models.study_plan import StudyPlan, PlanTemplate, PlanTask, PlanGoal, PlanProgress
from app.models.calendar_event import CalendarEvent
from app.models.notification import Notification
from app.models.course_recording import ClassBatch, CourseRecording
from app.models.question import Question, Workbook, WorkbookItem
from app.models.mistake import Mistake, MistakeReview
from app.models.package import Package, PackageItem
from app.models.attendance import Attendance
from app.models.position import Position
from app.models.favorite import PositionFavorite
from app.models.exam_paper import ExamPaper
from app.models.student_answer import StudentAnswer, ExamScore
from app.models.weakness import ModuleCategory, WeaknessTag
from app.models.finance import FinanceRecord
from app.models.recruitment_info import RecruitmentInfo, CrawlerConfig

async def init():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f'Created {len(Base.metadata.tables)} tables')

asyncio.run(init())
"

echo "Seeding initial data..."
python seed_data.py

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000

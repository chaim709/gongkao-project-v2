from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.routes import auth, students, supervision_logs, courses, homework, checkins, upload, analytics, positions, audit_logs, weaknesses, study_plans, course_recordings, mistakes, questions, packages, attendances, exams, finance, export, users, notifications, calendar, recycle_bin, recruitment_info
from app.exceptions.business import BusinessError
from app.middleware.error_handler import business_error_handler, validation_error_handler, unhandled_error_handler
from app.middleware.request_logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.auth import require_admin
from app.utils.logging import setup_logging
from contextlib import asynccontextmanager
import logging
import os

# 初始化日志
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # Startup
    from app.tasks.crawler_tasks import start_scheduler
    try:
        start_scheduler()
    except Exception as e:
        logging.getLogger(__name__).warning(f"采集调度器启动失败: {e}")
    yield
    # Shutdown
    from app.tasks.crawler_tasks import stop_scheduler
    from app.services.crawler_service import crawler_service
    stop_scheduler()
    await crawler_service.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# 请求日志
app.add_middleware(RequestLoggingMiddleware)

# API 限流
app.add_middleware(RateLimitMiddleware)

# 注册异常处理
app.add_exception_handler(BusinessError, business_error_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)

# 注册路由
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(supervision_logs.router)
app.include_router(courses.router)
app.include_router(homework.router)
app.include_router(checkins.router)
app.include_router(upload.router)
app.include_router(analytics.router)
app.include_router(positions.router)
app.include_router(audit_logs.router)
app.include_router(weaknesses.router)
app.include_router(study_plans.router)
app.include_router(course_recordings.router)
app.include_router(mistakes.router)
app.include_router(questions.router)
app.include_router(packages.router)
app.include_router(attendances.router)
app.include_router(exams.router)
app.include_router(finance.router)
app.include_router(export.router)
app.include_router(users.router)
app.include_router(notifications.router)
app.include_router(calendar.router)
app.include_router(recycle_bin.router)
app.include_router(recruitment_info.router)

# 静态文件服务（上传文件）
upload_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=upload_dir), name="uploads")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": settings.APP_VERSION}


@app.post("/api/v1/tasks/daily-reminders", tags=["定时任务"])
async def run_daily_reminders(current_user=Depends(require_admin)):
    """手动触发每日提醒（跟进 + 考试倒计时），也可由 cron 调用"""
    from app.database import AsyncSessionLocal
    from app.tasks.daily_tasks import check_followup_reminders, check_exam_reminders
    async with AsyncSessionLocal() as db:
        followup_count = await check_followup_reminders(db)
    async with AsyncSessionLocal() as db:
        exam_count = await check_exam_reminders(db)
    return {
        "message": f"已发送 {followup_count} 条跟进提醒，{exam_count} 条考试提醒"
    }


@app.post("/api/v1/tasks/exam-reminders", tags=["定时任务"])
async def run_exam_reminders(current_user=Depends(require_admin)):
    """单独触发考试倒计时提醒"""
    from app.database import AsyncSessionLocal
    from app.tasks.daily_tasks import check_exam_reminders
    async with AsyncSessionLocal() as db:
        count = await check_exam_reminders(db)
    return {"message": f"已发送 {count} 条考试倒计时提醒"}


@app.get("/")
async def root():
    return {"message": "公考管理系统 V2 API"}

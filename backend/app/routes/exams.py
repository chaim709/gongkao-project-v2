from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, Integer as SAInteger
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.models.exam_paper import ExamPaper
from app.models.question import Question
from app.models.student_answer import StudentAnswer, ExamScore
from app.models.mistake import Mistake
from app.models.student import Student
from app.schemas.exam import (
    ExamPaperCreate, ExamPaperResponse, ExamPaperListResponse,
    QuestionCreate, QuestionResponse, QuestionListResponse,
    MistakeSubmit, ExamScoreCreate, ExamScoreResponse,
)
from app.services.knowledge_tags import KNOWLEDGE_TAGS, SUBJECTS, EXAM_TYPES, get_all_flat_tags
from typing import Optional
import secrets
import io
import qrcode


router = APIRouter(prefix="/api/v1/exams", tags=["题库管理"])


# ==================== 试卷管理 ====================

@router.get("/papers", response_model=ExamPaperListResponse)
async def list_papers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    subject: Optional[str] = None,
    exam_type: Optional[str] = None,
    year: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取试卷列表"""
    query = select(ExamPaper).where(ExamPaper.deleted_at.is_(None))
    count_query = select(func.count(ExamPaper.id)).where(ExamPaper.deleted_at.is_(None))

    if subject:
        query = query.where(ExamPaper.subject == subject)
        count_query = count_query.where(ExamPaper.subject == subject)
    if exam_type:
        query = query.where(ExamPaper.exam_type == exam_type)
        count_query = count_query.where(ExamPaper.exam_type == exam_type)
    if year:
        query = query.where(ExamPaper.year == year)
        count_query = count_query.where(ExamPaper.year == year)
    if search:
        query = query.where(ExamPaper.title.ilike(f"%{search}%"))
        count_query = count_query.where(ExamPaper.title.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar()
    items = (await db.execute(
        query.order_by(ExamPaper.created_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    return ExamPaperListResponse(
        items=[ExamPaperResponse.model_validate(p) for p in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("/papers", response_model=ExamPaperResponse, status_code=201)
async def create_paper(
    data: ExamPaperCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建试卷并自动生成二维码token"""
    paper = ExamPaper(
        **data.model_dump(),
        qr_code_token=secrets.token_urlsafe(16),
        created_by=current_user.id,
    )
    db.add(paper)
    await db.commit()
    await db.refresh(paper)
    return ExamPaperResponse.model_validate(paper)


@router.get("/papers/{paper_id}", response_model=ExamPaperResponse)
async def get_paper(
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取试卷详情"""
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="试卷不存在")
    return ExamPaperResponse.model_validate(paper)


@router.get("/papers/{paper_id}/qrcode")
async def get_paper_qrcode(
    paper_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """生成试卷二维码图片"""
    result = await db.execute(select(ExamPaper).where(ExamPaper.id == paper_id))
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="试卷不存在")

    # 二维码链接指向H5错题提交页面
    qr_url = f"/submit/{paper.qr_code_token}"

    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(qr_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/png")


# ==================== 题目管理 ====================

@router.get("/questions", response_model=QuestionListResponse)
async def list_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    paper_id: Optional[int] = None,
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    knowledge_point: Optional[str] = None,
    difficulty: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取题目列表"""
    query = select(Question).where(Question.deleted_at.is_(None))
    count_query = select(func.count(Question.id)).where(Question.deleted_at.is_(None))

    if paper_id:
        query = query.where(Question.paper_id == paper_id)
        count_query = count_query.where(Question.paper_id == paper_id)
    if category:
        query = query.where(Question.category == category)
        count_query = count_query.where(Question.category == category)
    if subcategory:
        query = query.where(Question.subcategory == subcategory)
        count_query = count_query.where(Question.subcategory == subcategory)
    if knowledge_point:
        query = query.where(Question.knowledge_point == knowledge_point)
        count_query = count_query.where(Question.knowledge_point == knowledge_point)
    if difficulty:
        query = query.where(Question.difficulty == difficulty)
        count_query = count_query.where(Question.difficulty == difficulty)
    if search:
        query = query.where(Question.stem.ilike(f"%{search}%"))
        count_query = count_query.where(Question.stem.ilike(f"%{search}%"))

    total = (await db.execute(count_query)).scalar()
    order = Question.question_number.asc() if paper_id else Question.id.desc()
    items = (await db.execute(
        query.order_by(order).offset((page - 1) * page_size).limit(page_size)
    )).scalars().all()

    return QuestionListResponse(
        items=[QuestionResponse.model_validate(q) for q in items],
        total=total, page=page, page_size=page_size,
    )


@router.post("/questions", response_model=QuestionResponse, status_code=201)
async def create_question(
    data: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建单个题目"""
    question = Question(**data.model_dump())
    db.add(question)
    await db.commit()
    await db.refresh(question)
    return QuestionResponse.model_validate(question)


@router.post("/questions/batch", status_code=201)
async def batch_create_questions(
    questions: list[QuestionCreate],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """批量创建题目（用于AI导入确认后入库）"""
    created = []
    for data in questions:
        q = Question(**data.model_dump())
        db.add(q)
        created.append(q)
    await db.commit()
    return {"success": True, "count": len(created)}


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_question(
    question_id: int,
    data: QuestionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新题目"""
    result = await db.execute(select(Question).where(Question.id == question_id))
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="题目不存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(question, k, v)
    await db.commit()
    await db.refresh(question)
    return QuestionResponse.model_validate(question)


# ==================== 知识点标签 ====================

@router.get("/knowledge-tags")
async def get_knowledge_tags(current_user: User = Depends(get_current_user)):
    """获取知识点标签体系"""
    return {
        "tags": KNOWLEDGE_TAGS,
        "subjects": SUBJECTS,
        "exam_types": EXAM_TYPES,
    }


# ==================== 错题提交（H5页面，不需要JWT） ====================

@router.post("/submit/{qr_token}")
async def submit_mistakes(
    qr_token: str,
    data: MistakeSubmit,
    db: AsyncSession = Depends(get_db),
):
    """学生扫码提交错题（H5页面调用，无需JWT认证）"""
    # 查找试卷
    result = await db.execute(
        select(ExamPaper).where(ExamPaper.qr_code_token == qr_token)
    )
    paper = result.scalar_one_or_none()
    if not paper:
        raise HTTPException(status_code=404, detail="试卷不存在或二维码已失效")

    # 通过手机号查找学生
    result = await db.execute(
        select(Student).where(Student.phone == data.phone, Student.deleted_at.is_(None))
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="未找到该手机号对应的学员，请联系老师")

    # 双重验证：手机号 + 姓名
    if student.name != data.student_name.strip():
        raise HTTPException(status_code=400, detail="姓名与手机号不匹配，请检查输入")

    # 获取试卷中的题目（按题号索引）
    questions_result = await db.execute(
        select(Question).where(Question.paper_id == paper.id)
    )
    questions_map = {q.question_number: q for q in questions_result.scalars().all()}

    # 记录答题和错题
    wrong_count = 0
    category_stats = {}

    # 批量查询已有错题记录，避免 N+1 查询
    wrong_question_ids = [
        questions_map[q_num].id
        for q_num in data.wrong_numbers
        if q_num in questions_map and questions_map[q_num]
    ]
    existing_mistakes_map = {}
    if wrong_question_ids:
        existing_result = await db.execute(
            select(Mistake).where(
                Mistake.student_id == student.id,
                Mistake.question_id.in_(wrong_question_ids),
            )
        )
        existing_mistakes_map = {m.question_id: m for m in existing_result.scalars().all()}

    for q_num in range(1, paper.total_questions + 1):
        is_wrong = q_num in data.wrong_numbers
        question = questions_map.get(q_num)

        # 写入答题记录
        answer = StudentAnswer(
            student_id=student.id,
            paper_id=paper.id,
            question_id=question.id if question else None,
            question_number=q_num,
            is_correct=not is_wrong,
        )
        db.add(answer)

        # 错题处理
        if is_wrong and question:
            wrong_count += 1
            subcat = question.subcategory or "未分类"
            category_stats[subcat] = category_stats.get(subcat, 0) + 1

            # 使用预加载的错题记录
            mistake = existing_mistakes_map.get(question.id)
            if mistake:
                mistake.wrong_count = (mistake.wrong_count or 1) + 1
                mistake.last_wrong_at = func.now()
                mistake.mastered = False
            else:
                db.add(Mistake(
                    student_id=student.id,
                    question_id=question.id,
                    paper_id=paper.id,
                    question_order=q_num,
                    wrong_count=1,
                ))

    # 写入成绩
    correct_count = paper.total_questions - wrong_count
    db.add(ExamScore(
        student_id=student.id,
        paper_id=paper.id,
        correct_count=correct_count,
        wrong_count=wrong_count,
        score_detail=category_stats,
    ))

    await db.commit()

    # 找出最弱的模块
    weakest = sorted(category_stats.items(), key=lambda x: x[1], reverse=True)
    weakest_text = "、".join([f"{k}({v}题)" for k, v in weakest[:3]]) if weakest else "无"

    return {
        "success": True,
        "student_name": student.name,
        "paper_title": paper.title,
        "total": paper.total_questions,
        "correct": correct_count,
        "wrong": wrong_count,
        "accuracy": round(correct_count / paper.total_questions * 100, 1),
        "weakest_areas": weakest_text,
        "message": f"提交成功！共{wrong_count}题错误，主要集中在{weakest_text}",
    }


# ==================== 模考成绩管理 ====================

@router.get("/scores")
async def list_scores(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    paper_id: Optional[int] = None,
    student_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取模考成绩列表"""
    query = (
        select(ExamScore, Student.name.label("student_name"), ExamPaper.title.label("paper_title"),
               ExamPaper.subject, ExamPaper.total_questions)
        .join(Student, ExamScore.student_id == Student.id)
        .join(ExamPaper, ExamScore.paper_id == ExamPaper.id)
    )
    count_query = select(func.count(ExamScore.id))

    if paper_id:
        query = query.where(ExamScore.paper_id == paper_id)
        count_query = count_query.where(ExamScore.paper_id == paper_id)
    if student_id:
        query = query.where(ExamScore.student_id == student_id)
        count_query = count_query.where(ExamScore.student_id == student_id)

    total = (await db.execute(count_query)).scalar()
    rows = (await db.execute(
        query.order_by(ExamScore.submitted_at.desc())
        .offset((page - 1) * page_size).limit(page_size)
    )).all()

    items = []
    for score, student_name, paper_title, subject, total_questions in rows:
        total_answered = (score.correct_count or 0) + (score.wrong_count or 0)
        accuracy = round(score.correct_count / total_answered * 100, 1) if total_answered > 0 else 0
        items.append({
            "id": score.id,
            "student_id": score.student_id,
            "student_name": student_name,
            "paper_id": score.paper_id,
            "paper_title": paper_title,
            "subject": subject,
            "total_questions": total_questions,
            "correct_count": score.correct_count,
            "wrong_count": score.wrong_count,
            "accuracy": accuracy,
            "time_used": score.time_used,
            "rank_in_class": score.rank_in_class,
            "score_detail": score.score_detail,
            "submitted_at": score.submitted_at.isoformat() if score.submitted_at else None,
        })

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/scores", status_code=201)
async def create_score(
    data: ExamScoreCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动录入模考成绩"""
    # 检查是否已有成绩
    existing = await db.execute(
        select(ExamScore).where(
            ExamScore.student_id == data.student_id,
            ExamScore.paper_id == data.paper_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="该学员已有该试卷的成绩记录")

    score = ExamScore(**data.model_dump())
    db.add(score)
    await db.commit()
    await db.refresh(score)
    return {"success": True, "id": score.id}


# ==================== AI 题目导入 ====================

@router.post("/ai-parse")
async def ai_parse_questions(
    file: UploadFile = File(...),
    subject: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    """上传文档，AI 解析题目（返回预览数据，不入库）"""
    from app.services.ai_parser import parse_questions_with_ai

    # 读取文件内容
    content_bytes = await file.read()

    # 根据文件类型提取文本
    filename = file.filename or ""
    if filename.endswith(".txt"):
        text = content_bytes.decode("utf-8", errors="ignore")
    elif filename.endswith(".md"):
        text = content_bytes.decode("utf-8", errors="ignore")
    else:
        # 对于 PDF/Word 等格式，暂时以纯文本方式读取
        # 后续可集成 PyPDF2/python-docx 等库
        text = content_bytes.decode("utf-8", errors="ignore")

    if not text.strip():
        raise HTTPException(status_code=400, detail="文件内容为空")
    if len(text) > 50000:
        text = text[:50000]

    try:
        result = await parse_questions_with_ai(text, subject=subject)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI解析失败: {str(e)}")


# ==================== 学员弱项分析 ====================

@router.get("/analysis/student/{student_id}")
async def get_student_analysis(
    student_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学员弱项分析（雷达图数据）"""
    # 获取该学员所有答题记录，按知识点二级分类统计
    result = await db.execute(
        select(
            Question.subcategory,
            func.count(StudentAnswer.id).label("total"),
            func.sum(StudentAnswer.is_correct.cast(SAInteger)).label("correct"),
        )
        .join(Question, StudentAnswer.question_id == Question.id)
        .where(StudentAnswer.student_id == student_id)
        .group_by(Question.subcategory)
    )
    rows = result.all()

    categories = []
    for subcat, total, correct in rows:
        if not subcat:
            continue
        correct = correct or 0
        accuracy = round(correct / total * 100, 1) if total > 0 else 0
        categories.append({
            "category": subcat,
            "total": total,
            "correct": correct,
            "wrong": total - correct,
            "accuracy": accuracy,
        })

    categories.sort(key=lambda x: x["accuracy"])

    # 最近5次模考成绩趋势
    scores_result = await db.execute(
        select(ExamScore, ExamPaper.title)
        .join(ExamPaper, ExamScore.paper_id == ExamPaper.id)
        .where(ExamScore.student_id == student_id)
        .order_by(ExamScore.submitted_at.desc())
        .limit(10)
    )
    scores = [{
        "paper_title": title,
        "correct": s.correct_count,
        "wrong": s.wrong_count,
        "accuracy": round(s.correct_count / (s.correct_count + s.wrong_count) * 100, 1)
        if s.correct_count and s.wrong_count else 0,
        "date": s.submitted_at.strftime("%m/%d") if s.submitted_at else "",
        "score_detail": s.score_detail,
    } for s, title in scores_result.all()]

    # 错题总数
    mistake_count = (await db.execute(
        select(func.count(Mistake.id)).where(
            Mistake.student_id == student_id,
            Mistake.mastered == False,
        )
    )).scalar()

    return {
        "student_id": student_id,
        "categories": categories,
        "weakest": categories[:3] if categories else [],
        "scores_trend": list(reversed(scores)),
        "unmastered_mistakes": mistake_count,
    }


# ==================== 班级分析 ====================

@router.get("/analysis/class")
async def get_class_analysis(
    paper_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取班级整体分析（排名、弱项、对比）"""
    # 学员成绩排名
    score_query = (
        select(
            ExamScore.student_id,
            Student.name.label("student_name"),
            func.count(ExamScore.id).label("exam_count"),
            func.avg(
                ExamScore.correct_count * 100.0 / (ExamScore.correct_count + ExamScore.wrong_count)
            ).label("avg_accuracy"),
            func.max(
                ExamScore.correct_count * 100.0 / (ExamScore.correct_count + ExamScore.wrong_count)
            ).label("best_accuracy"),
        )
        .join(Student, ExamScore.student_id == Student.id)
        .where(ExamScore.correct_count.isnot(None), ExamScore.wrong_count.isnot(None))
        .where((ExamScore.correct_count + ExamScore.wrong_count) > 0)
    )
    if paper_id:
        score_query = score_query.where(ExamScore.paper_id == paper_id)

    score_query = score_query.group_by(ExamScore.student_id, Student.name)
    rows = (await db.execute(score_query)).all()

    rankings = sorted([{
        "student_id": sid,
        "student_name": name,
        "exam_count": cnt,
        "avg_accuracy": round(float(avg_acc), 1) if avg_acc else 0,
        "best_accuracy": round(float(best), 1) if best else 0,
    } for sid, name, cnt, avg_acc, best in rows], key=lambda x: x["avg_accuracy"], reverse=True)

    # 添加排名
    for i, r in enumerate(rankings):
        r["rank"] = i + 1

    # 班级整体弱项（所有学员答题按 subcategory 聚合）
    weak_query = (
        select(
            Question.subcategory,
            func.count(StudentAnswer.id).label("total"),
            func.sum(StudentAnswer.is_correct.cast(SAInteger)).label("correct"),
        )
        .join(Question, StudentAnswer.question_id == Question.id)
        .group_by(Question.subcategory)
    )
    if paper_id:
        weak_query = weak_query.where(StudentAnswer.paper_id == paper_id)

    weak_rows = (await db.execute(weak_query)).all()
    class_weaknesses = []
    for subcat, total, correct in weak_rows:
        if not subcat:
            continue
        correct = correct or 0
        accuracy = round(correct / total * 100, 1) if total > 0 else 0
        class_weaknesses.append({
            "category": subcat,
            "total": total,
            "correct": correct,
            "wrong": total - correct,
            "accuracy": accuracy,
        })
    class_weaknesses.sort(key=lambda x: x["accuracy"])

    # 统计概览
    total_students = len(rankings)
    avg_class = round(sum(r["avg_accuracy"] for r in rankings) / total_students, 1) if total_students else 0
    total_exams = (await db.execute(select(func.count(ExamScore.id)))).scalar()

    return {
        "rankings": rankings,
        "class_weaknesses": class_weaknesses[:10],
        "summary": {
            "total_students": total_students,
            "avg_accuracy": avg_class,
            "total_exams": total_exams,
            "weakest_area": class_weaknesses[0]["category"] if class_weaknesses else "无数据",
        },
    }

"""种子数据脚本：初始化系统所需的基础数据"""
import asyncio
from datetime import date, datetime, timezone, timedelta
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.models.student import Student
from app.models.supervision_log import SupervisionLog
from app.models.course import Course
from app.models.homework import Homework, HomeworkSubmission
from app.models.checkin import Checkin
from app.models.position import Position
from app.models.recruitment_info import CrawlerConfig
from app.utils.security import hash_password


def utc_now():
    return datetime.now(timezone.utc)


async def seed_users(session):
    """创建初始用户，返回督学用户 ID 列表"""
    required = [
        ("admin", "admin123", "系统管理员", "admin", "13800000001"),
        ("supervisor1", "123456", "张老师", "supervisor", "13800000002"),
        ("supervisor2", "123456", "李老师", "supervisor", "13800000003"),
        ("supervisor3", "123456", "王老师", "supervisor", "13800000004"),
    ]

    created = 0
    for username, pwd, name, role, phone in required:
        stmt = select(User).where(User.username == username)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            session.add(User(username=username, password_hash=hash_password(pwd),
                             real_name=name, role=role, phone=phone, is_active=True))
            created += 1

    await session.flush()
    if created:
        print(f"  创建 {created} 个用户")
    else:
        print("  用户已齐全，跳过")

    # 返回督学用户 ID 列表
    stmt = select(User).where(User.role == "supervisor").order_by(User.id)
    result = await session.execute(stmt)
    return [u.id for u in result.scalars().all()]


async def seed_students(session, supervisor_ids):
    """创建测试学员"""
    stmt = select(Student).limit(1)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        print("  学员数据已存在，跳过")
        return

    s = supervisor_ids  # 简写
    students_data = [
        {"name": "赵一", "phone": "13900000001", "gender": "男", "exam_type": "国省考",
         "education": "本科", "major": "法学", "supervisor_id": s[0], "status": "active",
         "enrollment_date": date(2026, 1, 10), "has_basic": True, "hukou_province": "江苏", "hukou_city": "南京"},
        {"name": "钱二", "phone": "13900000002", "gender": "女", "exam_type": "国省考",
         "education": "硕士", "major": "中文", "supervisor_id": s[0], "status": "active",
         "enrollment_date": date(2026, 1, 15), "has_basic": False, "hukou_province": "江苏", "hukou_city": "苏州"},
        {"name": "孙三", "phone": "13900000003", "gender": "男", "exam_type": "事业编",
         "education": "本科", "major": "计算机", "supervisor_id": s[1], "status": "active",
         "enrollment_date": date(2026, 1, 20), "has_basic": True, "hukou_province": "安徽", "hukou_city": "合肥"},
        {"name": "李四", "phone": "13900000004", "gender": "女", "exam_type": "事业编",
         "education": "本科", "major": "会计", "supervisor_id": s[1], "status": "active",
         "enrollment_date": date(2026, 2, 1), "has_basic": False, "hukou_province": "江苏", "hukou_city": "徐州"},
        {"name": "周五", "phone": "13900000005", "gender": "男", "exam_type": "国省考",
         "education": "本科", "major": "行政管理", "supervisor_id": s[0], "status": "active",
         "enrollment_date": date(2026, 2, 5), "has_basic": True, "hukou_province": "江苏", "hukou_city": "南京"},
        {"name": "吴六", "phone": "13900000006", "gender": "女", "exam_type": "三支一扶",
         "education": "大专", "major": "护理", "supervisor_id": s[2], "status": "active",
         "enrollment_date": date(2026, 2, 10), "has_basic": False, "hukou_province": "安徽", "hukou_city": "宿州"},
        {"name": "郑七", "phone": "13900000007", "gender": "男", "exam_type": "国省考",
         "education": "本科", "major": "经济学", "supervisor_id": s[2], "status": "active",
         "enrollment_date": date(2026, 2, 15), "has_basic": True, "hukou_province": "江苏", "hukou_city": "无锡"},
        {"name": "王八", "phone": "13900000008", "gender": "女", "exam_type": "事业编",
         "education": "硕士", "major": "教育学", "supervisor_id": s[0], "status": "active",
         "enrollment_date": date(2026, 2, 20), "has_basic": False, "hukou_province": "江苏", "hukou_city": "常州"},
        {"name": "冯九", "phone": "13900000009", "gender": "男", "exam_type": "国省考",
         "education": "本科", "major": "政治学", "supervisor_id": s[1], "status": "inactive",
         "enrollment_date": date(2025, 9, 1), "has_basic": True, "hukou_province": "安徽", "hukou_city": "蚌埠"},
        {"name": "陈十", "phone": "13900000010", "gender": "女", "exam_type": "事业编",
         "education": "本科", "major": "英语", "supervisor_id": s[2], "status": "graduated",
         "enrollment_date": date(2025, 6, 1), "has_basic": True, "hukou_province": "江苏", "hukou_city": "泗洪"},
    ]

    students = [Student(**data) for data in students_data]
    session.add_all(students)
    await session.flush()
    print(f"  创建 {len(students)} 个学员")


async def seed_supervision_logs(session, supervisor_ids):
    """创建督学日志数据"""
    stmt = select(SupervisionLog).limit(1)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        print("  督学日志已存在，跳过")
        return

    # 获取学员 ID
    stmt = select(Student.id).where(Student.status == "active").order_by(Student.id)
    result = await session.execute(stmt)
    student_ids = [r[0] for r in result.all()]

    today = date.today()
    logs = []
    contents = [
        "学员反馈行测做题速度提升，但判断推理仍需加强。布置了专项练习。",
        "电话沟通学习进度，学员状态良好，按计划推进复习。",
        "微信沟通，学员反映申论大作文写作有困难，建议多看范文。",
        "面谈讨论备考计划调整，学员决定侧重常识和数量关系。",
        "学员情绪有些焦虑，考试临近压力较大。做了心理疏导。",
        "检查模拟卷成绩，总分135，进步明显。鼓励继续保持。",
    ]
    methods = ["phone", "wechat", "meeting"]
    moods = ["positive", "stable", "anxious", "down"]
    statuses = ["excellent", "good", "average", "poor"]

    for i, sid in enumerate(student_ids):
        sup_id = supervisor_ids[i % len(supervisor_ids)]
        for days_ago in range(0, 30, 3 + i % 4):
            log_date = today - timedelta(days=days_ago)
            logs.append(SupervisionLog(
                student_id=sid,
                supervisor_id=sup_id,
                log_date=log_date,
                contact_method=methods[days_ago % 3],
                mood=moods[days_ago % 4],
                study_status=statuses[days_ago % 4],
                content=contents[days_ago % len(contents)],
                next_followup_date=log_date + timedelta(days=3),
            ))

    session.add_all(logs)
    await session.flush()
    print(f"  创建 {len(logs)} 条督学日志")


async def seed_courses(session, supervisor_ids):
    """创建课程数据"""
    stmt = select(Course).limit(1)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        print("  课程数据已存在，跳过")
        return

    courses = [
        Course(name="2026国省考全程班", course_type="国省考", teacher_id=supervisor_ids[0],
               start_date=date(2026, 1, 10), end_date=date(2026, 4, 30),
               description="国省考全程班，涵盖行测+申论全部模块", status="active"),
        Course(name="2026事业编基础班", course_type="事业编", teacher_id=supervisor_ids[1],
               start_date=date(2026, 2, 1), end_date=date(2026, 5, 30),
               description="事业编基础班，主讲综合知识和职业能力", status="active"),
        Course(name="行测刷题强化班", course_type="国省考", teacher_id=supervisor_ids[2],
               start_date=date(2026, 3, 1), end_date=date(2026, 3, 30),
               description="行测五大模块专项刷题", status="active"),
        Course(name="申论写作冲刺班", course_type="国省考", teacher_id=supervisor_ids[0],
               start_date=date(2026, 3, 15), end_date=date(2026, 4, 15),
               description="申论大作文和小题型突破", status="active"),
    ]
    session.add_all(courses)
    await session.flush()
    print(f"  创建 {len(courses)} 个课程")


async def seed_homework(session, supervisor_ids):
    """创建作业数据"""
    stmt = select(Homework).limit(1)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        print("  作业数据已存在，跳过")
        return

    # 获取课程 ID
    stmt = select(Course.id).order_by(Course.id)
    result = await session.execute(stmt)
    course_ids = [r[0] for r in result.all()]

    # 获取学员 ID
    stmt = select(Student.id).where(Student.status == "active").order_by(Student.id).limit(5)
    result = await session.execute(stmt)
    student_ids = [r[0] for r in result.all()]

    homework_list = [
        Homework(course_id=course_ids[0], title="言语理解专项练习（一）", description="完成30道言语理解题",
                 due_date=utc_now() + timedelta(days=3), status="published", created_by=supervisor_ids[0]),
        Homework(course_id=course_ids[0], title="数量关系基础训练", description="完成20道数量关系基础题",
                 due_date=utc_now() + timedelta(days=5), status="published", created_by=supervisor_ids[0]),
        Homework(course_id=course_ids[1], title="综合知识测试卷（一）", description="模拟卷一套，限时90分钟",
                 due_date=utc_now() + timedelta(days=7), status="published", created_by=supervisor_ids[1]),
        Homework(course_id=course_ids[2], title="判断推理50题", description="逻辑判断+图形推理+定义判断",
                 due_date=utc_now() - timedelta(days=2), status="closed", created_by=supervisor_ids[2]),
    ]
    session.add_all(homework_list)
    await session.flush()

    # 获取最后一个作业 ID
    hw_id = homework_list[-1].id

    submissions = []
    for idx, (score, feedback) in enumerate([(85, "做得不错，图形推理还需加强"),
                                              (72, "逻辑判断正确率偏低"),
                                              (91, "优秀！继续保持")]):
        if idx < len(student_ids):
            submissions.append(HomeworkSubmission(
                homework_id=hw_id, student_id=student_ids[idx],
                content="已完成", score=score, feedback=feedback,
                reviewed_by=supervisor_ids[0]))

    if submissions:
        session.add_all(submissions)
        await session.flush()
    print(f"  创建 {len(homework_list)} 个作业, {len(submissions)} 条提交")


async def seed_checkins(session):
    """创建打卡数据"""
    stmt = select(Checkin).limit(1)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        print("  打卡数据已存在，跳过")
        return

    # 获取活跃学员 ID
    stmt = select(Student.id).where(Student.status == "active").order_by(Student.id)
    result = await session.execute(stmt)
    student_ids = [r[0] for r in result.all()]

    today = date.today()
    checkins = []
    study_contents = [
        "行测：言语理解30题，正确率80%",
        "申论：写了一篇大作文，主题是乡村振兴",
        "常识判断专项复习，整理错题本",
        "数量关系20题 + 资料分析10题",
        "判断推理：逻辑判断15题，图形推理10题",
        "申论小题型练习：概括归纳 + 综合分析",
    ]

    for i, sid in enumerate(student_ids):
        for days_ago in range(0, 20, 1 + i % 3):
            checkin_date = today - timedelta(days=days_ago)
            checkins.append(Checkin(
                student_id=sid,
                checkin_date=checkin_date,
                content=study_contents[days_ago % len(study_contents)],
            ))

    session.add_all(checkins)
    await session.flush()
    print(f"  创建 {len(checkins)} 条打卡记录")


async def seed_positions(session):
    """创建岗位数据"""
    stmt = select(Position).limit(1)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        print("  岗位数据已存在，跳过")
        return

    positions = [
        Position(title="南京市鼓楼区综合管理岗", department="鼓楼区人民政府办公室",
                 location="南京", education="本科及以上", major="不限",
                 political_status="中共党员", work_experience="不限",
                 recruitment_count=2, exam_type="国省考", year=2026, status="active"),
        Position(title="苏州市工业园区经济管理岗", department="苏州工业园区管委会",
                 location="苏州", education="硕士及以上", major="经济学、金融学",
                 political_status="不限", work_experience="2年以上",
                 recruitment_count=1, exam_type="国省考", year=2026, status="active"),
        Position(title="徐州市教育局文秘岗", department="徐州市教育局",
                 location="徐州", education="本科及以上", major="中文、新闻",
                 political_status="不限", work_experience="不限",
                 recruitment_count=3, exam_type="事业编", year=2026, status="active"),
        Position(title="合肥市包河区社区管理岗", department="包河区民政局",
                 location="合肥", education="大专及以上", major="社会工作、公共管理",
                 political_status="不限", work_experience="不限",
                 recruitment_count=5, exam_type="事业编", year=2026, status="active"),
        Position(title="宿州市乡镇综合岗", department="宿州市泗县乡镇政府",
                 location="宿州", education="大专及以上", major="不限",
                 political_status="不限", work_experience="不限",
                 recruitment_count=8, exam_type="三支一扶", year=2026, status="active"),
        Position(title="南京市玄武区法律顾问岗", department="玄武区司法局",
                 location="南京", education="本科及以上", major="法学",
                 political_status="不限", work_experience="不限",
                 recruitment_count=2, exam_type="国省考", year=2026, status="active"),
        Position(title="无锡市财政局会计岗", department="无锡市财政局",
                 location="无锡", education="本科及以上", major="会计学、财务管理",
                 political_status="不限", work_experience="不限",
                 recruitment_count=2, exam_type="事业编", year=2026, status="active"),
        Position(title="常州市信息技术岗", department="常州市大数据管理局",
                 location="常州", education="本科及以上", major="计算机、软件工程",
                 political_status="不限", work_experience="不限",
                 recruitment_count=3, exam_type="事业编", year=2026, status="active"),
    ]
    session.add_all(positions)
    await session.flush()
    print(f"  创建 {len(positions)} 个岗位")


async def seed_crawler_config(session):
    """创建采集器默认配置"""
    stmt = select(CrawlerConfig).limit(1)
    result = await session.execute(stmt)
    if result.scalar_one_or_none():
        print("  采集配置已存在，跳过")
        return

    config = CrawlerConfig(
        name="公考雷达-浙江",
        target_url="https://gongkaoleida.com/area/878",
        interval_minutes=10,
        is_active=True,
        session_valid=False,
        total_crawled=0,
    )
    session.add(config)
    await session.flush()
    print("  创建 1 条采集配置")


async def main():
    print("=" * 50)
    print("  公考管理系统 V2 - 种子数据初始化")
    print("=" * 50)

    async with AsyncSessionLocal() as session:
        try:
            print("\n[1/8] 初始化用户...")
            supervisor_ids = await seed_users(session)

            print("[2/8] 初始化学员...")
            await seed_students(session, supervisor_ids)

            print("[3/8] 初始化督学日志...")
            await seed_supervision_logs(session, supervisor_ids)

            print("[4/8] 初始化课程...")
            await seed_courses(session, supervisor_ids)

            print("[5/8] 初始化作业...")
            await seed_homework(session, supervisor_ids)

            print("[6/8] 初始化打卡...")
            await seed_checkins(session)

            print("[7/8] 初始化岗位...")
            await seed_positions(session)

            print("[8/8] 初始化采集配置...")
            await seed_crawler_config(session)

            await session.commit()
            print("\n" + "=" * 50)
            print("  种子数据初始化完成！")
            print("=" * 50)
            print("\n默认账号：")
            print("  管理员：admin / admin123")
            print("  督学1：supervisor1 / 123456（张老师）")
            print("  督学2：supervisor2 / 123456（李老师）")
            print("  督学3：supervisor3 / 123456（王老师）")

        except Exception as e:
            await session.rollback()
            print(f"\n错误: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())

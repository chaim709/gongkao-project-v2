"""学员管理服务单元测试"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.student_service import StudentService
from app.schemas.student import StudentCreate, StudentUpdate
from app.models.user import User


@pytest.mark.unit
class TestStudentService:
    """学员服务测试"""

    @pytest.mark.asyncio
    async def test_create_student(self, db_session: AsyncSession, test_user: User):
        """测试创建学员"""
        service = StudentService()
        data = StudentCreate(
            name="张三",
            phone="13800138000",
            supervisor_id=test_user.id
        )

        student = await service.create_student(db_session, data, test_user.id)

        assert student.name == "张三"
        assert student.phone == "13800138000"

    @pytest.mark.asyncio
    async def test_get_student(self, db_session: AsyncSession, test_user: User):
        """测试获取学员"""
        service = StudentService()
        data = StudentCreate(name="张三", phone="13800138000", supervisor_id=test_user.id)
        created = await service.create_student(db_session, data, test_user.id)

        student = await service.get_student(db_session, created.id)
        assert student.name == "张三"

    @pytest.mark.asyncio
    async def test_list_students(self, db_session: AsyncSession, test_user: User):
        """测试学员列表"""
        service = StudentService()

        result = await service.list_students(db_session, page=1, page_size=20)
        assert result.total >= 0
        assert isinstance(result.items, list)

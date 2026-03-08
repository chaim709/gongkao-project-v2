from sqlalchemy import Column, Integer, String, Float, Date, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class FinanceRecord(Base):
    """财务收支记录"""
    __tablename__ = "finance_records"

    id = Column(Integer, primary_key=True, index=True)
    record_type = Column(String(10), nullable=False, index=True)  # income / expense
    category = Column(String(50), nullable=False)  # 分类：学费、场地租金、教师工资 等
    amount = Column(Float, nullable=False)
    record_date = Column(Date, nullable=False, index=True)
    description = Column(Text)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"))  # 关联学员（收入类）
    payment_method = Column(String(30))  # 微信/支付宝/银行转账/现金
    receipt_no = Column(String(100))  # 收据/发票号

    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)

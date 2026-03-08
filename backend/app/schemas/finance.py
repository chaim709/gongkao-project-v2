from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class FinanceCreate(BaseModel):
    record_type: str  # income / expense
    category: str
    amount: float
    record_date: date
    description: Optional[str] = None
    student_id: Optional[int] = None
    payment_method: Optional[str] = None
    receipt_no: Optional[str] = None


class FinanceUpdate(BaseModel):
    category: Optional[str] = None
    amount: Optional[float] = None
    record_date: Optional[date] = None
    description: Optional[str] = None
    student_id: Optional[int] = None
    payment_method: Optional[str] = None
    receipt_no: Optional[str] = None


class FinanceResponse(BaseModel):
    id: int
    record_type: str
    category: str
    amount: float
    record_date: date
    description: Optional[str] = None
    student_id: Optional[int] = None
    payment_method: Optional[str] = None
    receipt_no: Optional[str] = None
    created_by: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FinanceListResponse(BaseModel):
    items: list[FinanceResponse]
    total: int
    page: int
    page_size: int

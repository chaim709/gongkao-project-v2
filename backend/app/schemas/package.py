from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# ========== 套餐 ==========

class PackageCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: Decimal = Field(..., gt=0)
    original_price: Optional[Decimal] = None
    validity_days: int = Field(default=365, gt=0)
    is_active: bool = True


class PackageUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    original_price: Optional[Decimal] = None
    validity_days: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class PackageResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    price: Decimal
    original_price: Optional[Decimal] = None
    validity_days: int
    is_active: bool
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PackageListResponse(BaseModel):
    items: List[PackageResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ========== 套餐项目 ==========

class PackageItemCreate(BaseModel):
    package_id: int
    item_type: str = Field(..., min_length=1, max_length=50)
    item_id: int
    quantity: int = Field(default=1, gt=0)


class PackageItemResponse(BaseModel):
    id: int
    package_id: int
    item_type: str
    item_id: int
    quantity: int
    created_at: datetime

    model_config = {"from_attributes": True}

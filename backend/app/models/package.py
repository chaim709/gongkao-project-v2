from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base


class Package(Base):
    """套餐"""
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    original_price = Column(Numeric(10, 2))
    validity_days = Column(Integer, default=365)
    is_active = Column(Boolean, default=True)
    created_by = Column(Integer, ForeignKey("users.id"))

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True))
    deleted_by = Column(Integer)


class PackageItem(Base):
    """套餐项目"""
    __tablename__ = "package_items"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String(50), nullable=False)
    item_id = Column(Integer, nullable=False)
    quantity = Column(Integer, default=1)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

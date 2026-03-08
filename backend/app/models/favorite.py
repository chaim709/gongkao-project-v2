from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime, timezone
from app.database import Base


class PositionFavorite(Base):
    __tablename__ = "position_favorites"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    position_id = Column(Integer, ForeignKey("positions.id"), nullable=False, index=True)
    category = Column(String(20), default="saved")  # saved/sprint/stable/safe
    note = Column(String(200))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    deleted_at = Column(DateTime(timezone=True))

    __table_args__ = (
        UniqueConstraint("student_id", "position_id", name="uq_student_position"),
    )

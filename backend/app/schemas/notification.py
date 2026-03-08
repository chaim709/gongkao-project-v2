from pydantic import BaseModel
from typing import Optional


class NotificationCreate(BaseModel):
    title: str
    content: Optional[str] = None
    type: str = "system"
    link: Optional[str] = None
    user_id: Optional[int] = None  # None=发给所有人

from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime
import re


def validate_password_strength(password: str) -> str:
    """密码强度校验：至少8字符，包含字母和数字"""
    if len(password) < 8:
        raise ValueError("密码长度不能少于8个字符")
    if not re.search(r'[a-zA-Z]', password):
        raise ValueError("密码必须包含至少一个字母")
    if not re.search(r'\d', password):
        raise ValueError("密码必须包含至少一个数字")
    return password


class UserLogin(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    real_name: Optional[str] = None
    role: Literal["admin", "supervisor", "teacher"] = "supervisor"
    phone: Optional[str] = None
    email: Optional[str] = None

    @field_validator("password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserUpdate(BaseModel):
    real_name: Optional[str] = None
    role: Optional[Literal["admin", "supervisor", "teacher"]] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None


class UserResetPassword(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UserResponse(BaseModel):
    id: int
    username: str
    real_name: Optional[str] = None
    role: str
    phone: Optional[str] = None
    email: Optional[str] = None
    is_active: bool
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    page: int
    page_size: int


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def check_password(cls, v: str) -> str:
        return validate_password_strength(v)


class UpdateProfileRequest(BaseModel):
    real_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

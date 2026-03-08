# Pydantic Schemas示例

## backend/app/schemas/auth.py
```python
from pydantic import BaseModel
from typing import Optional

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

class UserResponse(BaseModel):
    id: int
    username: str
    real_name: Optional[str]
    role: str
    
    class Config:
        from_attributes = True
```

## backend/app/schemas/student.py
```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    wechat: Optional[str] = Field(None, max_length=50)
    education: Optional[str] = None
    major: Optional[str] = None
    exam_type: Optional[str] = None
    supervisor_id: Optional[int] = None

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    need_attention: Optional[bool] = None
    status: Optional[str] = None

class StudentResponse(StudentBase):
    id: int
    status: str
    created_at: date
    
    class Config:
        from_attributes = True

class StudentList(BaseModel):
    total: int
    page: int
    limit: int
    data: list[StudentResponse]
```

---

# 数据库模型示例

## backend/app/models/user.py
```python
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(50))
    role = Column(String(20), nullable=False)
    phone = Column(String(20))
    email = Column(String(100))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

## backend/app/models/student.py
```python
from sqlalchemy import Column, Integer, String, Boolean, Date, Text, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    phone = Column(String(20), index=True)
    wechat = Column(String(50))
    education = Column(String(20))
    major = Column(String(100))
    exam_type = Column(String(100))
    supervisor_id = Column(Integer, ForeignKey("users.id"))
    need_attention = Column(Boolean, default=False)
    last_contact_date = Column(Date)
    status = Column(String(20), default="active")
    
    # 关系
    supervisor = relationship("User", backref="students")
```

---

# 数据库配置

## backend/app/core/database.py
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://gongkao_user:password@localhost:5432/gongkao_db"
)

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=20,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

# 主应用文件

## backend/main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, students
from app.core.database import engine, Base

# 创建数据库表
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="公考培训机构管理系统",
    version="2.0.0"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/v1")
app.include_router(students.router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "公考培训机构管理系统 API v2.0"}
```

---

**文件位置**: `/Users/openclaw01/gongkao-project-v2/CODE_EXAMPLES.md`

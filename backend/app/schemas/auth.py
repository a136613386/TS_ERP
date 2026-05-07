"""
Pydantic Schemas - 认证模块
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    """Token 响应"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserBase(BaseModel):
    """用户基础信息"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """用户创建"""
    password: str


class UserUpdate(BaseModel):
    """用户更新"""
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = None


class UserResponse(UserBase):
    """用户响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TokenPayload(BaseModel):
    """Token 载荷"""
    sub: int
    exp: Optional[datetime] = None

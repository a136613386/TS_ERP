"""
Pydantic Schemas - 客户模块
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class CustomerBase(BaseModel):
    """客户基础信息"""
    name: str = Field(..., min_length=1, max_length=100)
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    level: str = "normal"
    address: Optional[str] = None
    department_id: Optional[int] = None


class CustomerCreate(CustomerBase):
    """创建客户"""
    pass


class CustomerUpdate(BaseModel):
    """更新客户"""
    name: Optional[str] = None
    contact: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    level: Optional[str] = None
    address: Optional[str] = None
    department_id: Optional[int] = None


class Customer(CustomerBase):
    """客户响应"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CustomerList(BaseModel):
    """客户列表响应"""
    items: List[Customer]
    total: int
    page: int
    page_size: int

"""
Pydantic Schemas - 订单模块
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class OrderItemBase(BaseModel):
    """订单明细基础"""
    product_id: int
    quantity: int
    unit_price: float


class OrderBase(BaseModel):
    """订单基础信息"""
    customer_id: int
    amount: float
    status: str = "pending"
    payment_method: Optional[str] = None
    remark: Optional[str] = None


class OrderCreate(OrderBase):
    """创建订单"""
    pass


class OrderUpdate(BaseModel):
    """更新订单"""
    status: Optional[str] = None
    payment_method: Optional[str] = None
    remark: Optional[str] = None


class Order(OrderBase):
    """订单响应"""
    id: int
    order_no: str
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderList(BaseModel):
    """订单列表响应"""
    items: List[Order]
    total: int
    page: int
    page_size: int

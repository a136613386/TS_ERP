"""
Pydantic Schemas - 财务模块
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field


class FinanceRecordBase(BaseModel):
    """财务记录基础"""
    customer_id: Optional[int] = None
    type: str  # receipt/payment
    amount: float
    record_date: date
    order_id: Optional[int] = None
    payment_method: Optional[str] = None
    remark: Optional[str] = None


class FinanceRecordCreate(FinanceRecordBase):
    """创建财务记录"""
    pass


class FinanceRecordUpdate(BaseModel):
    """更新财务记录"""
    type: Optional[str] = None
    amount: Optional[float] = None
    record_date: Optional[date] = None
    payment_method: Optional[str] = None
    remark: Optional[str] = None


class FinanceRecord(FinanceRecordBase):
    """财务记录响应"""
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FinanceRecordList(BaseModel):
    """财务记录列表响应"""
    items: List[FinanceRecord]
    total: int
    page: int
    page_size: int

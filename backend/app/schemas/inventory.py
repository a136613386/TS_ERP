"""
Pydantic Schemas - 库存模块
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class InventoryBase(BaseModel):
    """库存基础信息"""
    product_id: int
    warehouse_id: int
    quantity: int = 0
    min_stock_level: int = 10


class InventoryCreate(InventoryBase):
    """创建库存"""
    pass


class InventoryUpdate(BaseModel):
    """更新库存"""
    quantity: Optional[int] = None
    min_stock_level: Optional[int] = None


class Inventory(InventoryBase):
    """库存响应"""
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class InventoryAlert(InventoryBase):
    """库存预警"""
    product_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class InventoryList(BaseModel):
    """库存列表响应"""
    items: List[Inventory]
    total: int
    page: int
    page_size: int

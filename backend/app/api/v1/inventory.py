"""
库存管理 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.inventory import Inventory, InventoryCreate, InventoryUpdate, InventoryList, InventoryAlert

router = APIRouter()


@router.get("/", response_model=InventoryList)
def list_inventory(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    warehouse_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取库存列表"""
    from app.models.inventory import Inventory as InventoryModel
    
    query = db.query(InventoryModel)
    
    if keyword:
        query = query.filter(InventoryModel.product_name.like(f"%{keyword}%"))
    
    if warehouse_id:
        query = query.filter(InventoryModel.warehouse_id == warehouse_id)
    
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/alerts", response_model=List[InventoryAlert])
def get_inventory_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取库存预警列表"""
    from app.models.inventory import Inventory as InventoryModel
    
    # 查询库存不足的商品
    items = db.query(InventoryModel).filter(
        InventoryModel.quantity <= InventoryModel.min_stock_level
    ).all()
    
    return items


@router.get("/{inventory_id}", response_model=Inventory)
def get_inventory(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取库存详情"""
    from app.models.inventory import Inventory as InventoryModel
    
    item = db.query(InventoryModel).filter(InventoryModel.id == inventory_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    return item


@router.post("/", response_model=Inventory)
def create_inventory(
    data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建库存记录"""
    from app.models.inventory import Inventory as InventoryModel
    
    item = InventoryModel(**data.dict())
    db.add(item)
    db.commit()
    db.refresh(item)
    
    return item


@router.put("/{inventory_id}", response_model=Inventory)
def update_inventory(
    inventory_id: int,
    data: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新库存"""
    from app.models.inventory import Inventory as InventoryModel
    
    item = db.query(InventoryModel).filter(InventoryModel.id == inventory_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(item, key, value)
    
    db.commit()
    db.refresh(item)
    
    return item

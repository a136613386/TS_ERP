"""
订单管理 API
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.order import Order, OrderCreate, OrderUpdate, OrderList

router = APIRouter()


@router.get("/", response_model=OrderList)
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单列表"""
    from app.models.order import Order as OrderModel
    
    query = db.query(OrderModel)
    
    if customer_id:
        query = query.filter(OrderModel.customer_id == customer_id)
    
    if status:
        query = query.filter(OrderModel.status == status)
    
    if start_date:
        query = query.filter(OrderModel.created_at >= start_date)
    
    if end_date:
        query = query.filter(OrderModel.created_at <= end_date)
    
    total = query.count()
    orders = query.order_by(OrderModel.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": orders,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{order_id}", response_model=Order)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取订单详情"""
    from app.models.order import Order as OrderModel
    
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return order


@router.post("/", response_model=Order)
def create_order(
    order_data: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建订单"""
    from app.models.order import Order as OrderModel
    from app.core.database import SessionLocal
    
    order = OrderModel(**order_data.dict())
    db.add(order)
    db.commit()
    db.refresh(order)
    
    return order


@router.put("/{order_id}", response_model=Order)
def update_order(
    order_id: int,
    order_data: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新订单"""
    from app.models.order import Order as OrderModel
    
    order = db.query(OrderModel).filter(OrderModel.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    for key, value in order_data.dict(exclude_unset=True).items():
        setattr(order, key, value)
    
    db.commit()
    db.refresh(order)
    
    return order

"""
财务管理 API
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.finance import FinanceRecord, FinanceRecordCreate, FinanceRecordUpdate, FinanceRecordList

router = APIRouter()


@router.get("/", response_model=FinanceRecordList)
def list_finance_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    customer_id: Optional[int] = None,
    type: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取财务记录列表"""
    from app.models.finance import FinanceRecord as FinanceRecordModel
    
    query = db.query(FinanceRecordModel)
    
    if customer_id:
        query = query.filter(FinanceRecordModel.customer_id == customer_id)
    
    if type:
        query = query.filter(FinanceRecordModel.type == type)
    
    if start_date:
        query = query.filter(FinanceRecordModel.record_date >= start_date)
    
    if end_date:
        query = query.filter(FinanceRecordModel.record_date <= end_date)
    
    total = query.count()
    items = query.order_by(FinanceRecordModel.record_date.desc()).offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{record_id}", response_model=FinanceRecord)
def get_finance_record(
    record_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取财务记录详情"""
    from app.models.finance import FinanceRecord as FinanceRecordModel
    
    record = db.query(FinanceRecordModel).filter(FinanceRecordModel.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Finance record not found")
    
    return record


@router.post("/", response_model=FinanceRecord)
def create_finance_record(
    data: FinanceRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建财务记录"""
    from app.models.finance import FinanceRecord as FinanceRecordModel
    
    record = FinanceRecordModel(**data.dict())
    db.add(record)
    db.commit()
    db.refresh(record)
    
    return record


@router.put("/{record_id}", response_model=FinanceRecord)
def update_finance_record(
    record_id: int,
    data: FinanceRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新财务记录"""
    from app.models.finance import FinanceRecord as FinanceRecordModel
    
    record = db.query(FinanceRecordModel).filter(FinanceRecordModel.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Finance record not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(record, key, value)
    
    db.commit()
    db.refresh(record)
    
    return record

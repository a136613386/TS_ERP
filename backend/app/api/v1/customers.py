"""
客户管理 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.customer import Customer, CustomerCreate, CustomerUpdate, CustomerList

router = APIRouter()


@router.get("/", response_model=CustomerList)
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取客户列表"""
    from app.models.customer import Customer as CustomerModel
    
    query = db.query(CustomerModel)
    
    if keyword:
        query = query.filter(
            CustomerModel.name.like(f"%{keyword}%") |
            CustomerModel.contact.like(f"%{keyword}%") |
            CustomerModel.phone.like(f"%{keyword}%")
        )
    
    total = query.count()
    customers = query.offset((page - 1) * page_size).limit(page_size).all()
    
    return {
        "items": customers,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/{customer_id}", response_model=Customer)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取客户详情"""
    from app.models.customer import Customer as CustomerModel
    
    customer = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    return customer


@router.post("/", response_model=Customer)
def create_customer(
    customer_data: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建客户"""
    from app.models.customer import Customer as CustomerModel
    
    customer = CustomerModel(**customer_data.dict())
    db.add(customer)
    db.commit()
    db.refresh(customer)
    
    return customer


@router.put("/{customer_id}", response_model=Customer)
def update_customer(
    customer_id: int,
    customer_data: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新客户"""
    from app.models.customer import Customer as CustomerModel
    
    customer = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    for key, value in customer_data.dict(exclude_unset=True).items():
        setattr(customer, key, value)
    
    db.commit()
    db.refresh(customer)
    
    return customer


@router.delete("/{customer_id}")
def delete_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除客户"""
    from app.models.customer import Customer as CustomerModel
    
    customer = db.query(CustomerModel).filter(CustomerModel.id == customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    db.delete(customer)
    db.commit()
    
    return {"message": "Customer deleted successfully"}

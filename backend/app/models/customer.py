"""
客户模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Customer(Base):
    """客户模型"""
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    contact = Column(String(50))
    phone = Column(String(20))
    email = Column(String(100))
    level = Column(String(20), default="normal")  # normal/vip/svip
    address = Column(Text)
    department_id = Column(Integer, ForeignKey('departments.id'))
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    orders = relationship("Order", back_populates="customer")
    department = relationship("Department", back_populates="customers")

"""
财务模型
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship

from app.core.database import Base


class FinanceRecord(Base):
    """财务记录模型"""
    __tablename__ = "finance_records"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), index=True)
    type = Column(String(20), nullable=False)  # receipt/payment
    amount = Column(DECIMAL(12, 2), nullable=False)
    record_date = Column(Date, nullable=False, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'))
    payment_method = Column(String(20))
    remark = Column(Text)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    customer = relationship("Customer")
    order = relationship("Order")
    creator = relationship("User")

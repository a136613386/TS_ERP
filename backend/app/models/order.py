"""
订单模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, DECIMAL
from sqlalchemy.orm import relationship

from app.core.database import Base


class Order(Base):
    """订单模型"""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_no = Column(String(50), unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    amount = Column(DECIMAL(12, 2), nullable=False)
    status = Column(String(20), default="pending")  # pending/paid/shipped/completed/cancelled
    payment_method = Column(String(20))
    remark = Column(Text)
    created_by = Column(Integer, ForeignKey('users.id'))
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")
    creator = relationship("User")


class OrderItem(Base):
    """订单明细模型"""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id'), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    subtotal = Column(DECIMAL(12, 2), nullable=False)
    
    # 关系
    order = relationship("Order", back_populates="items")
    product = relationship("Product")

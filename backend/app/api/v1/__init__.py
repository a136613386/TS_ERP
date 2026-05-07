"""
API V1 路由汇总
"""
from fastapi import APIRouter

from app.api.v1 import auth, customers, orders, inventory, finance, chat, knowledge

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(customers.router, prefix="/customers", tags=["客户管理"])
api_router.include_router(orders.router, prefix="/orders", tags=["订单管理"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["库存管理"])
api_router.include_router(finance.router, prefix="/finance", tags=["财务管理"])
api_router.include_router(chat.router, prefix="/chat", tags=["智能客服"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识库"])

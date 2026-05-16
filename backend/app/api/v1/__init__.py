"""
API V1 路由汇总
"""
from fastapi import APIRouter

from app.api.v1 import auth, chat, knowledge
from app.api.v1 import java_proxy

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(chat.router, prefix="/chat", tags=["智能客服"])
api_router.include_router(knowledge.router, prefix="/knowledge", tags=["知识库"])

# Java 后端代理路由 (转发业务请求至 Spring Boot)
api_router.include_router(java_proxy.router, prefix="/java", tags=["Java后端代理"])

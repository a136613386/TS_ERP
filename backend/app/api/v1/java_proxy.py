"""
Java 后端 API 代理
将业务 API 请求转发至 Spring Boot Java 后端
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request
import httpx

from app.core.config import settings

router = APIRouter()


async def proxy_request(request: Request, path: str) -> any:
    """转发请求到 Java 后端"""
    # Python backend 作为网关时，不直接实现 ERP 业务 CRUD；
    # 业务接口统一转发到 Spring Boot，保持前后端分离和业务边界清晰。
    java_url = f"{settings.JAVA_BACKEND_URL.rstrip('/')}/{path.lstrip('/')}"

    # 获取请求体
    body = await request.body()

    # 构建转发 headers（去除 host 防止冲突）
    # 原样转发请求头和请求体，但去掉 host，避免目标 Java 服务误判来源主机。
    headers = dict(request.headers)
    headers.pop("host", None)

    async with httpx.AsyncClient(timeout=settings.JAVA_BACKEND_TIMEOUT) as client:
        response = await client.request(
            method=request.method,
            url=java_url,
            headers=headers,
            params=dict(request.query_params),
            content=body,
        )

    return response.json()


@router.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def java_proxy(request: Request, path: str):
    """通用代理：将 /api/v1/java/{path} 转发至 Java 后端 /api/{path}"""
    # 例如前端请求 /api/v1/java/knowledge/documents，
    # 这里会转发到 Java 后端 /api/knowledge/documents。
    return await proxy_request(request, f"api/{path}")

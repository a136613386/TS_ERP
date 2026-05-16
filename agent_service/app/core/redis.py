"""
Redis 客户端
"""
from typing import Optional

import redis

from app.core.config import settings


_redis_client: Optional[redis.Redis] = None


def get_redis_client() -> redis.Redis:
    """获取 Redis 客户端"""
    global _redis_client

    if _redis_client is None:
        _redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD or None,
            decode_responses=True,
            socket_connect_timeout=0.3,
            socket_timeout=0.3,
        )

    return _redis_client


def close_redis() -> None:
    """关闭 Redis 连接"""
    global _redis_client
    if _redis_client:
        _redis_client.close()
        _redis_client = None

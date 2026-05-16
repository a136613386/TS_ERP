"""
Agent 会话记忆模块。

Redis 用于保存多轮对话上下文，但不能影响单轮 ERP 问答。
当本地 Redis 不可用时，智能助手会跳过会话记忆读写，并继续返回当前问题的答案。
"""
from datetime import datetime
from typing import Any, Dict, Optional
import json

from redis.exceptions import RedisError

from app.core.redis import get_redis_client


class SessionMemory:
    """Redis 可用时，保存最近的对话上下文。"""

    SESSION_PREFIX = "agent:session:"
    CONTEXT_TTL = 3600

    def __init__(self):
        self.redis = get_redis_client()

    async def save_context(
        self,
        session_id: str,
        query: str,
        intent: str,
        result: Dict[str, Any],
    ) -> None:
        """保存一轮对话；Redis 不可用时自动降级。"""
        key = f"{self.SESSION_PREFIX}{session_id}"
        context = {
            "query": query,
            "intent": intent,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        }

        try:
            existing = self.redis.get(key)
            history = json.loads(existing) if existing else []
            history.append(context)
            history = history[-10:]
            self.redis.setex(key, self.CONTEXT_TTL, json.dumps(history, ensure_ascii=False))
        except RedisError as exc:
            print(f"会话记忆保存已跳过，Redis 不可用：{exc}")

    async def get_context(self, session_id: str) -> list:
        """返回历史对话；Redis 不可用时返回空列表。"""
        key = f"{self.SESSION_PREFIX}{session_id}"
        try:
            existing = self.redis.get(key)
            if existing:
                return json.loads(existing)
        except RedisError as exc:
            print(f"会话记忆读取已跳过，Redis 不可用：{exc}")
        return []

    async def clear_context(self, session_id: str) -> None:
        """Redis 可用时，清理指定会话的历史上下文。"""
        key = f"{self.SESSION_PREFIX}{session_id}"
        try:
            self.redis.delete(key)
        except RedisError as exc:
            print(f"会话记忆清理已跳过，Redis 不可用：{exc}")

    async def get_last_query(self, session_id: str) -> Optional[str]:
        """返回上一轮用户问题。"""
        context = await self.get_context(session_id)
        if context:
            return context[-1].get("query")
        return None

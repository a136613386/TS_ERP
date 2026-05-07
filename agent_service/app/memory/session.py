"""
会话上下文管理
"""
from typing import Dict, Any, Optional
import json
from datetime import datetime

from app.core.redis import get_redis_client


class SessionMemory:
    """会话记忆"""
    
    SESSION_PREFIX = "agent:session:"
    CONTEXT_TTL = 3600  # 1小时
    
    def __init__(self):
        self.redis = get_redis_client()
    
    async def save_context(
        self,
        session_id: str,
        query: str,
        intent: str,
        result: Dict[str, Any]
    ) -> None:
        """保存会话上下文"""
        key = f"{self.SESSION_PREFIX}{session_id}"
        
        context = {
            "query": query,
            "intent": intent,
            "result": result,
            "timestamp": datetime.now().isoformat()
        }
        
        # 获取现有上下文
        existing = self.redis.get(key)
        history = json.loads(existing) if existing else []
        
        history.append(context)
        
        # 保留最近10轮对话
        history = history[-10:]
        
        self.redis.setex(key, self.CONTEXT_TTL, json.dumps(history))
    
    async def get_context(self, session_id: str) -> list:
        """获取会话上下文"""
        key = f"{self.SESSION_PREFIX}{session_id}"
        
        existing = self.redis.get(key)
        if existing:
            return json.loads(existing)
        
        return []
    
    async def clear_context(self, session_id: str) -> None:
        """清除会话上下文"""
        key = f"{self.SESSION_PREFIX}{session_id}"
        self.redis.delete(key)
    
    async def get_last_query(self, session_id: str) -> Optional[str]:
        """获取上一轮查询"""
        context = await self.get_context(session_id)
        if context:
            return context[-1].get("query")
        return None

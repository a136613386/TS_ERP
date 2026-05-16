"""
Session memory for the Agent service.

Redis is useful for multi-turn context, but it must not block one-shot ERP
answers. When Redis is not available locally, the assistant skips memory
storage and still returns the current answer.
"""
from datetime import datetime
from typing import Any, Dict, Optional
import json

from redis.exceptions import RedisError

from app.core.redis import get_redis_client


class SessionMemory:
    """Persist recent conversation context in Redis when available."""

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
        """Save one conversation turn, degrading gracefully without Redis."""
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
            print(f"Session memory skipped, Redis unavailable: {exc}")

    async def get_context(self, session_id: str) -> list:
        """Return previous turns, or an empty list when Redis is unavailable."""
        key = f"{self.SESSION_PREFIX}{session_id}"
        try:
            existing = self.redis.get(key)
            if existing:
                return json.loads(existing)
        except RedisError as exc:
            print(f"Session memory read skipped, Redis unavailable: {exc}")
        return []

    async def clear_context(self, session_id: str) -> None:
        """Clear one session history when Redis is available."""
        key = f"{self.SESSION_PREFIX}{session_id}"
        try:
            self.redis.delete(key)
        except RedisError as exc:
            print(f"Session memory clear skipped, Redis unavailable: {exc}")

    async def get_last_query(self, session_id: str) -> Optional[str]:
        """Return the previous user query."""
        context = await self.get_context(session_id)
        if context:
            return context[-1].get("query")
        return None

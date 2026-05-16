"""
智能客服聊天 API
"""
from typing import List, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.core.redis import get_redis_client

router = APIRouter()


class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # user, assistant
    content: str
    timestamp: Optional[str] = None


class ChatQueryRequest(BaseModel):
    """聊天查询请求"""
    message: str
    session_id: Optional[str] = None


class ChatQueryResponse(BaseModel):
    """聊天查询响应"""
    answer: str
    sql: Optional[str] = None
    citations: Optional[List[dict]] = None
    data: Optional[dict] = None
    intent: str
    session_id: str


@router.post("/query", response_model=ChatQueryResponse)
async def chat_query(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    自然语言查询入口
    统一处理：固定查询、动态查询、RAG问答、混合查询
    """
    # Python backend 在三项目架构里是 API 网关角色：
    # 它负责鉴权和会话，真正的自然语言理解交给 agent_service 的 /agent/query。
    from app.core.config import settings
    import httpx
    import json
    
    # 获取或创建会话 ID
    session_id = request.session_id or f"session_{current_user.id}_{int(__import__('time').time())}"
    
    # 准备请求 Agent Service
    # 这些字段是 Agent 做权限、数据范围和上下文记忆的最小输入。
    agent_payload = {
        "query": request.message,
        "user_id": current_user.id,
        "username": current_user.username,
        "department_id": current_user.department_id,
        "session_id": session_id
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{settings.AGENT_SERVICE_URL}/agent/query",
                json=agent_payload
            )
            response.raise_for_status()
            result = response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent service error: {str(e)}")
    
    # 记录聊天历史
    # 聊天历史只保存展示所需的 user/assistant 消息；
    # Agent 内部还会保存一份更偏执行上下文的 session memory。
    redis_client = get_redis_client()
    chat_history_key = f"chat:history:{session_id}"
    
    user_message = {"role": "user", "content": request.message}
    assistant_message = {"role": "assistant", "content": result.get("answer", "")}
    
    redis_client.lpush(chat_history_key, json.dumps(user_message))
    redis_client.lpush(chat_history_key, json.dumps(assistant_message))
    redis_client.expire(chat_history_key, 86400)  # 24小时过期
    
    return {
        "answer": result.get("answer", ""),
        "sql": result.get("sql"),
        "citations": result.get("citations"),
        "data": result.get("data"),
        "intent": result.get("intent", "unknown"),
        "session_id": session_id
    }


@router.post("/reset")
async def reset_chat_session(
    session_id: str,
    current_user: User = Depends(get_current_user)
):
    """重置会话"""
    redis_client = get_redis_client()
    chat_history_key = f"chat:history:{session_id}"
    redis_client.delete(chat_history_key)
    
    return {"message": "Session reset successfully"}


@router.get("/history", response_model=List[ChatMessage])
async def get_chat_history(
    session_id: str,
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user)
):
    """获取聊天历史"""
    import json
    
    redis_client = get_redis_client()
    chat_history_key = f"chat:history:{session_id}"
    
    messages = redis_client.lrange(chat_history_key, 0, limit - 1)
    
    result = []
    for msg in messages:
        try:
            result.append(json.loads(msg))
        except:
            continue
    
    return list(reversed(result))

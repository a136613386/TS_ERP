"""
Agent 协调器
负责协调各 Agent 模块完成查询处理
"""
from typing import Dict, Any, Optional
import json

from app.agents.intent import IntentRecognizer
from app.agents.params import ParameterExtractor
from app.agents.router import QueryRouter
from app.agents.sql_agent import SQLAgent
from app.agents.rag_agent import RAGAgent
from app.agents.mixed_agent import MixedAgent
from app.agents.formatters.response import ResponseFormatter
from app.memory.session import SessionMemory
from app.permissions.context import PermissionContext


class AgentCoordinator:
    """Agent 协调器"""
    
    def __init__(self):
        self.intent_recognizer = IntentRecognizer()
        self.param_extractor = ParameterExtractor()
        self.query_router = QueryRouter()
        self.sql_agent = SQLAgent()
        self.rag_agent = RAGAgent()
        self.mixed_agent = MixedAgent()
        self.response_formatter = ResponseFormatter()
        self.session_memory = SessionMemory()
        self.permission_context = PermissionContext()
    
    async def process(
        self,
        query: str,
        user_id: int,
        username: str,
        department_id: Optional[int],
        session_id: str
    ) -> Dict[str, Any]:
        """
        处理用户查询的核心流程
        """
        # 1. 意图识别
        intent_result = await self.intent_recognizer.recognize(query)
        intent = intent_result["intent"]
        
        # 2. 获取用户权限上下文
        permission = await self.permission_context.get_user_permission(
            user_id=user_id,
            department_id=department_id
        )
        
        # 3. 参数提取
        params = await self.param_extractor.extract(
            query=query,
            intent=intent,
            session_id=session_id
        )
        
        # 4. 查询路由
        route = await self.query_router.route(
            intent=intent,
            params=params,
            permission=permission
        )
        
        # 5. 根据路由执行不同处理
        result = {}
        
        if route == "fixed_query":
            # 固定模板查询
            result = await self.sql_agent.execute_fixed_query(
                template_id=params.get("template_id"),
                params=params,
                permission=permission
            )
        
        elif route == "dynamic_query":
            # 动态 SQL 查询
            result = await self.sql_agent.execute_dynamic_query(
                query=query,
                params=params,
                permission=permission
            )
        
        elif route == "rag_query":
            # RAG 知识问答
            result = await self.rag_agent.answer(
                query=query,
                params=params,
                permission=permission
            )
        
        elif route == "mixed_query":
            # 混合查询
            result = await self.mixed_agent.answer(
                query=query,
                params=params,
                permission=permission
            )
        
        elif route == "permission_denied":
            # 权限不足
            result = {
                "answer": "抱歉，您没有权限访问相关信息。",
                "intent": intent,
                "sql": None,
                "citations": None,
                "data": None
            }
        
        elif route == "need_clarification":
            # 需要澄清
            result = {
                "answer": params.get("clarification_message", "请提供更多信息"),
                "intent": intent,
                "sql": None,
                "citations": None,
                "data": None
            }
        
        else:
            result = {
                "answer": "抱歉，我无法理解您的问题，请尝试重新描述。",
                "intent": intent,
                "sql": None,
                "citations": None,
                "data": None
            }
        
        # 6. 格式化响应
        formatted = await self.response_formatter.format(result)
        
        # 7. 保存上下文
        await self.session_memory.save_context(
            session_id=session_id,
            query=query,
            intent=intent,
            result=formatted
        )
        
        return formatted

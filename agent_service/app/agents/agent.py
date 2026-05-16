"""
Agent 协调器
负责协调各 Agent 模块完成查询处理
"""
from typing import Dict, Any, Optional
import logging

from app.agents.intent import IntentRecognizer
from app.agents.params import ParameterExtractor
from app.agents.router import QueryRouter
from app.agents.sql_agent import SQLAgent
from app.agents.rag_agent import RAGAgent
from app.agents.mixed_agent import MixedAgent
from app.formatters.response import ResponseFormatter
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
        logger = logging.getLogger(__name__)
        # /agent/query 的主流程只做编排，不把 SQL、RAG、权限等逻辑混在入口层。
        # 这样 Java 后端无论问业务数据、知识库，还是混合问题，都只需要调用一个接口。

        """
        处理用户查询的核心流程
        """
        # 0. 读取会话上下文，用于低信息追问和上下文改写。
        history = await self.session_memory.get_context(session_id)
        follow_up_result = self._resolve_follow_up(query, history)
        if follow_up_result:
            formatted = await self.response_formatter.format(follow_up_result)
            await self.session_memory.save_context(
                session_id=session_id,
                query=query,
                intent=formatted.get("intent", "follow_up"),
                result=formatted,
            )
            return formatted

        # 1. 意图识别
        intent_result = await self.intent_recognizer.recognize(query)
        intent = intent_result["intent"]
        rewritten_query = intent_result.get("rewrite_query") or query
        print('1. 意图识别-->',rewritten_query)
        if intent_result.get("confidence", 1.0) < 0.5:
            result = {
                "answer": "我还不能确定你想查业务数据还是问制度流程。可以补充一下对象或范围吗？例如：查询最近客户，或 库存不足怎么办。",
                "intent": "clarification",
                "sql": None,
                "citations": [],
                "data": None,
                "meta": {"intent_result": intent_result},
            }
            formatted = await self.response_formatter.format(result)
            await self.session_memory.save_context(session_id, query, "clarification", formatted)
            return formatted
        
        # 2. 获取用户权限上下文
        permission = await self.permission_context.get_user_permission(
            user_id=user_id,
            department_id=department_id
        )

        logger.info("已获取智能助手权限上下文，user_id=%s，department_id=%s", user_id, department_id)

        # 3. 参数提取
        params = await self.param_extractor.extract(
            query=rewritten_query,
            intent=intent,
            session_id=session_id
        )
        params["original_query"] = query
        params["intent_result"] = intent_result
        params["user_id"] = user_id
        params["department_id"] = department_id
        logger.info("智能助手参数提取完成，intent=%s，改写问题=%s，params=%s", intent, rewritten_query, params)

        if intent == "fixed_query" and not params.get("template_id"):
            intent = "dynamic_query"
            params["intent"] = intent
            logger.info("固定模板未命中，已降级到安全动态查询")

        # 4. 查询路由
        route = await self.query_router.route(
            intent=intent,
            params=params,
            permission=permission
        )
        logger.info("智能助手查询路由=%s", route)
        # 5. 根据路由执行不同处理
        # 路由值决定真正执行哪类智能体：
        # 固定查询和动态查询走业务数据，知识库查询走 RAG，混合查询同时查业务数据和知识库。
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
                query=rewritten_query,
                params=params,
                permission=permission
            )
        
        elif route == "rag_query":
            # RAG 知识问答
            result = await self.rag_agent.answer(
                query=rewritten_query,
                params=params,
                permission=permission
            )
        
        elif route == "mixed_query":
            # 混合查询
            result = await self.mixed_agent.answer(
                query=rewritten_query,
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
        logger.info("智能助手响应完成，intent=%s，回答预览=%s", formatted.get("intent"), formatted.get("answer", "")[:80])

        # 7. 保存上下文
        await self.session_memory.save_context(
            session_id=session_id,
            query=query,
            intent=intent,
            result=formatted
        )
        
        return formatted

    def _resolve_follow_up(self, query: str, history: list) -> Optional[Dict[str, Any]]:
        """根据上一轮上下文处理短追问。"""
        clean_query = "".join((query or "").split()).strip("？?。!！")
        if clean_query not in {"具体是哪一个", "具体是哪几个", "是哪一个", "是哪几个", "明细", "详情", "展开"}:
            return None
        if not history:
            return {
                "answer": "可以的，不过我需要知道你想追问哪一次查询。请把对象说完整一点。",
                "intent": "clarification",
                "sql": None,
                "citations": [],
                "data": None,
            }

        previous = history[-1].get("result") or {}
        data = previous.get("data")
        if isinstance(data, dict) and data.get("rows"):
            return {
                "answer": "这是上一轮查询的具体明细。",
                "intent": "follow_up",
                "sql": previous.get("sql"),
                "citations": previous.get("citations") or [],
                "data": data,
            }

        citations = previous.get("citations") or []
        if citations:
            return {
                "answer": "这是上一轮知识库回答引用到的来源。",
                "intent": "follow_up",
                "sql": None,
                "citations": citations,
                "data": {"chunks": citations},
            }
        return None

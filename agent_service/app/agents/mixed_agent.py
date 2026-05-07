"""
混合 Agent
同时处理 SQL 查询和 RAG 问答
"""
from typing import Dict, Any

from app.agents.sql_agent import SQLAgent
from app.agents.rag_agent import RAGAgent


class MixedAgent:
    """混合查询 Agent"""
    
    def __init__(self):
        self.sql_agent = SQLAgent()
        self.rag_agent = RAGAgent()
    
    async def answer(
        self,
        query: str,
        params: Dict[str, Any],
        permission: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        混合问答
        1. 查询实时业务数据
        2. 查询知识库
        3. LLM 合并回答
        """
        # 1. 执行动态 SQL 查询
        sql_result = await self.sql_agent.execute_dynamic_query(
            query=query,
            params=params,
            permission=permission
        )
        
        # 2. 执行 RAG 查询
        rag_result = await self.rag_agent.answer(
            query=query,
            params=params,
            permission=permission
        )
        
        # 3. 合并结果
        sql_data = sql_result.get("data")
        rag_data = rag_result.get("citations")
        
        # 4. 生成合并回答
        if sql_data and rag_data:
            answer = self._merge_answers(sql_data, rag_data, query)
        elif sql_data:
            answer = sql_result.get("answer", "")
        elif rag_data:
            answer = rag_result.get("answer", "")
        else:
            answer = "抱歉，无法回答您的问题。"
        
        return {
            "answer": answer,
            "sql": sql_result.get("sql"),
            "citations": rag_result.get("citations"),
            "data": sql_data,
            "intent": "mixed_query"
        }
    
    def _merge_answers(
        self,
        sql_data: Dict,
        rag_data: List,
        query: str
    ) -> str:
        """合并 SQL 和 RAG 结果生成回答"""
        # 简单实现：拼接两个回答
        sql_answer = f"业务数据查询结果：{sql_data.get('count', 0)} 条记录。"
        rag_answer = f"制度流程参考：{rag_data[0].get('content', '')[:200]}..."
        
        return f"{sql_answer}\n\n{rag_answer}"

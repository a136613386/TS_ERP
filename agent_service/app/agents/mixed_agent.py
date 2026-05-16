"""
混合 Agent
同时处理 SQL 查询和 RAG 问答
"""
from typing import Dict, Any, List

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
        # 1. 执行 SQL 查询
        # mixed_query 用于“实时数据 + 制度解释”类问题。
        # 例如先查哪些商品库存不足，再从知识库查公司制度要求如何处理。
        template_id = params.get("template_id")
        if template_id:
            sql_result = await self.sql_agent.execute_fixed_query(
                template_id=template_id,
                params=params,
                permission=permission,
            )
        else:
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
            answer = self._merge_answers(sql_result, rag_result, query)
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
            "data": {
                "rows": (sql_data or {}).get("rows", []),
                "columns": (sql_data or {}).get("columns", []),
                "count": (sql_data or {}).get("count", 0),
                "knowledge_chunks": (rag_result.get("data") or {}).get("chunks", []),
            },
            "intent": "mixed_query"
        }
    
    def _merge_answers(
        self,
        sql_result: Dict,
        rag_result: Dict,
        query: str
    ) -> str:
        """合并 SQL 和 RAG 结果生成回答"""
        sql_data = sql_result.get("data") or {}
        rows = sql_data.get("rows") or []
        citations = rag_result.get("citations") or []
        lines = [
            f"业务数据：共找到 {len(rows)} 条相关记录。",
        ]
        if rows:
            first = rows[0]
            if first.get("product_name"):
                lines.append(f"优先关注：{first.get('product_name')}，仓库：{first.get('warehouse_name', '-')}，可用库存：{first.get('available_qty', '-')}")
            elif first.get("customer_name"):
                lines.append(f"优先关注：{first.get('customer_name')}，状态：{first.get('status', '-')}")

        if citations:
            lines.append("制度参考：")
            for index, citation in enumerate(citations[:3], start=1):
                title = citation.get("document_title") or "未知文档"
                content = citation.get("content") or ""
                lines.append(f"{index}. {title}：{content}")
        else:
            lines.append("知识库暂未检索到可引用的制度来源。")

        return "\n".join(lines)

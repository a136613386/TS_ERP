"""
RAG Agent for knowledge-base question answering.
"""
from typing import Any, Dict, List

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.rag.retriever import RAGRetriever


class RAGAgent:
    """Answer questions with retrieved knowledge chunks."""

    ANSWER_PROMPT = """
你是一个 ERP 知识库助手，请严格根据检索到的知识片段回答用户问题。

用户问题: {query}

检索到的知识片段:
{context}

回答要求:
1. 只能基于知识片段回答，不要编造。
2. 如果知识片段不足以回答，请明确说明。
3. 给出来源标题。
"""

    def __init__(self):
        self.retriever = RAGRetriever()
        self.llm = None

    def _get_llm(self) -> ChatOpenAI:
        if self.llm is None:
            self.llm = ChatOpenAI(
                model=settings.LLM_MODEL,
                temperature=settings.LLM_TEMPERATURE,
                api_key=settings.LLM_API_KEY or None,
                base_url=settings.LLM_BASE_URL,
            )
        return self.llm

    async def answer(
        self,
        query: str,
        params: Dict[str, Any],
        permission: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Retrieve knowledge chunks and generate or format an answer."""
        user_id = params.get("user_id") or permission.get("user_id")
        department_id = params.get("department_id") or permission.get("department_id")
        search_results = await self.retriever.search(
            query=query,
            user_id=user_id,
            department_id=department_id,
            base_id=params.get("base_id"),
            top_k=5,
        )

        if not search_results:
            return {
                "answer": "抱歉，知识库中没有找到相关信息。",
                "sql": None,
                "citations": [],
                "data": None,
                "intent": "rag_query",
            }

        citations = self._build_citations(search_results)
        if not settings.LLM_API_KEY:
            return {
                "answer": self._format_retrieved_answer(search_results),
                "sql": None,
                "citations": citations,
                "data": {"chunks": search_results},
                "intent": "rag_query",
            }

        prompt = PromptTemplate.from_template(self.ANSWER_PROMPT)
        chain = prompt | self._get_llm()
        try:
            response = await chain.ainvoke({
                "query": query,
                "context": self._build_context(search_results),
            })
            return {
                "answer": response.content,
                "sql": None,
                "citations": citations,
                "data": {"chunks": search_results},
                "intent": "rag_query",
            }
        except Exception as exc:
            return {
                "answer": f"回答生成失败: {exc}",
                "sql": None,
                "citations": citations,
                "data": {"chunks": search_results},
                "intent": "rag_query",
            }

    def _build_context(self, results: List[Dict[str, Any]]) -> str:
        context_parts = []
        for index, result in enumerate(results, start=1):
            title = result.get("title") or "未知文档"
            content = result.get("content") or ""
            context_parts.append(f"[{index}] {title}\n{content}")
        return "\n\n".join(context_parts)

    def _format_retrieved_answer(self, results: List[Dict[str, Any]]) -> str:
        lines = [f"已从知识库找到 {len(results)} 条相关内容："]
        for index, result in enumerate(results[:5], start=1):
            title = result.get("title") or "未知文档"
            content = self._compact(result.get("content") or "", 180)
            lines.append(f"{index}. {title}：{content}")
        lines.append("当前未配置 LLM_API_KEY，以上为检索片段摘要。")
        return "\n".join(lines)

    def _build_citations(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return [
            {
                "chunk_id": result.get("chunk_id"),
                "document_id": result.get("document_id"),
                "document_title": result.get("title"),
                "score": result.get("score"),
                "content": self._compact(result.get("content") or "", 120),
            }
            for result in results
        ]

    @staticmethod
    def _compact(text: str, limit: int) -> str:
        compacted = " ".join(text.split())
        if len(compacted) <= limit:
            return compacted
        return compacted[:limit] + "..."

"""
RAG Agent
负责知识库问答
"""
from typing import Dict, Any, List
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app.rag.retriever import RAGRetriever


class RAGAgent:
    """RAG Agent"""
    
    # RAG 回答 Prompt
    ANSWER_PROMPT = """
你是一个 ERP 知识库助手，请根据检索到的知识片段回答用户的问题。

用户问题: {query}

检索到的知识片段:
{context}

回答要求:
1. 基于提供的知识片段回答，不要编造答案
2. 如果没有找到相关信息，请明确告知用户
3. 引用知识来源

输出格式:
答案: ...
来源: ...
"""
    
    def __init__(self):
        self.retriever = RAGRetriever()
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
    
    async def answer(
        self,
        query: str,
        params: Dict[str, Any],
        permission: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        RAG 知识问答
        """
        # 1. 检索相关知识
        search_results = await self.retriever.search(
            query=query,
            user_id=params.get("user_id"),
            department_id=params.get("department_id"),
            base_id=params.get("base_id"),
            top_k=5
        )
        
        if not search_results:
            return {
                "answer": "抱歉，知识库中没有找到相关信息。",
                "sql": None,
                "citations": [],
                "data": None,
                "intent": "rag_query"
            }
        
        # 2. 构建上下文
        context = self._build_context(search_results)
        
        # 3. 生成回答
        prompt = PromptTemplate.from_template(self.ANSWER_PROMPT)
        chain = prompt | self.llm
        
        try:
            response = await chain.ainvoke({
                "query": query,
                "context": context
            })
            
            answer = response.content
            
            # 提取来源
            citations = [
                {
                    "chunk_id": r.get("chunk_id"),
                    "document_title": r.get("document_title"),
                    "content": r.get("content", "")[:100] + "..."
                }
                for r in search_results
            ]
            
            return {
                "answer": answer,
                "sql": None,
                "citations": citations,
                "data": None,
                "intent": "rag_query"
            }
        except Exception as e:
            return {
                "answer": f"回答生成失败: {str(e)}",
                "sql": None,
                "citations": [],
                "data": None,
                "intent": "rag_query"
            }
    
    def _build_context(self, results: List[Dict]) -> str:
        """构建检索上下文"""
        context_parts = []
        
        for i, result in enumerate(results, 1):
            content = result.get("content", "")
            title = result.get("document_title", "未知文档")
            context_parts.append(f"[{i}] {title}:\n{content}")
        
        return "\n\n".join(context_parts)

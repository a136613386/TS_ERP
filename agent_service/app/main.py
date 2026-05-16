"""
Agent Service 主入口
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.agents.agent import AgentCoordinator
from app.core.config import settings
from app.rag.schemas import IndexDocumentRequest

app = FastAPI(
    title="TS_ERP Agent Service",
    description="ERP 智能体服务",
    version="1.0.0"
)

# 初始化 Agent 协调器
# AgentCoordinator 是 /agent/query 的总编排器。
# FastAPI 启动时只初始化一次，后续请求复用内部的意图识别、参数提取、SQL/RAG 等组件。
agent = AgentCoordinator()


class QueryRequest(BaseModel):
    """查询请求"""
    query: str
    user_id: int
    username: str
    department_id: Optional[int] = None
    session_id: str


class RAGSearchRequest(BaseModel):
    """RAG 检索请求"""
    query: str
    user_id: int
    department_id: Optional[int] = None
    base_id: Optional[int] = None
    top_k: int = 5


@app.post("/agent/query")
# 智能体统一查询入口：Java 后端会把当前用户、部门和会话 ID 透传到这里。
# 这里不直接拼回答，而是进入 AgentCoordinator 完成意图识别、路由、SQL/RAG 执行和响应格式化。
async def process_query(request: QueryRequest) -> Dict[str, Any]:
    """
    处理用户查询
    统一入口：意图识别 -> 参数提取 -> 路由 -> SQL/RAG -> 响应格式化
    """
    result = await agent.process(
        query=request.query,
        user_id=request.user_id,
        username=request.username,
        department_id=request.department_id,
        session_id=request.session_id
    )
    return result


@app.post("/rag/search")
# 知识库检索入口：只召回 ES 中的知识片段，不负责生成最终自然语言答案。
async def rag_search(request: RAGSearchRequest) -> Dict[str, Any]:
    """
    RAG 知识检索
    """
    from app.rag.retriever import RAGRetriever
    
    retriever = RAGRetriever()
    results = await retriever.search(
        query=request.query,
        user_id=request.user_id,
        department_id=request.department_id,
        base_id=request.base_id,
        top_k=request.top_k
    )
    
    return {"results": results}


@app.post("/rag/index-document")
# 文档索引入口：Java 上传文档后把正文 content 发到这里，Agent 负责切块、向量化并写入 ES。
# 返回的 chunks 会被 Java 用来更新 MySQL 分块表、文档分块数和索引状态。
async def index_document(request: IndexDocumentRequest) -> Dict[str, Any]:
    """
    文档索引入口：Java 上传文档后调用。
    Agent 负责语义分块、向量化并写入 Elasticsearch。
    """
    from app.rag.indexer import RAGIndexer

    indexer = RAGIndexer()
    result = await indexer.index_document(request)
    return result.model_dump()


@app.get("/")
async def root():
    return {
        "message": "TS_ERP Agent Service",
        "version": "1.0.0",
        "health": "/health",
        "agentQuery": "/agent/query",
        "ragSearch": "/rag/search"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

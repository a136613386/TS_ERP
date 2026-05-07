"""
Agent Service 主入口
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from app.agents.agent import AgentCoordinator
from app.core.config import settings

app = FastAPI(
    title="TS_ERP Agent Service",
    description="ERP 智能体服务",
    version="1.0.0"
)

# 初始化 Agent 协调器
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


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

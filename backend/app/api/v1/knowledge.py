"""
知识库管理 API
"""
import base64
import hashlib
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import os
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

# 文档上传临时目录
# 这是 Python backend 早期的知识库上传临时目录。
# 当前前端实际走 Java 后端上传，Java 再调用 agent_service /rag/index-document 做索引。
# 保留这个接口主要用于兼容和调试，不作为主链路。
UPLOAD_DIR = "/tmp/knowledge_uploads"


class DocumentUploadRequest(BaseModel):
    """文档上传请求，使用 JSON 以避免依赖 python-multipart"""

    filename: str = Field(..., min_length=1)
    content_base64: str = Field(..., min_length=1)
    content_type: str = "application/octet-stream"


@router.get("/bases")
def list_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取知识库列表"""
    from app.models.knowledge import KnowledgeBase as KnowledgeBaseModel
    
    bases = db.query(KnowledgeBaseModel).filter(
        KnowledgeBaseModel.is_active == True
    ).all()
    
    return bases


@router.post("/bases")
def create_knowledge_base(
    name: str,
    description: Optional[str] = None,
    module: str = "general",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建知识库"""
    from app.models.knowledge import KnowledgeBase as KnowledgeBaseModel
    
    base = KnowledgeBaseModel(
        name=name,
        description=description,
        module=module,
        created_by=current_user.id
    )
    db.add(base)
    db.commit()
    db.refresh(base)
    
    return base


@router.post("/documents/{base_id}")
async def upload_document(
    base_id: int,
    payload: DocumentUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文档"""
    # 旧版 Python 网关上传入口：接收 base64 文件内容，保存文件和元数据。
    # 注意：这里目前只把文档状态置为 pending，没有真正写入 ES。
    # 新主链路请看 Java 后端：/api/knowledge/documents/upload -> Agent /rag/index-document。
    from app.models.knowledge import KnowledgeBase as KnowledgeBaseModel, Document as DocumentModel
    
    # 验证知识库存在
    base = db.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.id == base_id).first()
    if not base:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 保存文件
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{payload.filename}")
    
    try:
        content = base64.b64decode(payload.content_base64)
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Invalid base64 content") from exc

    with open(file_path, "wb") as f:
        f.write(content)
    
    # 计算文件哈希
    file_hash = hashlib.md5(content).hexdigest()
    
    # 创建文档记录
    doc = DocumentModel(
        base_id=base_id,
        title=payload.filename,
        file_path=file_path,
        file_type=payload.content_type,
        file_hash=file_hash,
        file_size=len(content),
        uploaded_by=current_user.id,
        status="pending"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # TODO: 触发异步索引任务
    # 如果未来恢复 Python backend 上传主链路，需要在这里补异步任务：
    # 读取文件正文 -> 调用 agent_service /rag/index-document -> 写 chunk/状态。
    # worker.enqueue("index_document", doc.id)
    
    return {
        "id": doc.id,
        "title": doc.title,
        "status": doc.status
    }


@router.post("/documents/{doc_id}/reindex")
def reindex_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """重新索引文档"""
    from app.models.knowledge import Document as DocumentModel
    
    doc = db.query(DocumentModel).filter(DocumentModel.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # TODO: 触发重新索引任务
    doc.status = "pending"
    db.commit()
    
    return {"message": "Reindex task triggered"}


@router.post("/search")
def search_knowledge(
    query: str,
    base_id: Optional[int] = None,
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """知识检索"""
    # 知识库搜索仍然可以经由 Python backend 转发到 Agent。
    # 它只做检索，不等同于上传索引；上传索引由 /rag/index-document 负责。
    from app.core.config import settings
    import httpx
    
    # 调用 Agent Service 进行知识检索
    payload = {
        "query": query,
        "user_id": current_user.id,
        "department_id": current_user.department_id,
        "base_id": base_id,
        "top_k": top_k
    }
    
    try:
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        response = loop.run_until_complete(
            httpx.AsyncClient().post(
                f"{settings.AGENT_SERVICE_URL}/rag/search",
                json=payload,
                timeout=30.0
            )
        )
        result = response.json()
    except Exception as e:
        return {"results": [], "error": str(e)}
    
    return result

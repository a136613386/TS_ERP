"""
知识库管理 API
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
import os
import uuid

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User

router = APIRouter()

# 文档上传临时目录
UPLOAD_DIR = "/tmp/knowledge_uploads"


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
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """上传文档"""
    from app.models.knowledge import KnowledgeBase as KnowledgeBaseModel, Document as DocumentModel
    import hashlib
    
    # 验证知识库存在
    base = db.query(KnowledgeBaseModel).filter(KnowledgeBaseModel.id == base_id).first()
    if not base:
        raise HTTPException(status_code=404, detail="Knowledge base not found")
    
    # 保存文件
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}_{file.filename}")
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    # 计算文件哈希
    file_hash = hashlib.md5(content).hexdigest()
    
    # 创建文档记录
    doc = DocumentModel(
        base_id=base_id,
        title=file.filename,
        file_path=file_path,
        file_type=file.content_type,
        file_hash=file_hash,
        file_size=len(content),
        uploaded_by=current_user.id,
        status="pending"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # TODO: 触发异步索引任务
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

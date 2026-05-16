from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IndexDocumentRequest(BaseModel):
    # Java 调 /rag/index-document 的请求模型。
    # document_id 对应 Java 的 doc_code，content 是 Java 从上传文件中提取出的正文。
    document_id: str
    base_id: str = "default"
    title: str
    module: str = "通用制度"
    permission_scope: str = "public"
    content: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class IndexedChunk(BaseModel):
    # 返回给 Java 的分块模型。Java 会用 chunks 数更新列表展示，
    # 也可以把 content 写入 MySQL chunk 表，方便排查和后续重建索引。
    chunk_id: str
    document_id: str
    chunk_index: int
    title: str
    content: str
    module: str
    permission_scope: str
    es_document_id: Optional[str] = None


class IndexDocumentResponse(BaseModel):
    # indexed=false 不一定是系统错误，也可能是空文件或暂不支持解析的文件。
    # Java 根据 indexed/chunk_count 决定显示“已索引”“待处理”或“索引失败”。
    indexed: bool
    document_id: str
    chunk_count: int
    chunks: List[IndexedChunk] = Field(default_factory=list)
    message: str = "ok"

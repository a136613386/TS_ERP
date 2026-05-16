import hashlib
import math
from typing import List

from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from app.core.config import settings
from app.rag.schemas import IndexDocumentRequest, IndexDocumentResponse, IndexedChunk
from app.rag.splitters import split_document_text


class RAGIndexer:
    INDEX_NAME = "knowledge_chunk_index"

    def __init__(self):
        # 本地开发的 ES 已关闭账号密码；如果以后连接带认证的 ES，
        # 只要在环境变量中补 ES_USER/ES_PASSWORD，这里会自动带 basic_auth。
        options = {}
        if settings.ES_USER and settings.ES_PASSWORD:
            options["basic_auth"] = (settings.ES_USER, settings.ES_PASSWORD)
        self.es = Elasticsearch([settings.ES_URL], **options)
        self._embeddings = None

    async def index_document(self, request: IndexDocumentRequest) -> IndexDocumentResponse:
        # Java 已经负责文件保存和基础元数据落库；Python Agent 只处理“可检索内容”。
        # 这里先把完整正文切成多个语义片段，再逐片段写入 ES。
        chunks = self._build_chunks(request)
        if not chunks:
            return IndexDocumentResponse(
                indexed=False,
                document_id=request.document_id,
                chunk_count=0,
                chunks=[],
                message="文档内容为空或暂不支持解析",
            )

        self._ensure_index()
        actions = []
        for chunk in chunks:
            # 每个 chunk 都会有一份向量和一份原文：
            # - content_vector 用于向量召回
            # - title/content 用于 BM25/IK 中文分词召回
            vector = await self._embed(chunk.content)
            source = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "base_id": request.base_id,
                "title": chunk.title,
                "content": chunk.content,
                "content_vector": vector,
                "module": chunk.module,
                "tags": request.metadata.get("tags", []),
                "permission_scope": chunk.permission_scope,
                "created_by": request.metadata.get("created_by", "java-backend"),
                "created_at": request.metadata.get("created_at"),
                "updated_at": request.metadata.get("updated_at"),
            }
            actions.append({
                "_index": self.INDEX_NAME,
                "_id": chunk.chunk_id,
                "_source": source,
            })
            chunk.es_document_id = chunk.chunk_id

        # bulk 是批量写入 ES 的关键动作；执行成功后，知识库检索才能查到这些片段。
        bulk(self.es, actions)
        return IndexDocumentResponse(
            indexed=True,
            document_id=request.document_id,
            chunk_count=len(chunks),
            chunks=chunks,
            message="indexed",
        )

    def _build_chunks(self, request: IndexDocumentRequest) -> List[IndexedChunk]:
        # chunk_id 使用 document_id + 序号，方便 Java/MySQL/ES 三边排查同一篇文档。
        parts = split_document_text(request.content)
        return [
            IndexedChunk(
                chunk_id=f"{request.document_id}_{index + 1}",
                document_id=request.document_id,
                chunk_index=index + 1,
                title=request.title,
                content=content,
                module=request.module,
                permission_scope=request.permission_scope,
            )
            for index, content in enumerate(parts)
        ]

    async def _embed(self, content: str) -> List[float]:
        # 默认 local_hash 是本地联调用的轻量向量，不需要下载模型。
        # 生产或效果验证时可把 RAG_EMBEDDING_PROVIDER 切到 bge。
        if settings.RAG_EMBEDDING_PROVIDER != "bge":
            return self._hash_embed(content)
        vector = await self._get_embeddings().aembed_query(content)
        return list(vector)

    def _hash_embed(self, content: str) -> List[float]:
        vector = [0.0] * settings.RAG_VECTOR_DIMS
        for token in self._tokens(content):
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            index = int.from_bytes(digest[:4], "big") % settings.RAG_VECTOR_DIMS
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[index] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def _tokens(self, content: str) -> List[str]:
        text = (content or "").strip().lower()
        if not text:
            return ["empty"]
        words = [word for word in text.replace("\n", " ").split(" ") if word]
        chars = [text[i:i + 2] for i in range(max(len(text) - 1, 0))]
        return words + chars[:500]

    def _get_embeddings(self):
        if self._embeddings is None:
            try:
                from langchain_huggingface import HuggingFaceEmbeddings
            except ImportError:
                from langchain_community.embeddings import HuggingFaceEmbeddings

            self._embeddings = HuggingFaceEmbeddings(
                model_name="BAAI/bge-small-zh-v1.5",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        return self._embeddings

    def _ensure_index(self) -> None:
        # 首次写入时自动创建索引；已有索引不会覆盖，避免误删线上数据。
        if self.es.indices.exists(index=self.INDEX_NAME):
            return
        self.es.indices.create(
            index=self.INDEX_NAME,
            settings={
                "analysis": {
                    "analyzer": {
                        "ts_erp_ik_index": {
                            "type": "custom",
                            "tokenizer": "ik_max_word"
                        },
                        "ts_erp_ik_search": {
                            "type": "custom",
                            "tokenizer": "ik_smart"
                        }
                    }
                }
            },
            mappings={
                "properties": {
                    "chunk_id": {"type": "keyword"},
                    "document_id": {"type": "keyword"},
                    "base_id": {"type": "keyword"},
                    # title/content 使用 IK：写入时 ik_max_word 尽量多切词，
                    # 查询时 ik_smart 减少噪音，兼顾中文召回和精度。
                    "title": {
                        "type": "text",
                        "analyzer": "ts_erp_ik_index",
                        "search_analyzer": "ts_erp_ik_search"
                    },
                    "content": {
                        "type": "text",
                        "analyzer": "ts_erp_ik_index",
                        "search_analyzer": "ts_erp_ik_search"
                    },
                    "content_vector": {"type": "dense_vector", "dims": settings.RAG_VECTOR_DIMS, "index": True, "similarity": "cosine"},
                    "module": {"type": "keyword"},
                    "tags": {"type": "keyword"},
                    "permission_scope": {"type": "keyword"},
                    "created_by": {"type": "keyword"},
                    "created_at": {"type": "date", "ignore_malformed": True},
                    "updated_at": {"type": "date", "ignore_malformed": True},
                }
            },
        )

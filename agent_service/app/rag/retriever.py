"""
RAG 检索模块
"""
from typing import Dict, Any, List, Optional
from elasticsearch import Elasticsearch

from app.core.config import settings


class RAGRetriever:
    """RAG 检索器"""
    
    INDEX_NAME = "knowledge_chunk_index"
    
    def __init__(self):
        self.es = Elasticsearch(
            [settings.ES_URL],
            basic_auth=(settings.ES_USER, settings.ES_PASSWORD)
        )
    
    async def search(
        self,
        query: str,
        user_id: int,
        department_id: Optional[int] = None,
        base_id: Optional[int] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        混合检索：BM25 + 向量检索
        """
        # 构建查询
        must_clauses = []
        filter_clauses = [
            # 权限过滤
            {"term": {"permission_scope": "public"}}
        ]
        
        if department_id:
            filter_clauses.append({"term": {"permission_scope": f"dept_{department_id}"}})
        
        if base_id:
            filter_clauses.append({"term": {"base_id": str(base_id)}})
        
        # 检索 query
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["title^2", "content"],
                                "type": "best_fields"
                            }
                        }
                    ],
                    "filter": filter_clauses
                }
            },
            "knn": {
                "field": "content_vector",
                "query_vector": await self._get_embedding(query),
                "k": top_k,
                "num_candidates": 20
            },
            "rank": {
                "rrf": {
                    "rank_window_size": 10,
                    "rank_constant": 1
                }
            },
            "_source": ["chunk_id", "document_id", "base_id", "title", "content", "module", "tags"],
            "size": top_k
        }
        
        try:
            response = self.es.search(
                index=self.INDEX_NAME,
                body=search_body
            )
            
            results = []
            for hit in response["hits"]["hits"]:
                source = hit["_source"]
                results.append({
                    "chunk_id": source.get("chunk_id"),
                    "document_id": source.get("document_id"),
                    "title": source.get("title"),
                    "content": source.get("content"),
                    "module": source.get("module"),
                    "score": hit.get("_score", 0)
                })
            
            return results
        except Exception as e:
            print(f"RAG search error: {e}")
            return []
    
    async def _get_embedding(self, text: str) -> List[float]:
        """获取文本向量"""
        # 使用 OpenAI embedding
        from langchain_openai import OpenAIEmbeddings
        
        embeddings = OpenAIEmbeddings()
        vector = await embeddings.aembed_query(text)
        return vector
    
    async def index_document(
        self,
        document_id: str,
        base_id: str,
        title: str,
        chunks: List[Dict[str, str]]
    ) -> bool:
        """
        索引文档 chunks
        """
        from langchain_openai import OpenAIEmbeddings
        
        embeddings = OpenAIEmbeddings()
        actions = []
        
        for i, chunk in enumerate(chunks):
            content = chunk.get("content", "")
            vector = await embeddings.aembed_query(content)
            
            action = {
                "_index": self.INDEX_NAME,
                "_id": f"{document_id}_{i}",
                "_source": {
                    "chunk_id": f"{document_id}_{i}",
                    "document_id": document_id,
                    "base_id": base_id,
                    "title": title,
                    "content": content,
                    "content_vector": vector,
                    "chunk_index": i,
                    "created_at": "now"
                }
            }
            actions.append(action)
        
        if actions:
            from elasticsearch.helpers import bulk
            success, failed = bulk(self.es, actions)
            return failed == 0
        
        return True

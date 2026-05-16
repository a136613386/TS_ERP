"""RAG 检索模块：BM25 + 向量召回 + Python 侧 RRF 融合。"""
import hashlib
import logging
import math
from typing import Any, Dict, List, Optional

from elasticsearch import Elasticsearch

from app.core.config import settings


logger = logging.getLogger(__name__)


class RAGRetriever:
    """从 Elasticsearch 中检索知识片段。"""

    INDEX_NAME = "knowledge_chunk_index"
    RRF_K = 60

    def __init__(self):
        options = {}
        if settings.ES_USER and settings.ES_PASSWORD:
            options["basic_auth"] = (settings.ES_USER, settings.ES_PASSWORD)
        self.es = Elasticsearch([settings.ES_URL], **options)

    async def search(
        self,
        query: str,
        user_id: Optional[int],
        department_id: Optional[int] = None,
        base_id: Optional[int] = None,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """使用 BM25 和向量召回检索公开或已授权的知识片段。"""
        search_query = self._rewrite_query(query)
        permission_values = self._permission_values(user_id, department_id)
        filter_clauses: List[Dict[str, Any]] = [
            {"terms": {"permission_scope": permission_values}}
        ]
        if base_id:
            filter_clauses.append({"term": {"base_id": str(base_id)}})

        bm25_results = self._bm25_search(query, search_query, filter_clauses, permission_values, base_id, top_k)
        vector_results = await self._vector_search(query, filter_clauses, top_k)
        merged = self._rrf_merge([bm25_results, vector_results], top_k)
        return merged

    def _bm25_search(
        self,
        query: str,
        search_query: str,
        filter_clauses: List[Dict[str, Any]],
        permission_values: List[str],
        base_id: Optional[int],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        search_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": search_query,
                                "fields": ["title^3", "content"],
                                "type": "best_fields",
                                "operator": "or",
                            }
                        }
                    ],
                    "filter": filter_clauses,
                }
            },
            "_source": [
                "chunk_id",
                "document_id",
                "base_id",
                "title",
                "content",
                "module",
                "tags",
                "permission_scope",
            ],
            "size": top_k,
        }

        try:
            response = self.es.search(index=self.INDEX_NAME, body=search_body)
            hits = response.get("hits", {}).get("hits", [])
            logger.info(
                "RAG BM25 检索完成",
                extra={
                    "query": query,
                    "rewritten_query": search_query,
                    "permissions": permission_values,
                    "base_id": base_id,
                    "hit_count": len(hits),
                }
            )
            return [self._hit_to_result(hit, "bm25") for hit in hits]
        except Exception as exc:
            logger.warning("RAG BM25 检索失败：%s", exc)
            return []

    async def _vector_search(
        self,
        query: str,
        filter_clauses: List[Dict[str, Any]],
        top_k: int,
    ) -> List[Dict[str, Any]]:
        vector = await self._embed(query)
        search_body = {
            "query": {
                "script_score": {
                    "query": {"bool": {"filter": filter_clauses}},
                    "script": {
                        "source": "cosineSimilarity(params.query_vector, 'content_vector') + 1.0",
                        "params": {"query_vector": vector},
                    },
                }
            },
            "_source": [
                "chunk_id",
                "document_id",
                "base_id",
                "title",
                "content",
                "module",
                "tags",
                "permission_scope",
            ],
            "size": top_k,
        }
        try:
            response = self.es.search(index=self.INDEX_NAME, body=search_body)
            hits = response.get("hits", {}).get("hits", [])
            logger.info("RAG 向量检索完成，query=%s，命中数=%s", query, len(hits))
            return [self._hit_to_result(hit, "vector") for hit in hits]
        except Exception as exc:
            logger.warning("RAG 向量检索已跳过：%s", exc)
            return []

    def _hit_to_result(self, hit: Dict[str, Any], source_type: str) -> Dict[str, Any]:
        source = hit.get("_source", {})
        return {
            "chunk_id": source.get("chunk_id"),
            "document_id": source.get("document_id"),
            "base_id": source.get("base_id"),
            "title": source.get("title"),
            "document_title": source.get("title"),
            "content": source.get("content"),
            "module": source.get("module"),
            "tags": source.get("tags", []),
            "permission_scope": source.get("permission_scope"),
            "score": hit.get("_score", 0),
            "retrieval_source": source_type,
        }

    def _rrf_merge(self, result_lists: List[List[Dict[str, Any]]], top_k: int) -> List[Dict[str, Any]]:
        merged: Dict[str, Dict[str, Any]] = {}
        scores: Dict[str, float] = {}
        sources: Dict[str, set[str]] = {}
        for results in result_lists:
            for rank, result in enumerate(results, start=1):
                chunk_id = str(result.get("chunk_id") or result.get("document_id") or id(result))
                scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (self.RRF_K + rank)
                merged.setdefault(chunk_id, result)
                sources.setdefault(chunk_id, set()).add(result.get("retrieval_source", "unknown"))

        ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:top_k]
        final_results = []
        for chunk_id, rrf_score in ranked:
            item = dict(merged[chunk_id])
            item["rrf_score"] = round(rrf_score, 6)
            item["retrieval_source"] = "+".join(sorted(sources.get(chunk_id, set())))
            final_results.append(item)
            logger.info(
                "RAG 融合命中，rrf_score=%s，来源=%s，chunk_id=%s，标题=%s，预览=%s",
                item["rrf_score"],
                item["retrieval_source"],
                item.get("chunk_id"),
                item.get("title"),
                (item.get("content") or "")[:100],
            )
        return final_results

    def _permission_values(self, user_id: Optional[int], department_id: Optional[int]) -> List[str]:
        """返回任一可访问的权限范围，而不是要求所有权限同时满足。"""
        values = ["public"]
        if department_id:
            values.append(f"dept_{department_id}")
        if user_id:
            values.append(f"user_{user_id}")
        return values

    def _rewrite_query(self, query: str) -> str:
        """为较短的中文问题补充轻量 ERP 同义词。"""
        terms = [query]
        normalized = (query or "").strip()
        if "ERP" in normalized.upper():
            terms.extend(["企业资源计划", "系统简介", "系统介绍", "ERP系统"])
        if any(word in normalized for word in ["库存不足", "缺货", "低库存"]):
            terms.extend(["安全库存", "补货", "补货申请", "采购"])
        if any(word in normalized for word in ["创建订单", "新建订单", "下单"]):
            terms.extend(["订单管理", "创建订单", "订单状态"])
        if any(word in normalized for word in ["采购入库", "入库", "验收"]):
            terms.extend(["采购订单", "到货验收", "入库确认"])
        return " ".join(dict.fromkeys(term for term in terms if term))

    async def _embed(self, content: str) -> List[float]:
        if settings.RAG_EMBEDDING_PROVIDER == "bge":
            vector = await self._get_embeddings().aembed_query(content)
            return list(vector)
        return self._hash_embed(content)

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
        if not hasattr(self, "_embeddings"):
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

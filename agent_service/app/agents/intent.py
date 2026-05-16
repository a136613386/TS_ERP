"""
ERP 智能助手意图识别模块。

高频、稳定的问题优先使用本地确定性规则，避免每次都依赖大模型。
例如“库存不足”既可能是查询当前低库存商品，也可能是询问处理流程，
所以这里需要先根据表达方式做明确区分。
"""
from typing import Any, Dict, List
import json
import logging
import re

from langchain_core.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from app.core.config import settings


logger = logging.getLogger(__name__)


class IntentRecognizer:
    """将用户问题路由到 SQL、RAG、混合查询或动态查询。"""

    INTENT_PROMPT = """
你是一个 ERP 智能助手，需要根据用户问题判断查询意图。

用户问题: {query}

意图类型:
1. fixed_query: 高频、稳定、可控的数据查询，例如库存不足商品列表、客户列表、财务记录。
2. dynamic_query: 统计分析、排行、复杂组合筛选。
3. rag_query: 制度、流程、操作说明、FAQ 等知识库问答。
4. mixed_query: 同时需要业务数据和制度知识。

请只输出 JSON:
{{
  "intent": "fixed_query",
  "domain": "inventory",
  "query_type": "list",
  "needs_business_data": true,
  "needs_knowledge": false,
  "confidence": 0.95,
  "missing_slots": [],
  "rewrite_query": "查询当前库存不足商品列表",
  "reasoning": "判断理由"
}}
"""

    def __init__(self):
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

    async def recognize(self, query: str) -> Dict[str, Any]:
        """识别用户意图；优先使用 ERP 本地规则。"""
        normalized_query = self._normalize_query(query)
        rule_result = self._recognize_by_rules(normalized_query)
        if rule_result:
            return rule_result

        if not settings.LLM_API_KEY:
            return self._fallback_recognize(normalized_query)

        prompt = PromptTemplate.from_template(self.INTENT_PROMPT)
        chain = prompt | self._get_llm()

        try:
            response = await chain.ainvoke({"query": query})
            json_match = re.search(r"\{[^{}]*\}", response.content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return self._normalize_result(result, normalized_query)
        except Exception as exc:
            logger.warning("意图识别调用失败：%s", exc)

        return self._fallback_recognize(normalized_query)

    def _fallback_recognize(self, query: str) -> Dict[str, Any]:
        """LLM 未配置或调用失败时，使用本地语义规则兜底。"""
        normalized = self._normalize_query(query)
        rule_result = self._recognize_by_rules(normalized)
        if rule_result:
            return rule_result

        if self._is_unclear_follow_up(normalized):
            return self._result(
                intent="clarification",
                domain="unknown",
                query_type="follow_up",
                confidence=0.45,
                rewrite_query=normalized,
                reasoning="缺少上一轮上下文或指代不清，需要追问。",
                missing_slots=["referent"],
            )

        if self._has_business_word(normalized) and self._has_knowledge_action_word(normalized):
            intent = "mixed_query"
            domain = self._infer_domain(normalized)
            query_type = "analysis"
        elif self._has_knowledge_action_word(normalized):
            intent = "rag_query"
            domain = self._infer_domain(normalized)
            query_type = "policy"
        elif any(keyword in normalized for keyword in ["最高", "最低", "最多", "最少", "排名", "统计", "汇总", "合计", "平均", "趋势"]):
            intent = "dynamic_query"
            domain = self._infer_domain(normalized)
            query_type = "analysis"
        else:
            intent = "fixed_query"
            domain = self._infer_domain(normalized)
            query_type = "list"

        return self._result(
            intent=intent,
            domain=domain,
            query_type=query_type,
            confidence=0.68,
            rewrite_query=normalized,
            reasoning="基于本地语义规则判断。",
        )

    def _recognize_by_rules(self, query: str) -> Dict[str, Any] | None:
        normalized = self._normalize_query(query)

        if self._has_inventory_shortage_word(normalized):
            asks_current_data = self._has_data_query_word(normalized)
            asks_process = self._has_knowledge_action_word(normalized)
            if asks_current_data and asks_process:
                return self._result("mixed_query", "inventory", "analysis", 0.95, "查询当前库存不足商品并解释处理流程", "同时询问库存不足数据和处理制度。")
            if asks_process:
                return self._result("rag_query", "inventory", "policy", 0.95, "查询库存不足处理办法和流程", "询问库存不足处理办法/流程，走知识库。")
            if asks_current_data:
                return self._result("fixed_query", "inventory", "list", 0.95, "查询当前库存不足商品列表", "询问当前库存不足商品列表，走固定 SQL。")

        if "客户" in normalized and any(word in normalized for word in ["哪些", "哪几", "列表", "所有", "全部", "最近", "最新", "查询", "查看"]):
            return self._result("fixed_query", "customer", "list", 0.92, normalized, "询问客户列表，走固定 SQL。")

        if "客户" in normalized and any(word in normalized for word in ["多少", "几个", "数量", "统计", "总数"]):
            return self._result("dynamic_query", "customer", "count", 0.92, normalized, "询问客户统计数量，走安全动态 SQL。")

        if any(word in normalized for word in ["应收", "应付", "欠款", "逾期"]):
            return self._result("dynamic_query", "finance", "list", 0.9, normalized, "询问财务应收应付数据，走安全动态 SQL。")

        if "订单" in normalized and any(word in normalized for word in ["查询", "查看", "列表", "最近", "最新", "哪些", "采购", "销售"]):
            return self._result("dynamic_query", "order", "list", 0.9, normalized, "询问订单业务数据，走安全动态 SQL。")

        if "供应商" in normalized and any(word in normalized for word in ["查询", "查看", "列表", "所有", "哪些"]):
            return self._result("dynamic_query", "purchase", "list", 0.9, normalized, "询问供应商业务数据，走安全动态 SQL。")

        if self._is_unclear_follow_up(normalized):
            return self._result("clarification", "unknown", "follow_up", 0.45, normalized, "短句追问需要结合多轮上下文。", ["referent"])

        return None

    def _normalize_result(self, result: Dict[str, Any], fallback_query: str) -> Dict[str, Any]:
        intent = result.get("intent") or "fixed_query"
        if intent not in {"fixed_query", "dynamic_query", "rag_query", "mixed_query", "clarification"}:
            intent = "fixed_query"
        return self._result(
            intent=intent,
            domain=result.get("domain") or self._infer_domain(fallback_query),
            query_type=result.get("query_type") or "list",
            confidence=float(result.get("confidence") or 0.0),
            rewrite_query=result.get("rewrite_query") or fallback_query,
            reasoning=result.get("reasoning") or "",
            missing_slots=result.get("missing_slots") or [],
        )

    @staticmethod
    def _result(
        intent: str,
        domain: str,
        query_type: str,
        confidence: float,
        rewrite_query: str,
        reasoning: str,
        missing_slots: List[str] | None = None,
    ) -> Dict[str, Any]:
        return {
            "intent": intent,
            "domain": domain,
            "query_type": query_type,
            "needs_business_data": intent in {"fixed_query", "dynamic_query", "mixed_query"},
            "needs_knowledge": intent in {"rag_query", "mixed_query"},
            "confidence": confidence,
            "missing_slots": missing_slots or [],
            "rewrite_query": rewrite_query,
            "reasoning": reasoning,
        }

    @staticmethod
    def _has_inventory_shortage_word(query: str) -> bool:
        keywords = ["库存不足", "库存预警", "缺货", "低库存", "不足库存"]
        return any(keyword in query for keyword in keywords)

    @staticmethod
    def _has_data_query_word(query: str) -> bool:
        keywords = ["哪些", "哪几", "查询", "查看", "列表", "多少", "几个", "商品", "产品", "当前", "现在"]
        return any(keyword in query for keyword in keywords)

    @staticmethod
    def _has_business_word(query: str) -> bool:
        keywords = ["客户", "订单", "库存", "商品", "产品", "应收", "应付", "采购", "销售", "供应商", "金额", "数量", "数据"]
        return any(keyword in query for keyword in keywords)

    @staticmethod
    def _has_knowledge_action_word(query: str) -> bool:
        keywords = [
            "怎么办",
            "怎么版",
            "咋办",
            "怎么处理",
            "如何处理",
            "应该怎么办",
            "应该怎么",
            "处理办法",
            "处理流程",
            "流程",
            "制度",
            "规范",
            "规则",
            "说明",
            "是什么",
            "如何",
            "怎么",
        ]
        return any(keyword in query for keyword in keywords)

    @staticmethod
    def _is_unclear_follow_up(query: str) -> bool:
        clean = re.sub(r"[\s?？。!！,，；;]", "", query or "")
        return clean in {"具体是哪一个", "具体是哪几个", "是哪一个", "是哪几个", "有哪些", "为什么", "怎么办", "怎么处理", "展开", "明细", "详情"}

    @staticmethod
    def _infer_domain(query: str) -> str:
        domain_keywords = [
            ("inventory", ["库存", "缺货", "低库存", "商品", "产品", "仓库"]),
            ("customer", ["客户", "客戶"]),
            ("order", ["订单", "訂單", "销售单", "采购单"]),
            ("finance", ["应收", "应付", "收款", "付款", "发票", "财务"]),
            ("purchase", ["采购", "供应商", "入库"]),
            ("sales", ["销售", "报价", "发货", "退货"]),
        ]
        for domain, words in domain_keywords:
            if any(word in query for word in words):
                return domain
        return "knowledge"

    @staticmethod
    def _normalize_query(query: str) -> str:
        normalized = (query or "").translate(str.maketrans({
            "詢": "询",
            "戶": "户",
            "庫": "库",
            "貨": "货",
            "處": "处",
            "理": "理",
            "麼": "么",
            "麼": "么",
            "應": "应",
            "該": "该",
            "規": "规",
            "範": "范",
            "則": "则",
        }))
        normalized = normalized.replace("怎么版", "怎么办")
        normalized = normalized.replace("怎麼辦", "怎么办")
        normalized = normalized.replace("咋处理", "怎么处理")
        return normalized
